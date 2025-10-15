# prophecy-deploy-cli-config

Configuration files package for the Prophecy Deploy CLI used by JPMC.

## Contents
- Shell script wrapper (`deploy-cli.sh`)
- Configuration files (`config/embedded.yml`)
- Documentation (`README.md`)

## Install
```bash
pip install prophecy-deploy-cli-config
```

## Usage
```python
import prophecy_deploy_cli_config

# Get path to the shell script wrapper
shell_script = prophecy_deploy_cli_config.get_shell_script_path()
print(f"Shell script: {shell_script}")

# Get path to config directory
config_dir = prophecy_deploy_cli_config.get_config_dir()
print(f"Config directory: {config_dir}")

# Get path to README
readme_path = prophecy_deploy_cli_config.get_readme_path()
print(f"README: {readme_path}")
```

## Note
This package contains only configuration files. For the complete CLI with the main executable and dependencies, install `prophecy-deploy-cli` instead.
