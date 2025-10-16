#!/usr/bin/env python3
"""Setup script for Chainlit with Brazil build integration."""

from setuptools import setup, find_packages
import os

# Run our build script first
from build import build
build()

# Read version from pyproject.toml with Python version compatibility
import sys
with open("pyproject.toml", "rb") as f:
    if sys.version_info >= (3, 11):
        import tomllib
        pyproject = tomllib.load(f)
    else:
        try:
            import tomli
            pyproject = tomli.load(f)
        except ImportError:
            # Fallback to older toml library (pre-3.11 compatibility)
            try:
                import toml
                with open("pyproject.toml", "r") as rf:
                    pyproject = toml.load(rf)
            except ImportError:
                raise ImportError("No TOML parser available. Please install 'tomli' or 'toml' package.")

project_info = pyproject["project"]

# Handle authors format (list of dicts vs list of strings)
authors_list = project_info.get("authors", [])
if authors_list and isinstance(authors_list[0], dict):
    authors_str = ", ".join([author.get("name", "") for author in authors_list])
else:
    authors_str = ", ".join(authors_list)

# Get version from hatch version config
version = "0.1.0"  # fallback version
try:
    # Try to read version from chainlit/version.py as specified in pyproject.toml
    version_file = "chainlit/version.py"
    if os.path.exists(version_file):
        with open(version_file, "r") as f:
            exec(f.read())
            version = locals().get("__version__", "0.1.0")
except Exception:
    pass

setup(
    name=project_info.get("name", "chainlit-aki"),
    version=version,
    description=project_info.get("description", ""),
    long_description=open("README.md").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author=authors_str,
    license=project_info.get("license", {}).get("text", "Apache-2.0"),
    url=project_info.get("urls", {}).get("Homepage", ""),
    packages=find_packages(exclude=["chainlit.*.dist", "chainlit.*.dist.*"]),
    include_package_data=True,
    package_data={
        "chainlit": [
            "frontend/dist/**/*",
            "copilot/dist/**/*",
        ],
    },
    python_requires=">=3.10,<4.0.0",
    entry_points={
        "console_scripts": [
            "chainlit=chainlit.cli:cli",
        ],
    },
    classifiers=project_info.get("classifiers", []),
)