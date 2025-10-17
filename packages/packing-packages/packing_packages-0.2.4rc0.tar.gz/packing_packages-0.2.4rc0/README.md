# PACKING-PACKAGES

[![CI](https://github.com/yu9824/packing-packages/actions/workflows/CI.yml/badge.svg)](https://github.com/yu9824/packing-packages/actions/workflows/CI.yml)
[![docs](https://github.com/yu9824/packing-packages/actions/workflows/docs.yml/badge.svg)](https://github.com/yu9824/packing-packages/actions/workflows/docs.yml)
[![release-pypi](https://github.com/yu9824/packing-packages/actions/workflows/release-pypi.yml/badge.svg)](https://github.com/yu9824/packing-packages/actions/workflows/release-pypi.yml)

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://github.com/python/mypy)

[![python_badge](https://img.shields.io/pypi/pyversions/packing-packages)](https://pypi.org/project/packing-packages/)
[![license_badge](https://img.shields.io/pypi/l/packing-packages)](https://pypi.org/project/packing-packages/)
[![PyPI version](https://badge.fury.io/py/packing-packages.svg)](https://pypi.org/project/packing-packages/)
[![Downloads](https://static.pepy.tech/badge/packing-packages)](https://pepy.tech/project/packing-packages)

<!-- [![Conda Version](https://img.shields.io/conda/vn/conda-forge/packing-packages.svg)](https://anaconda.org/conda-forge/packing-packages)
[![Conda Platforms](https://img.shields.io/conda/pn/conda-forge/packing-packages.svg)](https://anaconda.org/conda-forge/packing-packages) -->

This module provides functionality to pack conda environments and their dependencies into a specified directory.

You can use this package to migrate a conda environment to another offline machine with the same operating system.


## Install

```bash
# Need python, setuptools, pip package
pip install packing-packages

```

## How to use

see `--help`.

### Pack

```bash
packing-packages pack -d .

```

### Install

```bash
packing-packages install .

```

## Example

### Source device

```bash
conda activate <envname>
python -m pip install packing-packages
python -m packing_packages pack -d .

```

### Destination device (offline)

```bash
conda create -yn <envname> --offline
conda activate <envname>
conda install --use-local --offline ./conda/*
python -m pip install --no-deps --no-build-isolation ./pypi/*

```

## Notes

### Installing PyTorch from a Non-PyPI Source

If you want to use pip to download packages from a source other than PyPI (e.g., the official PyTorch index), standard methods may not complete successfully. Some packages may fail to download and must be handled manually. This process is complex, and automated support is not currently provided.

```bash
# Installation command
pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cu124

# Download command (without dependencies)
# --no-deps: download only the specified package
# -d: set the destination directory
pip download torch==2.5.1 --index-url https://download.pytorch.org/whl/cu124 --no-deps -d .
```

### Handling Installation Failures with `--use-pep517`

Some older packages may not install successfully using `pip install`. In such cases, you may be able to install them manually using the `--use-pep517` option:

```bash
pip install <package-name> --use-pep517
```

### Choosing Between Standard Install Commands and `packing-packages install`

There are two main methods for installing packages:

1. Using `conda install` or `pip install`
2. Using the `packing-packages install` command, which wraps these tools and provides error handling

| Command                         | Advantages                             | Disadvantages                |
| ------------------------------- | -------------------------------------- | ---------------------------- |
| `conda install` / `pip install` | Fast execution                         | Stops immediately upon error |
| `packing-packages install`      | Skips failed packages and reports them | Slower installation process  |


### Packing an Environment Using a `.yaml` File

~~If you already have an environment file (`.yaml`), you can create and pack the environment on an online machine with the same OS:~~

Now you can pack them by using the following command even if the different OS;

```bash
packing-packages pack yaml /path/to/file.yaml
```

### Using a Proxy (If Required)

If you are in an environment that requires a proxy, you may need to configure the proxy settings before downloading or installing packages:

```bash
export HTTP_PROXY="your proxy"
export HTTPS_PROXY="your proxy"
```
