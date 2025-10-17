import os
import subprocess
from pathlib import Path
from typing import Optional, Union

from packing_packages.constants import (
    EXTENSIONS_CONDA,
    EXTENSIONS_PYPI,
)
from packing_packages.utils import check_encoding, is_installed

if is_installed("tqdm"):
    from tqdm import tqdm
else:
    from packing_packages.utils import (  # type: ignore[assignment]
        dummy_tqdm as tqdm,
    )

from packing_packages.logging import get_child_logger

_logger = get_child_logger(__name__)


def install_packages(
    env_name: Optional[str] = None,
    dirpath_packages: Union[str, os.PathLike] = ".",
    encoding: Optional[str] = None,
) -> None:
    """install conda packages

    Parameters
    ----------
    env_name : str, optional
        conda environment name, by default None
    dirpath_packages : Union[str, os.PathLike], optional
        directory path of packages
    """
    encoding = check_encoding(encoding)

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
            raise ValueError(f"Environment '{env_name}' not found.")

    _logger.info(
        f"Installing packages from '{dirpath_packages}' into '{env_name}'"
    )

    dirpath_packages = Path(dirpath_packages).resolve()

    list_filepaths_conda: list[Path] = sum(
        [
            [
                filepath
                for filepath in dirpath_packages.glob(f"**/*{ext}")
                if filepath.is_file()
            ]
            for ext in EXTENSIONS_CONDA
        ],
        start=[],
    )
    list_filepaths_pypi: list[Path] = sum(
        [
            [
                filepath
                for filepath in dirpath_packages.glob(f"**/*{ext}")
                if filepath.is_file()
            ]
            for ext in EXTENSIONS_PYPI
        ],
        start=[],
    )

    list_filepaths_conda_failed: list[Path] = []
    # install conda packages
    for filepath_conda in tqdm(
        list_filepaths_conda,
        desc="Installing conda packages",
        unit="package",
    ):
        result_conda_install = subprocess.run(
            [
                os.environ["CONDA_EXE"],
                "install",
                "-y",
                "-n",
                env_name,
                "--offline",
                "--use-local",
                str(filepath_conda),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _logger.info(result_conda_install.stdout.decode(encoding))
        if result_conda_install.returncode != 0:
            _logger.warning(
                f"Failed to install conda package: {filepath_conda}"
            )
            _logger.error(result_conda_install.stderr.decode(encoding))
            list_filepaths_conda_failed.append(filepath_conda)

    # install pypi packages
    list_filepaths_pypi_failed: list[Path] = []
    for filepath_pypi in tqdm(
        list_filepaths_pypi,
        desc="Installing PyPI packages",
        unit="package",
    ):
        result_pip_install = subprocess.run(
            [
                os.environ["CONDA_EXE"],
                "run",
                "-n",
                env_name,
                "pip",
                "install",
                "--no-deps",
                "--no-build-isolation",
                str(filepath_pypi),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _logger.info(result_pip_install.stdout.decode(encoding))
        if result_pip_install.returncode != 0:
            _logger.warning(f"Failed to install PyPI package: {filepath_pypi}")
            _logger.error(result_pip_install.stderr.decode(encoding))
            list_filepaths_pypi_failed.append(filepath_pypi)

    if list_filepaths_conda_failed:
        _logger.warning(
            f"Failed to install {len(list_filepaths_conda_failed)} conda packages."
        )
        for filepath in list_filepaths_conda_failed:
            _logger.warning(f"  - {filepath}")
    else:
        _logger.info("All conda packages installed successfully.")
    if list_filepaths_pypi_failed:
        _logger.warning(
            f"Failed to install {len(list_filepaths_pypi_failed)} PyPI packages."
        )
        for filepath in list_filepaths_pypi_failed:
            _logger.warning(f"  - {filepath}")
    else:
        _logger.info("All PyPI packages installed successfully.")

    _logger.info(
        f"Installed {len(list_filepaths_conda) + len(list_filepaths_pypi)} packages."
    )
    _logger.info(
        f"Failed to install {len(list_filepaths_conda_failed) + len(list_filepaths_pypi_failed)} packages."
    )
    if not list_filepaths_conda_failed and not list_filepaths_pypi_failed:
        _logger.info("All packages installed successfully.")
    else:
        _logger.warning(
            "Some packages failed to install. Please check the logs."
        )
