import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from shutil import copyfile
from typing import NamedTuple, Optional, Union

from packing_packages.constants import EXTENSIONS_CONDA, EXTENSIONS_PYPI
from packing_packages.logging import get_child_logger
from packing_packages.utils import check_encoding, is_installed

if is_installed("tqdm"):
    from tqdm.auto import tqdm
else:
    from packing_packages.utils import (  # type: ignore[assignment]
        dummy_tqdm as tqdm,
    )


class Package(NamedTuple):
    """

    Parameters
    ----------
    name : str
        package name
    version : str
        package version
    build : str
        package build string
    channel : str
        package channel

    """

    name: str
    version: str
    build: str
    channel: str


def get_existing_packages_conda(
    dirpath_output: Union[os.PathLike, str],
) -> set[tuple[str, str, str]]:
    """get existing conda packages in the output directory

    Parameters
    ----------
    dirpath_output : str
        output directory path

    Returns
    -------
    set[tuple[str, str, str]]
        set of existing conda packages (name, version, build)
    """
    dirpath_output = Path(dirpath_output).resolve()

    st_packages_conda: set[tuple[str, str, str]] = set()
    for ext in EXTENSIONS_CONDA:
        for filepath_conda in dirpath_output.glob(f"**/*.{ext}"):
            if match := (
                re.match(rf"(.+)-(\d+.+?)-(.+)\.{ext}$", filepath_conda.name)
            ):
                package = Package(
                    name=match.group(1),
                    version=match.group(2),
                    build=match.group(3),
                    channel="",
                )
                st_packages_conda.add(package[:3])
    return st_packages_conda


def get_existing_packages_pypi(
    dirpath_output: Union[os.PathLike, str],
) -> set[tuple[str, str]]:
    """get existing pypi packages in the output directory

    Parameters
    ----------
    dirpath_output : str
        output directory path

    Returns
    -------
    set[tuple[str, str]]
        set of existing pypi packages (name, version)
    """
    dirpath_output = Path(dirpath_output).resolve()

    st_packages_pypi: set[tuple[str, str]] = set()
    for ext in EXTENSIONS_PYPI:
        for filepath_pypi in dirpath_output.glob(f"**/*.{ext}"):
            if match := re.match(
                rf"(.+)-(\d+.+?)-.+\.{ext}$", filepath_pypi.name
            ):
                package = Package(
                    name=match.group(1),
                    version=match.group(2),
                    build="",
                    channel="pypi",
                )
                st_packages_pypi.add((package.name, package.version))
                st_packages_pypi.add(
                    (package.name.replace("_", "-"), package.version)
                )
    return st_packages_pypi


_logger = get_child_logger(__name__)


def packing_packages(
    env_name: Optional[str] = None,
    dirpath_target: Union[os.PathLike, str] = ".",
    diff_only: bool = False,
    encoding: Optional[str] = None,
    dry_run: bool = False,
) -> None:
    """packaging conda environment packages

    Parameters
    ----------
    env_name : str
        conda environment name
    dirpath_target : str
        target directory path
    diff_only : bool
        if True, only download packages that are not already downloaded
    encoding : str
        encoding for subprocess output
    dry_run : bool
        if True, do not download files
    """

    encoding = check_encoding(encoding)

    if dry_run:
        _logger.warning("This is a dry run. No files will be downloaded.")

    # check install conda
    if "CONDA_EXE" not in os.environ:
        raise ValueError(
            "Please install conda and set the CONDA_EXE environment variable."
        )

    DIRPATH_CONDA_ROOT = Path(os.environ["CONDA_EXE"]).parent.parent.resolve()
    dirpath_pkgs = DIRPATH_CONDA_ROOT / "pkgs"

    if env_name is None:
        env_name = os.environ["CONDA_DEFAULT_ENV"]
    else:
        # check environment name
        result_conda_env_list = subprocess.run(
            [
                os.environ["CONDA_EXE"],
                "info",
                "-e",
            ],
            stdout=subprocess.PIPE,
        )
        conda_env_list = result_conda_env_list.stdout.decode(
            encoding
        ).splitlines()
        env_name_list = {
            line.split()[0]
            for line in conda_env_list
            if line and line[0] != "#"
        }
        if env_name not in env_name_list:
            raise ValueError(
                f"'{env_name}' is not found. Please check the environment name."
            )
    _logger.info(f"Packing conda environment '{env_name}'...")

    dirpath_target = Path(dirpath_target).resolve()
    if not dirpath_target.is_dir():
        raise FileNotFoundError(dirpath_target)

    dirpath_output = dirpath_target / env_name
    if dirpath_output.is_dir():
        if diff_only:
            _logger.info(
                f"Output directory '{dirpath_output}' already exists. "
                "Only downloading missing packages..."
            )

            st_existing_conda = get_existing_packages_conda(dirpath_output)
            st_existing_pypi = get_existing_packages_pypi(dirpath_output)

            # Update dirpath_output to diff directory
            dirpath_output = (
                dirpath_output
                / "diffs"
                / datetime.now().strftime("%Y%m%d_%H%M")
            )
            dirpath_output.mkdir(parents=True)
        else:
            _logger.warning(
                f"Output directory '{dirpath_output}' already exists. "
                "We will add files to this directory. "
                "If you want to add only missing packages, set 'diff_only=True'."
            )

            st_existing_conda = set()
            st_existing_pypi = set()

    if not dry_run:
        os.makedirs(dirpath_output, exist_ok=True)

    _logger.info(f"Packing to '{dirpath_output}'...")

    dirpath_output_pypi = dirpath_output / "pypi"
    dirpath_output_conda = dirpath_output / "conda"
    for _dirpath in (dirpath_output_pypi, dirpath_output_conda):
        if not dry_run:
            os.makedirs(_dirpath, exist_ok=True)

    result_conda_list = subprocess.run(
        [
            os.environ["CONDA_EXE"],
            "list",
            "-n",
            env_name,
        ],
        stdout=subprocess.PIPE,
    )
    conda_list = result_conda_list.stdout.decode(encoding).splitlines()

    # conda listの出力をパースする
    list_packages: list[Package] = []
    for line in conda_list:
        if line[0] == "#":
            continue
        line_split = tuple(line.strip().split())
        package = Package(
            name=line_split[0],
            version=line_split[1],
            build=line_split[2],
            channel=line_split[3] if len(line_split) > 3 else "",
        )
        list_packages.append(package)
        if package.name == "python":
            env_python_version = package.version

    # conda listで取得したpythonのバージョンと、現在のpythonのバージョンが異なる場合は警告を出す
    if (
        tuple(map(int, env_python_version.split(".")[:2]))
        != sys.version_info[:2]
    ):
        _logger.warning(
            "The Python version of the conda environment and the current Python version do not match. "
            "It is recommended to use the same Python version."
        )

    list_failed_packages: list[Package] = []
    for package in tqdm(list_packages):
        # pypiの場合はダウンロードする
        if package.channel == "pypi":
            if (package.name, package.version) in st_existing_pypi:
                _logger.info(
                    f"'{package.name}=={package.version}' is already downloaded. Skipping..."
                )
                continue

            if dry_run:
                result_pip_download = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        f"{package.name}=={package.version}",
                        "--no-deps",
                        "--no-build-isolation",
                        "--python-version",
                        f"{env_python_version}",
                        "--dry-run",
                        "--target",
                        dirpath_output_pypi.as_posix(),
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            else:
                result_pip_download = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "download",
                        f"{package.name}=={package.version}",
                        "--no-deps",
                        "--python-version",
                        f"{env_python_version}",
                        "-d",
                        dirpath_output_pypi.as_posix(),
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

            _logger.info("\n" + result_pip_download.stdout.decode(encoding))
            if result_pip_download.returncode != 0:
                _logger.warning(f"'{package}' is not found.")
                _logger.error(result_pip_download.stderr.decode(encoding))
                list_failed_packages.append(package)

            continue

        # conda
        if package[:3] in st_existing_conda:
            _logger.info(
                f"'{package.name}-{package.version}-{package.build}' is already downloaded. Skipping..."
            )
            continue

        tup_filepaths_package = tuple(
            dirpath_pkgs
            / f"{package.name}-{package.version}-{package.build}.{ext}"
            for ext in EXTENSIONS_CONDA
        )

        # あるときは、dirpath_pkgsからコピーする
        for filepath_package in tup_filepaths_package:
            if filepath_package.is_file():
                _logger.info(
                    f"Copying '{filepath_package.name}' from cache..."
                )
                if not dry_run:
                    copyfile(
                        filepath_package,
                        dirpath_output_conda / filepath_package.name,
                    )
                break
        else:
            _logger.info(f"{package} is not found in the conda package cache.")

            # ない場合は、直接ダウンロード
            result_conda_search = subprocess.run(
                [
                    os.environ["CONDA_EXE"],
                    "search",
                    f"{package.name}={package.version}={package.build}",
                    "--info",
                ]
                + (
                    ["-c", package.channel]
                    if package.channel
                    else ["-c", "defaults"]
                ),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if match_conda_package_url := re.search(
                r"url\s*:\s*(https?://\S+\.{})".format(
                    r"(?:"
                    + r"|".join(EXTENSIONS_CONDA).replace(r".", r"\.")
                    + r")"
                ),
                result_conda_search.stdout.decode(encoding),
            ):
                url = match_conda_package_url.group(1)
            else:
                _logger.warning(
                    "Could not detect the URL of the conda package."
                )
                continue

            filename_download_conda = Path(url).name
            _logger.info(f"Downloading '{filename_download_conda}' from {url}")
            if not dry_run:
                try:
                    _ = urllib.request.urlretrieve(
                        url, dirpath_output_conda / filename_download_conda
                    )
                except Exception as error:
                    _logger.exception(repr(error))
                    _logger.warning(
                        f"'{filename_download_conda}' could not be downloaded from {url}."
                    )
                    list_failed_packages.append(package)

    n_success = len(list_packages) - len(list_failed_packages)
    n_failed = len(list_failed_packages)
    _logger.info(
        f"{n_success} / {(n_success + n_failed)} packages are success!"
    )

    if n_failed > 0:
        for package in list_failed_packages:
            _logger.warning(f"  {package.name}=={package.version}")
        _logger.warning(
            "Please check the above packages. "
            "You can try to download them manually."
        )


if __name__ == "__main__":
    packing_packages("open-webui", "./open-webui")
