# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

import logging
from pathlib import Path

from aria.diagnostics.utils import run_command_noexcept


class DiagnosticsAdbController:
    def __init__(self):
        self._adb_path = None
        try:
            # Intentional decision to allow using diagnostics_adb_controller both inside and outside of Client SDK wheel
            import pkg_resources

            adb_path = pkg_resources.resource_filename("aria", "tools/adb")
            if Path(adb_path).is_file():
                pass
            else:
                logging.warning(
                    "adb not packaged as resource. Using system default adb instead"
                )
                adb_path = "adb"
        except Exception as e:
            logging.warning(
                f"Unable to find adb packaged as resource. Using system default adb instead. Exception: {e}"
            )
            adb_path = "adb"
        if self._check_adb(adb_path):
            self._adb_path = adb_path

    def _check_adb(self, adb_path: str) -> bool:
        """
        Check to ensure that the adb_path is valid. Logs error otherwise
        """
        ret = run_command_noexcept([adb_path, "version"])
        # Basic sanity to ensure that adb is actually installed
        if ret and "Installed" in ret:
            return True
        logging.error(
            f"Adb path {adb_path} not found. Please pass the correct path to adb using --adb_path"
        )
        return False

    def get_device_list(self) -> str:
        """
        Return the list of adb devices connected (as a string)
        """
        if self._adb_path:
            ret = run_command_noexcept([self._adb_path, "devices", "-l"])
            return ret

    def get_aria_devices(self) -> list:
        """
        Returns device serial numbers for all Aria devices connected
        """
        aria_devices = []
        devices = self.get_device_list()
        if devices:
            for line in devices.splitlines():
                # Currently only Aria is supported (Oatmeal not supported)
                if "product:gemini" in line:
                    device_serial = line.split()[0].strip()
                    aria_devices.append(device_serial)
        return aria_devices

    def save_device_logs(self, device_serial, save_folder: Path, prefix: str):
        """
        Saves device logs for a given Aria/Oatmeal device connected
        """
        aria_devices = self.get_aria_devices()
        if device_serial in aria_devices:
            filename = prefix + device_serial + ".log"
            save_path = save_folder / filename
            logging.info(f"Saving device:{device_serial} logs to {filename}")
            logs = run_command_noexcept(
                [self._adb_path, "-s", device_serial, "logcat", "-d"]
            )
            if logs:
                with open(save_path, "w") as file:
                    file.write(logs)
            else:
                logging.error(f"Unable to retrieve logs for device:{device_serial}")
        else:
            logging.error(
                f"Invalid device serial - {device_serial}. This device is not connected !"
            )

    def save_all_devices_logs(self, save_folder: Path, prefix: str = "logcat_") -> None:
        """
        Saves device logs for all Aria devices connected
        """
        aria_devices = self.get_aria_devices()
        if aria_devices:
            for device_serial in aria_devices:
                self.save_device_logs(device_serial, save_folder, prefix)
