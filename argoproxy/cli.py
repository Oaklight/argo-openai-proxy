#!/usr/bin/env python3
import argparse
import os


def main():
    parser = argparse.ArgumentParser(description="Argo Proxy CLI")
    parser.add_argument(
        "config",
        type=str,
        nargs="?",  # makes argument optional
        help="Path to the configuration file",
        default=None,
    )
    args = parser.parse_args()

    if args.config:
        os.environ["CONFIG_PATH"] = args.config

    # import config after setting CONFIG_PATH
    from argoproxy.config import config

    print(config)


if __name__ == "__main__":
    main()
