import argparse
import subprocess
import sys
import tempfile
import shutil
import json
import logging
import os
import pprint
import shlex
import warnings
import io
from contextlib import contextmanager, redirect_stdout, redirect_stderr
from pathlib import Path
from collections import defaultdict
from datetime import datetime, UTC
import importlib.resources as pkg_resources

import yaml
import requests
import urllib3

from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
from ansible.template import Templar
from ansible.parsing.vault import VaultSecret, VaultSecretsContext

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("edd-installer")

SESSION = requests.Session()
SESSION.verify = False

class VaultString(str):
    """A string subclass to mark values coming from !vault tags."""
    pass


class Loader(yaml.SafeLoader):
    """
    Custom YAML Loader that preserves !vault blocks from Ansible YAML files.
    Instead of trying to decrypt them, it stores them as VaultString objects.
    """
    pass


class Dumper(yaml.SafeDumper):
    """
    Custom YAML Dumper that knows how to re-emit VaultString values
    using the !vault tag exactly as they appeared.
    """
    pass


def vault_constructor(loader, node):
    """
    Called when the YAML parser encounters a !vault tag.
    Simply store the raw scalar content as a VaultString.
    """
    value = loader.construct_scalar(node)
    return VaultString(value)


def vault_representer(dumper, data):
    """
    Called when dumping a VaultString.
    Emits the data as a literal block scalar with the !vault tag.
    """
    # Use style='|' to preserve multi-line formatting
    return dumper.represent_scalar('!vault', data, style='|')


# Register the constructors and representers
Loader.add_constructor('!vault', vault_constructor)
Dumper.add_representer(VaultString, vault_representer)

def ensure_rc_file():
    """Ensure that ~/.edd-tool.rc exists. Create from template if missing."""
    rc_file = Path.home() / ".edd-tool.rc"
    if rc_file.exists():
        return

    try:
        # Load the packaged template
        with pkg_resources.files("edd_tool.data").joinpath("edd-tool.rc.template").open("r") as template:
            rc_file.write_text(template.read())
        logger.info(f"Created default config file at {rc_file}")
    except Exception as e:
        logger.warning(f"Could not create default RC file: {e}")


def configure_file_logging(site_repo, version, inventory):
    """
    Configure logging to also write to a timestamped log file.

    Args:
        site_repo (str): Site repository URL or name
        version (str): Version/branch/tag
        inventory (str): Inventory name
    Returns:
        Path: Path to the created log file
    """
    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()  # e.g. 2025-09-19T14:02:00+00:00
    safe_repo = site_repo.split("/")[-1].replace(".git", "")
    log_dir = Path.home() / ".edd" / "deployment_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{timestamp}_{safe_repo}_{version}_{inventory}.log"

    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
    logging.getLogger().addHandler(fh)

    logger.info(f"Logging to file: {log_path}")
    return log_path


@contextmanager
def suppress_ansible_warnings():
    """
    Context manager to suppress warnings and stdout/stderr noise.
    Useful for silencing Ansible's noisy inventory parsing.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        buffer = io.StringIO()
        with redirect_stdout(buffer), redirect_stderr(buffer):
            yield

@contextmanager
def working_directory(path):
    """Temporarily change the working directory inside the context."""
    original_dir = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(original_dir)

def get_repositories(registry):
    url = f"{registry}/v2/_catalog"
    resp = SESSION.get(url)
    resp.raise_for_status()
    return resp.json().get("repositories", [])

def get_tags(registry, repo):
    url = f"{registry}/v2/{repo}/tags/list"
    resp = SESSION.get(url)
    resp.raise_for_status()
    return resp.json().get("tags", [])

def get_manifest_digest(registry, repo, tag):
    url = f"{registry}/v2/{repo}/manifests/{tag}"
    headers = {"Accept": "application/vnd.docker.distribution.manifest.v2+json"}
    resp = SESSION.head(url, headers=headers)
    resp.raise_for_status()
    return resp.headers.get("Docker-Content-Digest")

def snapshot_registry(registry):
    """Return a dict mapping repo -> digest -> tags."""
    snapshot = {}
    for repo in get_repositories(registry):
        tags = get_tags(registry, repo)
        if not tags:
            continue
        digest_to_tags = defaultdict(list)
        for tag in tags:
            digest = get_manifest_digest(registry, repo, tag)
            if digest:
                digest_to_tags[digest].append(tag)
        snapshot[repo] = {digest: sorted(tags) for digest, tags in digest_to_tags.items()}
    return snapshot

def compare_snapshots(before, after):
    """Return a report of added and removed tags."""
    report = []
    all_repos = set(before.keys()) | set(after.keys())
    for repo in sorted(all_repos):
        before_d = before.get(repo, {})
        after_d = after.get(repo, {})
        all_digests = set(before_d.keys()) | set(after_d.keys())
        for digest in all_digests:
            before_tags = set(before_d.get(digest, []))
            after_tags = set(after_d.get(digest, []))
            added = after_tags - before_tags
            removed = before_tags - after_tags
            if added or removed:
                report.append((repo, digest, sorted(added), sorted(removed)))
    return report

def print_report(report):
    if not report:
        logger.info("No changes detected in the registry.")
        return
    for repo, digest, added, removed in report:
        short_digest = digest[:20]
        if added:
            logger.info(f"[+] {repo}:{short_digest} --> added tags: {', '.join(added)}")
        if removed:
            logger.info(f"[-] {repo}:{short_digest} --> removed tags: {', '.join(removed)}")

def run_cmd(cmd, cwd=None, check=True, env=None, log_func=None):
    """
    Run a subprocess command and stream its output into the logger.

    Args:
        cmd (list[str]): Command and arguments
        cwd (str|Path, optional): Directory to run command in
        check (bool): Exit on non-zero return code
        env (dict, optional): Environment variables

    Returns:
        int: Return code of the command
    """
    if not log_func:
        log_func = logger.info
    
    logger.debug(f"Running command: {' '.join(cmd)}")
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    # Stream output live into logger
    for line in process.stdout:
        log_func(line.rstrip())

    process.wait()

    if process.returncode != 0:
        logger.error(f"Command failed with exit code {process.returncode}: {' '.join(cmd)}")
        if check:
            sys.exit(process.returncode)

    return process.returncode


def default_deployment_dir(args):
    """
    Compute the default deployment directory for a site_repo/version/inventory combination.

    Args:
        args (Namespace): Parsed argparse arguments with site_repo, version, inventory

    Returns:
        Path: Absolute path for deployment directory
    """
    site_repo = args.site_repo.split("/")[-1].replace(".git", "")
    path = Path.home() / ".edd" / "deployments" / site_repo / str(args.version) / args.inventory
    return path


def create_deployment_dir(path, force=False):
    """
    Create a deployment directory, optionally clearing it if it exists and is not empty.

    Args:
        path (str|Path): Path to create
        force (bool): If True, remove contents if directory exists

    Returns:
        Path: Absolute path of the deployment directory
    """
    path = Path(path).absolute()
    if path.exists():
        if any(path.iterdir()):
            if not force:
                raise RuntimeError(f"Deployment directory {path} already exists and is not empty. Use --force to override.")
            logger.warning(f"Deployment directory {path} exists and is not empty. Force enabled, clearing contents.")
            for item in path.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
    else:
        path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Deployment directory ready: {path}")
    return path


def clone_or_copy_site_repo(site_repo_path, deploy_dir, branch=None):
    """
    Clone a git repository into the deployment directory.

    Args:
        site_repo_path (str): Git URL of the site_repo
        deploy_dir (str|Path): Deployment directory
        branch (str, optional): Branch or tag to checkout
    """
    logger.debug(f"Cloning repository from {site_repo_path} into {deploy_dir}")
    if branch:
        run_cmd(["git", "clone", "--single-branch", "--depth", "1", "--branch",
                 branch, site_repo_path, str(deploy_dir)], log_func=logger.debug)
    else:
        run_cmd(["git", "clone", "--single-branch", "--depth", "1", site_repo_path, str(deploy_dir)], 
                log_func=logger.debug)


def parse_inventory(inventory_source, vault_pass_file=None):
    """
    Parse the Ansible inventory and extract variables and EDD_PLUGINS,
    resolving Jinja2 templates and decrypting vault-encrypted variables.

    Args:
        inventory_source (str): Path to inventory (file, directory, or script)
        vault_pass_file (str, optional): Path to Ansible vault password file

    Returns:
        tuple: (all_vars: dict of merged variables, plugins: list of plugin dicts)
    """
    loader = DataLoader()

    vault_secret = None
    if vault_pass_file:
        with open(vault_pass_file, "rb") as f:
            vault_secret = VaultSecret(f.read().strip())

    if vault_secret:
        VaultSecretsContext.initialize(VaultSecretsContext([("default", vault_secret)]))

    inventory = InventoryManager(loader=loader, sources=[inventory_source])
    variable_manager = VariableManager(loader=loader, inventory=inventory)

    all_vars = {}
    all_plugins = []

    for host in inventory.get_hosts():
        host_vars = variable_manager.get_vars(host=host)
        templar = Templar(loader=loader, variables=host_vars)

        resolved_vars = {k: templar.template(v) if isinstance(v, str) else v
                         for k, v in host_vars.items()}
        all_vars.update(resolved_vars)

        if "EDD_PLUGINS" in resolved_vars:
            rendered_plugins = []
            for plugin in resolved_vars["EDD_PLUGINS"]:
                rendered_plugins.append({k: templar.template(v) if isinstance(v, str) else v
                                         for k, v in plugin.items()})
            all_plugins.extend(rendered_plugins)

    # Deduplicate plugins by JSON-serialized content
    deduped_plugins = list({json.dumps(p, sort_keys=True): p for p in all_plugins}.values())
    logger.info(f"Found {len(deduped_plugins)} plugins after templating and decryption")
    return all_vars, deduped_plugins


def display_vars(vars_dict):
    """
    Pretty-print a dictionary of variables.

    Args:
        vars_dict (dict): Dictionary of variables
    """
    logger.debug(pprint.pformat(vars_dict, indent=2))


def install_plugins(plugins, method="galaxy"):
    """
    Install plugins using the specified method.

    Args:
        plugins (list[dict]): List of plugin dictionaries
        method (str): "galaxy" or "git"
    """
    if not plugins:
        logger.info("No plugins to install.")
        return

    if method == "galaxy":
        req_file = tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".yml")
        req_file.write("collections:\n")
        for p in plugins:
            req_file.write(f"  - type: git\n    source: {p['source']}\n    version: \"{p['version']}\"\n")
        req_file.close()
        run_cmd(["ansible-galaxy", "collection", "install", "-r", req_file.name, "-p", "./ansible_collections/"], log_func=logger.debug)
    elif method == "git-submodule":
        run_cmd(["git", "submodule", "update", "--init", "--recursive"], log_func=logger.debug)
        run_cmd(["git", "submodule", "update", "--remote", "--recursive"], log_func=logger.debug)
    else:
        raise NotImplementedError(f"Plugin install method '{method}' is unsupported")


def run_playbook(inventory, vault_args, site_config, tags=None, dry_run=False, extra_args_str=None):
    """
    Run an Ansible playbook with optional extra args as a quoted string.

    Args:
        inventory (str): Inventory path
        vault_args (list[str]): Vault argument list (--vault-password-file or --ask-vault-pass)
        site_config (str): Playbook YAML file
        tags (str, optional): Tags to limit execution
        dry_run (bool): If True, log the command instead of running
        extra_args_str (str): String of extra args to pass to ansible-playbook (quoted)
    """
    collections = (Path().cwd() / "ansible_collections").absolute()
    env = os.environ.copy()
    env['ANSIBLE_COLLECTIONS_PATH'] = str(collections)

    # Safely tokenize the extra args string
    extra_args = shlex.split(extra_args_str) if extra_args_str else []

    cmd = ["ansible-playbook", "-i", inventory] + vault_args 
    if extra_args_str:
        cmd.extend(shlex.split(extra_args_str))
    if tags:
        cmd.extend(["--tags", tags])
    cmd.append(site_config)

    if dry_run:
        logger.info("Would run: %s", " ".join(cmd))
    else:
        # avoid the logger by using a direct run call
        subprocess.run(cmd, env=env, check=True)




def cmd_install(args):
    """
    Main install/deploy command handler.

    Args:
        args (Namespace): Parsed command-line arguments
    """
    # Settup file logging for installs
    if not args.dry_run:
        configure_file_logging(args.site_repo, args.version, args.inventory)
    
    deploy_dir = args.deploy_dir or default_deployment_dir(args)
    logger.info("Creating deployment directory: %s", deploy_dir)
    deploy_dir = create_deployment_dir(deploy_dir, force=args.force)

    # Resolve vault password file
    vault_pass_file = None
    if args.vault_pass_file:
        vault_pass_file = str(Path(args.vault_pass_file).expanduser().absolute())
    elif os.getenv("ANSIBLE_VAULT_PASSWORD_FILE"):
        vault_pass_file = os.getenv("ANSIBLE_VAULT_PASSWORD_FILE")
        logger.debug(f"Using vault password file from environment: {vault_pass_file}")

    if vault_pass_file:
        vault_args = ["--vault-password-file", vault_pass_file]
    else:
        logger.warning("No vault password file provided. Falling back to --ask-vault-pass.")
        vault_args = ["--ask-vault-pass"]

    with working_directory(deploy_dir):
        logger.info("Cloning site repository: %s (version: %s)", args.site_repo, args.version)
        clone_or_copy_site_repo(args.site_repo, "./", branch=args.version)
        logger.info("Parsing ansible inventory")
        with suppress_ansible_warnings():
            vars_dict, plugins = parse_inventory(args.inventory, vault_pass_file)
        display_vars(vars_dict)
        
        if not args.dry_run:
            logger.info("Installing plugins")
            install_plugins(plugins, method=args.plugin_install_method)
        else:
            for plugin in plugins:
                logger.info("Would install plugin: %s", plugin)

        if not args.no_pullremote:
            logger.info("Pulling docker images")
            registry = f"https://{vars_dict['docker_registry']}:{vars_dict['docker_registry_port']}"
            logger.debug("Taking registry snapshot before pullremote...")
            before_state = snapshot_registry(registry)
            logger.debug(before_state)
            run_playbook(args.inventory, vault_args, args.site_config,
                         tags="pullremote", dry_run=args.dry_run,
                         extra_args_str=args.ansible_args)
            after_state = snapshot_registry(registry)
            logger.debug("Taking registry snapshow after pullremote")
            logger.debug(after_state)
            report = compare_snapshots(before_state, after_state)
            print_report(report)
        logger.info("Running deployment")
        run_playbook(args.inventory, vault_args, args.site_config, 
                     dry_run=args.dry_run, extra_args_str=args.ansible_args)
        logger.info("Deployment finished")

def replace_plugins(fname, replacement):
    replacement_lines = replacement.splitlines()
    with open(fname, "r") as f:
        lines = f.readlines()
    output_lines = []
    in_plugin_block = False
    for ii, line in enumerate(lines):
        if line.startswith("EDD_PLUGIN"):
            in_plugin_block = True
            continue
        if in_plugin_block:
            if line.startswith(" ") or line.startswith("-") or not line:
                continue
            else:
                in_plugin_block = False
                for replacement_line in replacement_lines:
                    output_lines.append(replacement_line)
        else:
            output_lines.append(line)
    with open(fname, "w") as f:
        for line in output_lines:
            if not line.endswith("\n"):
                line = line + "\n"
            f.write(line)
 
def get_tags_and_branches(url):
    out = subprocess.check_output(["git", "ls-remote", "--tags", "--heads", "--refs", url])
    lines = out.decode().splitlines()
    tags, branches = [], []
    for line in lines:
        if "/tags/" in line:
            tags.append(line.split("/tags/")[-1].strip())
        elif "/heads/" in line:
            branches.append(line.split("/heads/")[-1].strip())
    return tags, branches
 
def update_plugin_list(all_yaml_path, version_map):
    with open(all_yaml_path, "r") as f:
        raw_yaml = yaml.load(f.read(), Loader=Loader)
    plugin_yaml = raw_yaml["EDD_PLUGINS"]
    for p in plugin_yaml:
        p['version'] = str(version_map[p['name']])
    plugin_txt = yaml.dump({"EDD_PLUGINS": plugin_yaml}, Dumper=Dumper, indent=2)
    logger.info(f"Updated EDD plugin yaml:\n{plugin_txt}")
    replace_plugins(all_yaml_path, plugin_txt)
    
def cmd_update_plugins(args):
    """
    Pluging update command handler.

    Args:
        args (Namespace): Parsed command-line arguments
    """
    deploy_dir = args.deploy_dir or default_deployment_dir(args)
    logger.info("Creating deployment directory: %s", deploy_dir)
    deploy_dir = create_deployment_dir(deploy_dir, force=args.force)

    # Resolve vault password file
    vault_pass_file = None
    if args.vault_pass_file:
        vault_pass_file = str(Path(args.vault_pass_file).expanduser().absolute())
    elif os.getenv("ANSIBLE_VAULT_PASSWORD_FILE"):
        vault_pass_file = os.getenv("ANSIBLE_VAULT_PASSWORD_FILE")
        logger.debug(f"Using vault password file from environment: {vault_pass_file}")

    with working_directory(deploy_dir):
        logger.info("Cloning site repository: %s (version: %s)", args.site_repo, args.version)
        clone_or_copy_site_repo(args.site_repo, "./", branch=args.version)
        logger.info("Parsing ansible inventory")
        with suppress_ansible_warnings():
            vars_dict, plugins = parse_inventory(args.inventory, vault_pass_file)
        version_map = {}
        for p in plugins:
            logger.debug(f"Pulling tags and branches for {p['name']}")
            tags, branches = get_tags_and_branches(p['source'])
            if p['version'] in branches:
                logger.warning(f"{p['name']} is set to the {p['version']} branch and will not be updated.")
                version_map[p['name']] = p['version']
            elif not tags:
                logger.warning(f"No tags available for {p['name']}, version will stay as {p['version']}")
                version_map[p['name']] = p['version']
            else:
                new_tag = sorted(tags)[-1]
                if new_tag == p['version']:
                    logger.info(f"{p['name']} already on latest tag ({p['version']})")
                    version_map[p['name']] = p['version']
                else:
                    logger.info(f"{p['name']} updated {p['version']} --> {new_tag}")
                    version_map[p['name']] = new_tag
        # here we need to load the orginal file without templating
        all_yaml_path = os.path.join(args.inventory, "group_vars", "all.yml")
        update_plugin_list(all_yaml_path, version_map)
        if args.commit:
            run_cmd(["git", "add", all_yaml_path], log_func=logger.info)
            run_cmd(["git", "commit", "-m", "[edd-tool] bump plugin versions"], log_func=logger.info)
            logger.warning("Committing currently disabled until branch policy determined")
            #run_cmd(["git", "push"], log_func=logger.info)
            
        # TODO: Clean this up and break into functions
        # TODO: Add logic to only update tags and avoid updating branches    
        
    
def load_rc_config(profile):
    """
    Load configuration profile from ~/.edd-tool.rc.

    Args:
        profile (str): Profile name (e.g. 'production')

    Returns:
        dict: Profile configuration or raises RuntimeError if not found
    """
    rc_path = Path.home() / ".edd-tool.rc"
    if not rc_path.exists():
        logger.warning("No ~/.edd-tool.rc found, skipping profile loading")
        return {}

    with open(rc_path, "r") as f:
        config = yaml.safe_load(f) or {}

    if profile not in config:
        raise RuntimeError(f"Profile '{profile}' not found in {rc_path}")
    return config[profile]


def merge_args_with_profile(args, profile_data):
    """
    Merge profile data into argparse Namespace.
    CLI arguments always override profile values.

    Args:
        args (Namespace): Parsed CLI arguments
        profile_data (dict): Profile defaults
    """
    for key, value in profile_data.items():
        # Argparse converts CLI args to snake_case
        arg_key = key.replace("-", "_")
        current_value = getattr(args, arg_key, None)
        if current_value is None:
            setattr(args, arg_key, value)
            logger.debug(f"Using profile default for {arg_key}={value}")
        else:
            logger.debug(f"CLI override in effect for {arg_key}={current_value}")


def main():
    ensure_rc_file()
    
    """Command-line entry point for the EDD installer with profile support."""
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level (default: INFO)"
    )

    parser = argparse.ArgumentParser(prog="edd-tool", description="EDD Installer Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ##########
    # Deploy #
    ##########
    sp_install = subparsers.add_parser(
        "deploy",
        help="Install and deploy EDD backend instance",
        parents=[parent_parser]
    )
    sp_install.add_argument(
        "config_profile",
        nargs="?",
        help="Optional profile name from ~/.edd-tool.rc (e.g. 'production', 'devel')"
    )
    sp_install.add_argument("--site-repo", help="Git URL of the EDD site repository")
    sp_install.add_argument("--version", default=None, help="Branch or tag for the site repository")
    sp_install.add_argument("--deploy-dir", default=None, help="Deployment directory")
    sp_install.add_argument("--inventory", help="Ansible inventory path (file, dir, or script)")
    sp_install.add_argument(
        "--vault-pass-file",
        help="Path to vault password file (defaults to $ANSIBLE_VAULT_PASSWORD_FILE if set)"
    )
    sp_install.add_argument("--site-config", help="Path to site configuration YAML")
    sp_install.add_argument("--plugin-install-method", choices=["galaxy", "git-submodule"], default="galaxy")
    sp_install.add_argument("--no-pullremote", action="store_true", help="Skip pullremote tag")
    sp_install.add_argument("--force", action="store_true", help="Force overwrite of deployment directory")
    sp_install.add_argument("--dry-run", action="store_true", help="Dry run the deployment")
    sp_install.add_argument(
        "--ansible-args",
        help="Quoted string of extra ansible-playbook args"
    )
    sp_install.set_defaults(func=cmd_install)

    ##########
    # Plugin #
    ##########
    sp_update_plugins = subparsers.add_parser(
        "update-plugins",
        help="Update EDD plugins",
        parents=[parent_parser]
    )
    sp_update_plugins.add_argument(
        "config_profile",
        nargs="?",
        help="Optional profile name from ~/.edd-tool.rc (e.g. 'production', 'devel')"
    )
    sp_update_plugins.add_argument("--site-repo", help="Git URL of the EDD site repository")
    sp_update_plugins.add_argument("--version", default=None, help="Branch or tag for the site repository")
    sp_update_plugins.add_argument("--deploy-dir", default=None, help="Deployment directory")
    sp_update_plugins.add_argument("--inventory", help="Ansible inventory path (file, dir, or script)")
    sp_update_plugins.add_argument(
        "--vault-pass-file",
        help="Path to vault password file (defaults to $ANSIBLE_VAULT_PASSWORD_FILE if set)"
    )
    sp_update_plugins.add_argument("--site-config", help="Path to site configuration YAML")
    sp_update_plugins.add_argument("--force", action="store_true", help="Force overwrite of deployment directory")
    sp_update_plugins.add_argument("--commit", action="store_true", help="Commit plugin changes back to the repository")
    sp_update_plugins.set_defaults(func=cmd_update_plugins)

    args = parser.parse_args()

    # Apply profile defaults if specified
    if args.config_profile:
        try:
            profile_data = load_rc_config(args.config_profile)
            merge_args_with_profile(args, profile_data)
        except RuntimeError as e:
            logger.error(str(e))
            sys.exit(1)

    # Enforce required arguments AFTER profile merge
    missing = []
    for required in ["site_repo", "inventory", "site_config", "version"]:
        if getattr(args, required, None) is None:
            missing.append(required)
    if missing:
        logger.error(f"Missing required arguments after profile merge: {', '.join(missing)}")
        sys.exit(2)

    # Set log level after parsing
    numeric_level = getattr(logging, args.log_level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    logging.getLogger().setLevel(numeric_level)
    logger.debug("Log level set to %s", args.log_level)

    args.func(args)




if __name__ == "__main__":
    main()
