from importlib import resources as _resources
from pathlib import Path as _Path

def get_shell_script_path() -> str:
    """Return filesystem path to the deploy-cli.sh shell script."""
    with _resources.as_file(_resources.files(__package__).joinpath("deploy-cli-standalone-v1.0.1-jpmc-bec9ef6/deploy-cli.sh")) as p:
        return str(_Path(p))

def get_config_dir() -> str:
    """Return filesystem path to the config directory."""
    with _resources.as_file(_resources.files(__package__).joinpath("deploy-cli-standalone-v1.0.1-jpmc-bec9ef6/config")) as p:
        return str(_Path(p))

def get_readme_path() -> str:
    """Return filesystem path to the README.md file."""
    with _resources.as_file(_resources.files(__package__).joinpath("deploy-cli-standalone-v1.0.1-jpmc-bec9ef6/README.md")) as p:
        return str(_Path(p))
