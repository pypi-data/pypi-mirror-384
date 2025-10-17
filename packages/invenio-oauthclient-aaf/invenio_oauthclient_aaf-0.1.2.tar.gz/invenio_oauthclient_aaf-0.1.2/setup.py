"""Setup for invenio-oauthclient-aaf package.

DEPRECATED: This file is maintained for backward compatibility only.
Modern Python packaging uses pyproject.toml exclusively (PEP 517/518).

For development, use: uv pip install -e .
For building: uv build
"""

from setuptools import find_packages, setup

# Note: All metadata is now in pyproject.toml
# This file exists only for legacy tool compatibility
setup(
    packages=find_packages(exclude=["tests", "tests.*"]),
)
