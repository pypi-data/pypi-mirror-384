# EDD Tool

`edd-tool` is a command-line utility for deploying and managing EDD (Effelsberg Direct Digitisation) backend instances.  
It automates cloning site repositories, resolving variables from Ansible inventories, installing plugins, and running playbooks.

## Purpose

The `edd-tool` simplifies the deployment of EDD site repositories managing the docker update cycle and plugin installation phases of an EDD backend deployment.

## Installation

It is strongly recommended to install and run `edd-tool` inside a Python virtual environment to avoid dependency conflicts.

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install from PyPI
pip install edd-tool
```

You can verify the installation with:

```bash
edd-tool --help
```

## Basic usage

```
$ edd-tool deploy --h
usage: edd-tool deploy [-h] [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [--site-repo SITE_REPO] [--version VERSION]
                       [--deploy-dir DEPLOY_DIR] [--inventory INVENTORY] [--vault-pass-file VAULT_PASS_FILE]
                       [--site-config SITE_CONFIG] [--plugin-install-method {galaxy,git-submodule}] [--no-pullremote] [--force]
                       [--dry-run] [--ansible-args ANSIBLE_ARGS]
                       [config_profile]

positional arguments:
  config_profile        Optional profile name from ~/.edd-tool.rc (e.g. 'production', 'devel')

options:
  -h, --help            show this help message and exit
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level (default: INFO)
  --site-repo SITE_REPO
                        Git URL of the EDD site repository
  --version VERSION     Branch or tag for the site repository
  --deploy-dir DEPLOY_DIR
                        Deployment directory
  --inventory INVENTORY
                        Ansible inventory path (file, dir, or script)
  --vault-pass-file VAULT_PASS_FILE
                        Path to vault password file (defaults to $ANSIBLE_VAULT_PASSWORD_FILE if set)
  --site-config SITE_CONFIG
                        Path to site configuration YAML
  --plugin-install-method {galaxy,git-submodule}
  --no-pullremote       Skip pullremote tag
  --force               Force overwrite of deployment directory
  --dry-run             Dry run the deployment
  --ansible-args ANSIBLE_ARGS
                        Quoted string of extra ansible-playbook args
```

## Deployment profiles

To simplify the deployment interface it is possible to define deployment profiles in the `~/.edd-tool.rc` configuration file.
This will be used to set the default values for CLI arguments. For example `~/.edd-tool.rc` might contain:

```YAML
## Example ~/.edd-tool.rc
## Define reusable deployment profiles here
## Uncomment and update the profiles below to get started

production:
  site_config: production_config.yml
  site_repo: https://gitlab.com/site-repos/my-telescope-site.git
  inventory: production
  vault-pass-file: ~/.edd/production.pwd

development:
  site_config: development_config.yml
  site_repo: https://gitlab.com/site-repos/my-telescope-site.git
  inventory: development
  vault-pass-file: ~/.edd/development.pwd
```

The name of a profile can be passed as a positional argument to the `deploy` command of `edd-tool`:

```bash
edd-tool deploy development --force --version 250915.0
```

or 

```bash
edd-tool deploy production --dry-run --force --version 250915.0
```
