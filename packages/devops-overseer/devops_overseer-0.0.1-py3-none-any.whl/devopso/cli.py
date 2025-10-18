import argparse
import logging
from importlib.metadata import entry_points
from importlib.resources import files
from pathlib import Path

_APP_LOGGER_NAME = "devops-overseer"
_BANNER_PATH = "resources/devops-overseer.banner"


def get_hello_string() -> str:
    """
    Return a short status message for the overseer CLI.

    This function provides a simple, human-readable string used for
    logging or banner messages when the application starts.

    Returns:
        str: A greeting or status string.
    """
    return "The overseer is in the room"


def print_banner() -> None:
    """
    Print the application banner to the console.

    The banner is loaded from a text file within the `devopso` package
    resources and printed to standard output. It typically contains the
    application logo or ASCII art.

    Raises:
        FileNotFoundError: If the banner file cannot be found in package resources.
        UnicodeDecodeError: If the banner file cannot be decoded as UTF-8.
    """
    content = Path(files("devopso").joinpath(_BANNER_PATH)).read_text(encoding="utf-8")
    print(content)


def load_plugins(subparsers):
    """
    Dynamically load and register CLI subcommands from entry points.

    This function discovers all registered entry points under the
    'devopso.plugins' group and invokes each plugin function, passing
    the `subparsers` object so that new subcommands can be added.

    Args:
        subparsers (argparse._SubParsersAction): The subparser manager used
            to register subcommands for the main CLI.

    Raises:
        ImportError: If a plugin cannot be imported or loaded.
        Exception: If a plugin's registration function fails.
    """
    for ep in entry_points(group="devopso.plugins"):
        plugin_fn = ep.load()
        plugin_fn(subparsers)


def main():
    """
    Entry point for the `devopso` command-line interface.

    This function initializes logging, prints the startup banner,
    sets up the argument parser, loads all available plugins as CLI
    subcommands, and executes the selected subcommand based on user input.

    Steps:
        1. Print the banner.
        2. Log a startup message.
        3. Initialize the main argument parser.
        4. Load all registered plugins.
        5. Parse arguments and execute the corresponding function.

    Raises:
        SystemExit: If argument parsing fails or if the subcommand function raises.
    """
    print_banner()
    logging.getLogger(_APP_LOGGER_NAME).warning(get_hello_string())

    parser = argparse.ArgumentParser(prog="devopso")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    load_plugins(subparsers)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
