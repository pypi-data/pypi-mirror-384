import logging
import logging.config
from pathlib import Path

from devopso.core.configuration import Configuration

_LOGGING_CONFIGURATION = "resources/configs/logging.yml"


def _check_app_resources_directories():
    """Making sure all the necessary files and folders are there."""
    _log = logging.getLogger("boot")
    _log.debug("checking directories (main config one already checked for logging)")

    _log.debug("checking configurations")
    config_dir = Path.home() / ".config" / "devops-overseer" / "configs"
    config_dir.mkdir(parents=True, exist_ok=True)

    _log.debug("checking clients configurations")
    config_dir = Path.home() / ".config" / "devops-overseer" / "configs" / "clients"
    config_dir.mkdir(parents=True, exist_ok=True)


def _configure_logging():
    """Configure logging once, at first import of the package."""
    config_dir = Path.home() / ".config" / "devops-overseer"
    config_dir.mkdir(parents=True, exist_ok=True)
    logging.config.dictConfig(Configuration.read_configuration(_LOGGING_CONFIGURATION, expand_strs=True))


# Ensure configuration runs only once
if not logging.getLogger().hasHandlers():
    _configure_logging()

_check_app_resources_directories()
