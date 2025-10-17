import argparse
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

from packing_packages.pack.yaml._core import packing_packages_from_yaml


def pack_from_yaml(args: argparse.Namespace) -> None:
    dirpath_target = Path(args.dirpath_target).resolve()
    if not dirpath_target.is_dir():
        raise FileNotFoundError(dirpath_target)

    packing_packages_from_yaml(
        args.filepath_yaml,
        platform=args.platform,
        dirpath_target=dirpath_target,
        diff_only=args.diff_only,
        dry_run=args.dry_run,
        encoding=args.encoding,
    )


def add_arguments_pack_from_yaml(parser: argparse.ArgumentParser):
    parser.add_argument(
        "filepath_yaml",
        metavar="FILEPATH_YAML",
        type=Path,
        help="conda .yaml file",
    )
    parser.add_argument(
        "-p",
        "--platform",
        type=str,
        choices=[
            "win-64",
            "win-32",
            "linux-64",
            "linux-aarch64",
            "linux-ppc64le",
            "linux-s390x",
            "osx-64",
            "osx-arm64",
        ],
        help="platform, e.g.) win-64, linux-64 etc.",
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
    parser.set_defaults(func=pack_from_yaml)


def main(cli_args: Sequence[str], prog: Optional[str] = None) -> None:
    parser = argparse.ArgumentParser(prog=prog, description="")
    add_arguments_pack_from_yaml(parser)
    args = parser.parse_args(cli_args)
    args.func(args)


if __name__ == "__main__":
    import sys

    main(sys.argv[1:])
