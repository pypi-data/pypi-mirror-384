# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

from pathlib import Path

from aria.diagnostics.platform_info import PlatformInfo
from aria.diagnostics.utils import run_command_noexcept


class MacPlatformInfo(PlatformInfo):
    """
    Mac specific implementation of PlatformInfo
    """

    def get_hardware_info(self) -> str:
        return run_command_noexcept(["system_profiler", "SPHardwareDataType"])

    def get_os_info(self) -> str:
        return run_command_noexcept(["system_profiler", "SPSoftwareDataType"])

    def get_usb_info(self) -> str:
        return run_command_noexcept(["system_profiler", "SPUSBDataType"])

    def get_network_info(self) -> str:
        return run_command_noexcept(["system_profiler", "SPNetworkDataType"])

    def get_aria_folder_structure(self) -> str:
        aria_dir = Path.home() / ".aria"
        return run_command_noexcept(["ls", "-alR", aria_dir])
