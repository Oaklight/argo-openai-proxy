#!/usr/bin/env python3
import argparse
import asyncio
import os
import subprocess
import sys
from argparse import RawTextHelpFormatter
from typing import Optional

from loguru import logger
from packaging import version

from .__init__ import __version__
from .app import run
from .config import PATHS_TO_TRY, validate_config
from .endpoints.extras import get_latest_pypi_version

logger.remove()  # Remove default handlers
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{message}</level>",
    level="INFO",
)


def parsing_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Argo Proxy CLI",
        formatter_class=RawTextHelpFormatter,
    )
    parser.add_argument(
        "config",
        type=str,
        nargs="?",  # makes argument optional
        help="Path to the configuration file",
        default=None,
    )
    parser.add_argument(
        "--host",
        "-H",
        type=str,
        help="Host address to bind the server to",
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        help="Port number to bind the server to",
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=False,  # default is False, so --verbose will set it to True
        help="Enable verbose logging, override if `verbose` set False in config",
    )
    group.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        default=False,  # default is False, so --quiet will set it to True
        help="Disable verbose logging, override if `verbose` set True in config",
    )

    parser.add_argument(
        "--edit",
        "-e",
        action="store_true",
        help="Open the configuration file in the system's default editor for editing",
    )
    parser.add_argument(
        "--validate",
        "-vv",
        action="store_true",
        help="Validate the configuration file and exit",
    )
    parser.add_argument(
        "--show",
        "-s",
        action="store_true",
        help="Show the current configuration during launch",
    )
    parser.add_argument(
        "--version",
        "-V",
        # action="store_true",  # Changed from 'version' to 'store_true'
        action="version",
        version=f"%(prog)s {version_check()}",
        help="Show the version and check for updates",
    )

    args = parser.parse_args()

    return args


def set_config_envs(args: argparse.Namespace):
    if args.port:
        os.environ["PORT"] = str(args.port)
    if args.verbose:
        os.environ["VERBOSE"] = str(True)
    if args.quiet:
        os.environ["VERBOSE"] = str(False)


def open_in_editor(config_path: Optional[str] = None):
    paths_to_try = [config_path] if config_path else PATHS_TO_TRY

    # Add EDITOR from environment variable if set, followed by defaults
    editors_to_try = [os.getenv("EDITOR")] if os.getenv("EDITOR") else []
    editors_to_try += ["notepad"] if os.name == "nt" else ["nano", "vi", "vim"]
    # Filter out None editors
    editors_to_try = [e for e in editors_to_try if e is not None]

    for path in paths_to_try:
        if path and os.path.exists(path):
            for editor in editors_to_try:
                try:
                    subprocess.run([editor, path], check=True)
                    return
                except FileNotFoundError:
                    continue  # Try the next editor in the list
                except Exception as e:
                    logger.error(f"Failed to open editor with {editor} for {path}: {e}")
                    sys.exit(1)

    logger.error("No valid configuration file found to edit.")
    sys.exit(1)


def version_check() -> str:
    ver_content = [__version__]
    latest = asyncio.run(get_latest_pypi_version())

    if latest:
        # Use packaging.version to compare versions correctly
        if version.parse(latest) > version.parse(__version__):
            ver_content.extend(
                [
                    f"New version available: {latest}",
                    "Update with `pip install --upgrade argo-proxy`",
                ]
            )

    return "\n".join(ver_content)


def main():
    args = parsing_args()

    if args.edit:
        open_in_editor(args.config)
        return

    set_config_envs(args)

    try:
        # Validate config in main process only
        logger.warning(f"Running Argo-Proxy {version_check()}")
        config_instance = validate_config(args.config, args.show)
        if args.validate:
            logger.info("Configuration validation successful.")
            return
        run(host=config_instance.host, port=config_instance.port)
    except KeyError:
        logger.error("Port not specified in configuration file.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start ArgoProxy server: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred while starting the server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
