# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import subprocess
import sys

try:
    from importlib.resources import files
except ImportError:
    # Fallback for Python < 3.9
    from importlib_resources import files


def get_cli_path():
    return str(files("aria").joinpath("aria-cli"))


def get_adb_path():
    return str(files("aria").joinpath("tools/adb"))


def main():
    # Get the aria CLI binary
    cmd = [get_cli_path()]

    # If we found packaged adb from the wheel use that
    adb_path = get_adb_path()
    if os.path.exists(adb_path):
        cmd += ["--adb-path", adb_path]

    # Add any additional arguments
    cmd += sys.argv[1:]
    process = subprocess.run(cmd)
    sys.exit(process.returncode)


if __name__ == "__main__":
    main()
