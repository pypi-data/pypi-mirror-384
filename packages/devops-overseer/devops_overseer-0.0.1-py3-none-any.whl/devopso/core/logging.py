import logging

from devopso.core.configuration import Configured


class ConfiguredLogger(Configured):
    def __init__(self, config_path: str) -> None:
        super().__init__(config_path)
        if "logger" in self._conf:
            self._logger = logging.getLogger(self._conf["logger"]["name"])

    def critical(self, message: str):
        self._logger.critical(message)

    def error(self, message: str):
        self._logger.error(message)

    def warning(self, message: str):
        self._logger.warning(message)

    def info(self, message: str):
        self._logger.info(message)

    def debug(self, message: str):
        self._logger.debug(message)
