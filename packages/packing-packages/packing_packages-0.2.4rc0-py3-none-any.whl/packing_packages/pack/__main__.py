import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

from packing_packages.pack._core import packing_packages


def pack(args: argparse.Namespace) -> None:
    """pack conda environment"""
    if args.env_name is None:
        env_name = os.environ["CONDA_DEFAULT_ENV"]
    else:
        env_name = args.env_name

    dirpath_target = Path(args.dirpath_target).resolve()
    if not dirpath_target.is_dir():
        raise FileNotFoundError(dirpath_target)

    packing_packages(
        env_name=env_name,
        dirpath_target=dirpath_target,
        diff_only=args.diff_only,
        encoding=args.encoding,
        dry_run=args.dry_run,
    )


def add_arguments_pack(parser: argparse.ArgumentParser):
    parser.add_argument(
        "-n",
        "--env-name",
        type=str,
        default=None,
        help=(
            "Name of the conda environment to pack. If not specified, the current active environment is used."
        ),
    )
    parser.add_argument(
        "-d",
        "--dirpath-target",
        type=Path,
        default=".",
        help=(
            "Path to the directory where the packed environment will be saved. Defaults to the current directory."
        ),
    )
    parser.add_argument(
        "-D",
        "--dry-run",
        action="store_true",
        help=(
            "Perform a dry run without actually packing the environment. Useful for testing."
        ),
    )
    parser.add_argument(
        "-e",
        "--encoding",
        type=str,
        default=None,
        help=(
            "Encoding to use for subprocess execution. If not set, system default is used."
        ),
    )
    parser.add_argument(
        "--diff-only",
        action="store_true",
        help=(
            "Only download packages that are not already present in the target directory."
        ),
    )
    parser.set_defaults(func=pack)


def main(cli_args: Sequence[str], prog: Optional[str] = None) -> None:
    """Main function to parse arguments and call the packing function."""
    parser = argparse.ArgumentParser(
        prog=prog, description="pack conda environment"
    )
    add_arguments_pack(parser)
    args = parser.parse_args(cli_args)
    args.func(args)


if __name__ == "__main__":
    import sys

    main(sys.argv[1:])
