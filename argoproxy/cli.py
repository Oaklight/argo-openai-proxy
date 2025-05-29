#!/usr/bin/env python3
import argparse
import os
import sys

from loguru import logger

logger.remove()  # Remove default handlers
logger.add(sys.stdout, colorize=True, format="<level>{message}</level>", level="INFO")


def main():
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
        default="0.0.0.0",
        help="Host address to bind the server to",
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8000,
        help="Port number to bind the server to",
    )
    parser.add_argument(
        "--num-worker",
        "-n",
        type=int,
        default=5,
        help="Number of worker processes to run",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        type=bool,
        default=False,
        help="Enable verbose logging",
    )
    args = parser.parse_args()

    if args.config:
        os.environ["CONFIG_PATH"] = args.config
    if args.show:
        os.environ["SHOW_CONFIG"] = "true"
    if args.host:
        os.environ["HOST"] = args.host
    if args.port:
        os.environ["PORT"] = str(args.port)
    if args.num_worker:
        os.environ["NUM_WORKERS"] = str(args.num_worker)
    if args.verbose:
        os.environ["VERBOSE"] = str(args.verbose)

    # import config after setting CONFIG_PATH
    from .app import app
    from .config import config_instance

    try:
        app.run(
            host=config_instance.host,
            port=config_instance.port,
            workers=config_instance.num_workers,
        )
    except KeyError:
        logger.error("Port not specified in configuration file.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred while starting the server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
