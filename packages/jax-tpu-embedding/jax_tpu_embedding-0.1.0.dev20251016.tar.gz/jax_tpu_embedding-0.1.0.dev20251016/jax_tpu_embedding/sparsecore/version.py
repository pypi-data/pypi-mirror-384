"""JAX TPU Embedding versioning utilities

For releases, the version is of the form:
  xx.yy.zz

For nightly builds, the date of the build is added:
  xx.yy.zz-devYYYMMDD
"""

_base_version = "0.1.0"
_version_suffix = "dev20251016"

# Git commit corresponding to the build, if available.
__git_commit__ = "68249b78ac7d8affe68e2e200391d14b74cf88ab"

# Library version.
__version__ = _base_version + _version_suffix

