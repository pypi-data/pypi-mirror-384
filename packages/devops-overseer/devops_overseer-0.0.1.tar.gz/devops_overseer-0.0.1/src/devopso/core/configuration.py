from __future__ import annotations

import logging
import os
from importlib.resources import files
from pathlib import Path
from typing import Any, Dict, Union

import yaml

_log = logging.getLogger("configuration")


class Error(Exception):
    """
    Exception raised for errors in the devopso configuration.

    This error is raised when a configuration file cannot be parsed,
    validated, or otherwise fails to meet expected requirements.

    Attributes:
        path (str): Path to the configuration file where the error occurred.
        body (str): The detailed error message or context for the failure.
    """

    def __init__(self, path: str, body: str):
        """
        Initialize a configuration error.

        Args:
            path (str): The path to the configuration file that caused the error.
            body (str): A descriptive error message or problematic content.
                        Only the first 500 characters are included in the
                        exception message for readability.

        Example:
            >>> raise Error("/etc/devopso/config.yml", "Missing required field 'logger'")
        """
        super().__init__(f"devopso configuration error in {path}: {body[:500]}")
        self.path = path
        self.body = body


class Configured:
    """
    Base class for loading and managing configuration files.

    This class attempts to load a YAML configuration file from the given path.
    If the file cannot be found at the provided path, it falls back to looking
    in the `devopso` package resources.
    """

    def __init__(self, path: str = "") -> None:
        """
        Initialize the configuration loader.

        Args:
            path (str, optional): Path to the configuration file. Can be an absolute
                path or a relative path to a resource within the `devopso` package.
                Defaults to an empty string.
        """
        self._conf: Dict[str, Any] = {}
        self._conf_path = path
        if not self.read_configuration():
            self._conf_path = files("devopso").joinpath(path)
            self.read_configuration()

    def read_configuration(self) -> bool:
        """
        Attempt to read a YAML configuration file.

        The method checks whether the configured path points to an existing
        `.yml` or `.yaml` file. If found, it loads the configuration into
        `self._conf`.

        Returns:
            bool: True if the configuration file was successfully read,
            False otherwise.
        """
        if self._conf_path:
            p = Path(self._conf_path)
            if p.is_file() and p.suffix.lower() in {".yml", ".yaml"}:
                self._conf = Configuration.read_configuration(p, read_includes=True)
                return True
        return False


class Configuration:
    """
    Utility class for reading and parsing YAML configuration files.

    This class provides static helpers to:
    - Load YAML configuration files into Python dictionaries.
    - Ensure that the root of the YAML file is a mapping (dict).
    - Support recursive includes for composing configurations.
    - Expand environment variables and user home shortcuts in strings.
    """

    @staticmethod
    def read_yaml(path: Union[str, os.PathLike[str]]) -> Dict[str, Any]:
        """
        Read a YAML file and return its contents as a Python dictionary.

        Args:
            path (Union[str, os.PathLike[str]]): Filesystem path to the YAML
                file. Can be a string or any object implementing the
                ``os.PathLike`` interface, such as ``pathlib.Path``.

        Returns:
            Dict[str, Any]: Parsed YAML content as a dictionary.

        Raises:
            FileNotFoundError: If the file does not exist in both the given
                path and the fallback ``devopso`` package resources.
            ValueError: If the root of the YAML file is not a dictionary.
            yaml.YAMLError: If the YAML file cannot be parsed.
        """
        file_path = Path(os.path.expanduser(path))
        _log.debug(f"reading yaml file: {file_path}")
        data = {}
        if not file_path.is_file():
            file_path = files("devopso").joinpath(path)

        if file_path.is_file():
            with file_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict):
                raise Error(path, f"YAML root must be a mapping (dict), got {type(data).__name__}")
        else:
            _log.debug(f"no file to read: {file_path}")
        return data

    @staticmethod
    def write_yaml(path: Union[str, os.PathLike[str]], data: Dict[str, Any]) -> None:
        """
        Write a Python dictionary to a YAML file.

        Args:
            path (Union[str, os.PathLike[str]]): Filesystem path to the YAML
                file. Can be a string or any object implementing the
                ``os.PathLike`` interface, such as ``pathlib.Path``.
            data (Dict[str, Any]): The data to write to the file. Must be a
                dictionary, which will be serialized as a YAML mapping.

        Raises:
            TypeError: If the ``data`` argument is not a dictionary.
            yaml.YAMLError: If the data cannot be serialized to YAML.
            OSError: If the file cannot be written due to I/O issues.
        """
        file_path = Path(os.path.expanduser(path))
        _log.debug(f"writing yaml file: {file_path}")

        if not isinstance(data, dict):
            raise TypeError(f"Expected dictionary for YAML output, got {type(data).__name__}")

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with file_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)

    @staticmethod
    def read_configuration(
        path: Union[str, os.PathLike[str]],
        read_includes: bool = False,
        expand_strs: bool = False,
    ) -> Dict[str, Any]:
        """
        Load a configuration file with optional support for includes and string expansion.

        Args:
            path (Union[str, os.PathLike[str]]): Path to the configuration file.
                Must be a `.yml` or `.yaml` file.
            read_includes (bool, optional): If True, process the ``include`` key
                recursively, merging additional configuration files. Defaults to False.
            expand_strs (bool, optional): If True, expand environment variables
                and user home shortcuts (``~``) in string values. Defaults to False.

        Returns:
            Dict[str, Any]: The loaded configuration dictionary.

        Raises:
            Error: If the provided path is empty.
            ValueError: If the YAML file is not a mapping (dict) at the root.
        """
        _log.debug(f"reading configuration file: {path}")
        conf = {}
        if not path:
            raise Error("no path", "The path provided is empty")

        p = Path(path)
        if p.suffix.lower() in {".yml", ".yaml"}:
            conf = Configuration.read_yaml(p)
        else:
            _log.debug(f"missing file: {p}")

        if "include" in conf and read_includes:
            if isinstance(conf["include"], list):
                for included_conf in conf["include"]:
                    conf = conf | Configuration.read_configuration(Configuration.expand_strs(included_conf))
            elif isinstance(conf["include"], str):
                conf = conf | Configuration.read_configuration(conf["include"])
            else:
                _log.debug("Unsupported type for 'include'")
        else:
            _log.debug("no include")

        if expand_strs:
            conf = Configuration.expand_strs(conf)

        return conf

    @staticmethod
    def expand_strs(obj):
        """
        Recursively expand environment variables and user home shortcuts in strings.

        Args:
            obj (Any): A string, dictionary, list, or nested structure
                containing strings.

        Returns:
            Any: The same structure as the input, with all string values
            expanded (e.g., ``~/path`` → ``/home/user/path``,
            ``${VAR}`` → environment variable value).
        """
        if isinstance(obj, str):
            return os.path.expandvars(os.path.expanduser(obj))
        if isinstance(obj, dict):
            return {k: Configuration.expand_strs(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [Configuration.expand_strs(i) for i in obj]
        return obj
