"""
Version information for github-action-toolkit.

Follows semantic versioning (https://semver.org/) with support for
development builds via suffix (e.g., ".dev20231201").
"""

_MAJOR = "0"
_MINOR = "8"
# On main and in a nightly release the patch should be one ahead of the last
# released build.
_PATCH = "0"
# This is mainly for nightly builds which have the suffix ".dev$DATE". See
# https://semver.org/#is-v123-a-semantic-version for the semantics.
_SUFFIX = ""

# Short version for display (e.g., "0.7")
VERSION_SHORT = f"{_MAJOR}.{_MINOR}"

# Full version string (e.g., "0.7.0" or "0.7.0.dev20231201")
VERSION = f"{_MAJOR}.{_MINOR}.{_PATCH}{_SUFFIX}"
