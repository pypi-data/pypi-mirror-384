# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

import logging
import subprocess
import zipfile
from pathlib import Path

from termcolor import colored


class ColoredFormatter(logging.Formatter):
    """
    Create a custom formatter for logging based on levels
    This color codes the outputs for better visualization
    """

    def __init__(self):
        super().__init__()
        self._format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        self._FORMATS = {
            logging.DEBUG: colored(self._format, "dark_grey"),
            logging.INFO: colored(self._format, "light_grey"),
            logging.WARNING: colored(self._format, "yellow"),
            logging.ERROR: colored(self._format, "light_red"),
            logging.CRITICAL: colored(self._format, "red"),
        }

    def format(self, record):
        log_fmt = self._FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

    def successMessage(self, text):
        return colored(text, "green")


def run_command_noexcept(command_list):
    """
    Runs a command and returns the output.
    If the command fails, it logs the error and returns None.
    """
    try:
        output = subprocess.check_output(command_list).decode("utf-8")
        return output
    # Exception handling intentionally broad and not restricted to subprocess.CalledProcessError
    # as we cannot afford crashing as part of diagnostics
    except Exception as e:
        logging.error(
            "Command Issued - " + " ".join([str(command) for command in command_list])
        )
        logging.error(f"Exception encountered: {e}")
        return None


def zip_folder(folder_path: Path, output_zip_file: Path):
    """
    Zips a folder and all its contents
    """
    with zipfile.ZipFile(output_zip_file, "w") as zip_file:
        for file in folder_path.rglob("*"):
            if file.is_file():
                relative_path = file.relative_to(folder_path)
                zip_file.write(file, relative_path)
