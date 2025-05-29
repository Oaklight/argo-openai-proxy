#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys

from loguru import logger

from . import app
from .config import validate_config

logger.remove()  # Remove default handlers
logger.add(sys.stdout, colorize=True, format="<level>{message}</level>", level="INFO")


def parsing_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Argo Proxy CLI")
    parser.add_argument(
        "config",
        type=str,
        nargs="?",  # makes argument optional
        help="Path to the configuration file",
        default=None,
    )
    parser.add_argument(
        "--show",
        "-s",
        action="store_true",
        help="Show the current configuration",
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
    parser.add_argument(
        "--num-worker",
        "-n",
        type=int,
        help="Number of worker processes to run",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        type=bool,
        help="Enable verbose logging",
    )
    args = parser.parse_args()

    return args


def set_config_envs(args: argparse.Namespace):
    if args.port:
        os.environ["PORT"] = str(args.port)
    if args.verbose:
        os.environ["VERBOSE"] = str(args.verbose)


def main():
    args = parsing_args()
    set_config_envs(args)

    try:
        # Validate config in main process only
        config_instance = validate_config(args.config, args.show)
        # Run the app with validated config
        app.app.run(
            host=args.host or config_instance.host,
            port=args.port or config_instance.port,
            workers=args.num_worker or config_instance.num_workers,
        )
    except KeyError:
        logger.error("Port not specified in configuration file.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start Sanic server: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred while starting the server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
