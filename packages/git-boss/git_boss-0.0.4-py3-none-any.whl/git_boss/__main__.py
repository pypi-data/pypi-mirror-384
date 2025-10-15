"""Command-line interface for the git_boss package.

When run as a module (python -m git_boss) this file provides a small CLI.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from git_boss.commands import set_starting_folder, add, remove, sync, ls, grep, version
from . import config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="git_boss",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "   __| _ _| __ __|    _ )   _ \    __|   __| \n"
            "  (_ |   |     |      _ \  (   | \__ \ \__ \ \n"
            " \___| ___|   _|     ___/ \___/  ____/ ____/ \n"
        ),
    )
    parser.add_argument("--config", help="Path to YAML config file", required=False)

    subparsers = parser.add_subparsers(dest="command")

    # add git project URL
    add_parser = subparsers.add_parser("add", help="Add a git project URL to the config")
    add_parser.add_argument("url", help="Git project URL to add")
    # remove git project URL
    remove_parser = subparsers.add_parser("remove", help="Remove a git project URL from the config")
    remove_parser.add_argument("url", help="Git project URL to remove")
    # sync command - clone projects from config
    subparsers.add_parser("sync", help="Clone projects listed in the config into startingFolder")
    # ls command - list git projects from config
    subparsers.add_parser("ls", help="List git projects from the config file")
    # grep command - filter git projects by substring
    grep_parser = subparsers.add_parser("grep", help="Find projects that contain a substring")
    grep_parser.add_argument("pattern", help="Substring to search for in project URLs")
    # set-starting-folder subcommand
    set_parser = subparsers.add_parser("set-starting-folder", help="Overwrite startingFolder in the config file")
    set_parser.add_argument("path", help="Absolute path to set as startingFolder")
    # version command - print project metadata
    subparsers.add_parser("version", help="Print package name, version, description and homepage")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Load config if provided; pass it to commands instead of storing globally
    if getattr(args, "config", None):
        cfg_path = Path(args.config)
        cfg = config.create_from_file_path(args.config)
    else:
        # Load the bundled default config shipped with the module
        cfg_path = Path(__file__).parent / "config.default.yaml"
        cfg = config.create_from_file_path(str(cfg_path))

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "sync":
        return sync.run(cfg, str(cfg_path))

    if args.command == "add":
        return add.run(cfg, args.url, str(cfg_path))

    if args.command == "remove":
        return remove.run(cfg, args.url, str(cfg_path))

    if args.command == "ls":
        return ls.run(cfg, str(cfg_path))

    if args.command == "grep":
        return grep.run(cfg, args.pattern, str(cfg_path))

    if args.command == "set-starting-folder":
        return set_starting_folder.run(cfg, args.path, str(cfg_path))
    
    if args.command == "version":
        return version.run(cfg, str(cfg_path))

    # Unknown command
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
