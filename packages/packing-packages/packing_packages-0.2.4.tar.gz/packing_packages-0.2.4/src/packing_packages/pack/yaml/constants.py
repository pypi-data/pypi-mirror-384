PLATFORM_MAP = {
    "win-64": {
        "pypi": "win_amd64",
        "conda": "win-64",
    },
    "win-32": {
        "pypi": "win32",
        "conda": "win-32",
    },
    "linux-64": {
        "pypi": "manylinux2014_x86_64",
        "conda": "linux-64",
    },
    "linux-aarch64": {
        "pypi": "manylinux2014_aarch64",
        "conda": "linux-aarch64",
    },
    "linux-ppc64le": {
        "pypi": "manylinux2014_ppc64le",
        "conda": "linux-ppc64le",
    },
    "linux-s390x": {
        "pypi": "manylinux2014_s390x",
        "conda": "linux-s390x",
    },
    "osx-64": {
        "pypi": "macosx_10_9_x86_64",
        "conda": "osx-64",
    },
    "osx-arm64": {
        "pypi": "macosx_11_0_arm64",
        "conda": "osx-arm64",
    },
}
"""
This dictionary `PLATFORM_MAP` maps platform identifiers used in package management
to corresponding platform strings for PyPI and Conda repositories.

Keys represent platform identifiers typically used in package distribution:
- 'win-64': Windows 64-bit
- 'win-32': Windows 32-bit
- 'linux-64': Linux 64-bit
- 'linux-aarch64': Linux ARM 64-bit
- 'linux-ppc64le': Linux PowerPC 64-bit little-endian
- 'linux-s390x': Linux IBM Z (s390x)
- 'osx-64': macOS 64-bit (x86_64)
- 'osx-arm64': macOS ARM 64-bit (arm64)

For each platform, the dictionary provides mappings for:
- 'pypi': PyPI platform string
- 'conda': Conda platform string

Examples of usage:
- To obtain the PyPI platform string for Windows 64-bit:
  `PLATFORM_MAP['win-64']['pypi']` returns 'win_amd64'
- To obtain the Conda platform string for macOS ARM 64-bit:
  `PLATFORM_MAP['osx-arm64']['conda']` returns 'osx-arm64'
"""
