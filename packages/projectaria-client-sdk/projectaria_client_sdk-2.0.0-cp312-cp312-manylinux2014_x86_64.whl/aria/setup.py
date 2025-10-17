#!/usr/bin/env python3
# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

import pathlib

from _version import __version__ as version
from setuptools import find_packages, setup
from setuptools.dist import Distribution

# The directory containing this file
HERE = pathlib.Path(__file__).parent.resolve()

# The text of the README file
README = (HERE / "README.md").read_text()


class BinaryDistribution(Distribution):
    # Forces a binary package with platform name

    def has_ext_modules(self):
        return True


# This call to setup() does all the work
setup(
    name="projectaria_client_sdk",
    author="Meta",
    # NOTE: If/when you need to bump the version, do it in __init__.py.
    version=version,
    description="Project Aria Client SDK For Python",
    long_description=README,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "projectaria-tools==2.0.0",
        "setuptools",
        "termcolor",
    ],
    package_data={
        "aria": [
            "libsdk_core.*",
            "sdk.*.so",
            "sdk_gen2.*.so",  # oatmeal specific
            "sdk.pyi",
            "__cli__.py",
            "__gen2_cli__.py",
            "doctor.py",
            "extract_sdk_samples.py",
            "aria-cli",
            "aria_gen2_cli",
            "libomp.so",
            "tools/adb",
            "samples/*",
            "gen2_samples/*",
            "samples/ticsync/*",
            "diagnostics/*",
            "sdk_gen2/*",
        ],
    },
    entry_points={
        "console_scripts": [
            "aria=aria.__cli__:main",
            "aria_gen2=aria.__gen2_cli__:main",
            "aria_doctor=aria.doctor:main",
            "aria_diagnostics=aria.diagnostics.diagnostics:main",
            "aria_streaming_viewer=aria.aria_streaming_viewer:main",
        ],
    },
    distclass=BinaryDistribution,
)

# NOTE: To generate the distribution, make sure the version has been bumped in
# both the _version.py, then call this module:
# python3 setup.py bdist_wheel
