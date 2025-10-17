import argparse
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

from packing_packages.install._core import install_packages


def install(args: argparse.Namespace) -> None:
    """Install packages in the conda environment."""
    if args.env_name is None:
        env_name = os.environ["CONDA_DEFAULT_ENV"]
    else:
        env_name = args.env_name

    dirpath_packages = Path(args.dirpath_packages).resolve()
    if not dirpath_packages.is_dir():
        raise FileNotFoundError(dirpath_packages)

    install_packages(
        dirpath_packages=dirpath_packages,
        env_name=env_name,
        encoding=args.encoding,
    )


def add_arguments_install(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "dirpath-packages",
        type=Path,
        default=".",
        help=(
            "Path to the directory containing packages to install (e.g., *.tar.bz2, *.conda). "
            "Defaults to the current directory ('.') if not specified."
        ),
        metavar="DIRPATH_PACKAGES",
    )
    parser.add_argument(
        "-n",
        "--env-name",
        type=str,
        default=None,
        help=(
            "Name of the conda environment where packages will be installed. "
            "If not specified, the currently active environment will be used."
        ),
    )
    parser.add_argument(
        "-e",
        "--encoding",
        type=str,
        default=None,
        help=(
            "Encoding to use for subprocess execution (e.g., when calling conda commands). "
            "Defaults to the system encoding if not specified."
        ),
    )
    parser.set_defaults(func=install)


def main(cli_args: Sequence[str], prog: Optional[str] = None) -> None:
    """Main function to parse arguments and call the install function."""
    parser = argparse.ArgumentParser(
        prog=prog, description="Install packages in the conda environment"
    )
    add_arguments_install(parser)
    args = parser.parse_args(cli_args)
    args.func(args)
