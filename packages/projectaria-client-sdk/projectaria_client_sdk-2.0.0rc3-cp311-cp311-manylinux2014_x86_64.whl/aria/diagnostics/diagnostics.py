# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

import argparse
import logging
import platform
import tempfile
import time
from pathlib import Path

import aria.sdk as aria
from aria.diagnostics.diagnostics_streaming_handlers import (
    DeviceContextManager,
    StreamingContextManager,
)
from aria.diagnostics.utils import ColoredFormatter, zip_folder

if platform.system() == "Darwin":
    from aria.diagnostics.mac_platform_info import MacPlatformInfo as PlatformInfo
elif platform.system() == "Linux":
    from aria.diagnostics.linux_platform_info import LinuxPlatformInfo as PlatformInfo
else:
    raise ValueError("Unsupported platform. Diagnostics only works on Linux and Mac")

from aria.diagnostics.diagnostics_adb_controller import DiagnosticsAdbController


class DiagnosticsHandler:
    """
    Generates and stores diagnostics artifacts required for debugging
    """

    def __init__(self):
        self.platform_info = PlatformInfo()
        self.adb_controller = DiagnosticsAdbController()

    def diagnostics_capture(self, save_dir: Path) -> None:
        """
        Captures the following diagnostics artifacts
        1. Hardware Information
        2. OS Information
        3. USB Information
        4. Network Information
        5. Aria folder structure
        6. ADB connected devices list
        7. Device logs for all Aria/Oatmeal devices connected
        8. Get device status and info for all connected devices using clientsdk
        9. Attempt streaming for 20 seconds capture logs
        """
        logging.info("#### DIAGNOSTICS CAPTURE STARTED ####")
        hardware_info = self.platform_info.get_hardware_info()
        logging.info("#### HARDWARE INFO ####")
        logging.info(hardware_info)
        os_info = self.platform_info.get_os_info()
        logging.info("#### OS INFO ####")
        logging.info(os_info)
        usb_info = self.platform_info.get_usb_info()
        logging.info("#### USB INFO ####")
        logging.info(usb_info)
        network_info = self.platform_info.get_network_info()
        logging.info("#### NETWORK INFO ####")
        logging.info(network_info)
        aria_folder_structure = self.platform_info.get_aria_folder_structure()
        logging.info("#### ARIA FOLDER STRUCTURE ####")
        logging.info(aria_folder_structure)
        device_list = self.adb_controller.get_device_list()
        logging.info("#### ADB DEVICE LIST ####")
        logging.info(device_list)
        aria_devices = self.adb_controller.get_aria_devices()
        logging.info("#### ARIA DEVICES ####")
        logging.info("Aria Devices : " + ",".join(aria_devices))
        logging.info("#### SAVING DEVICE LOGS ####")
        self.adb_controller.save_all_devices_logs(save_dir)

        logging.info("#### CLIENT SDK CONNECTIVITY ####")
        for device_serial in aria_devices:
            with DeviceContextManager(device_serial) as device_context_manager:
                if device_context_manager.device_init:
                    logging.info(f"#### DEVICE:{device_serial} INFO ####")
                    device_context_manager.log_device_info()
                    logging.info(f"#### DEVICE:{device_serial} STATUS ####")
                    device_context_manager.log_device_status()
                    logging.info(f"#### DEVICE:{device_serial} STREAMING TEST ####")
                    with StreamingContextManager(
                        device_context_manager.get_device()
                    ) as streaming_context_manager:
                        if streaming_context_manager.streaming_started:
                            logging.warning(
                                "Streaming test started. Please wait for 20 seconds.."
                            )
                            time.sleep(20)
                    # Regardless of whether streaming started or not, store the logs when streaming was attempted
                    self.adb_controller.save_device_logs(
                        device_serial, save_dir, "streaming_logcat_"
                    )

        logging.info("#### DIAGNOSTICS CAPTURE COMPLETED ####")


def main() -> None:
    parser = argparse.ArgumentParser(description="Project Aria Client SDK doctor.")
    parser.add_argument(
        "-v", "--verbose", help="increase output verbosity", action="store_true"
    )
    args = parser.parse_args()

    output_dir = tempfile.TemporaryDirectory()
    output_path = Path(output_dir.name)

    # Setup Logger to ensure that logs are persisted to a file
    file_handler = logging.FileHandler(output_path / "diagnostics.log", "w")
    file_handler.setLevel(logging.DEBUG)

    # Create a console handler for logging errors to terminal
    console_handler = logging.StreamHandler()
    if args.verbose:
        console_handler.setLevel(logging.DEBUG)
    else:
        console_handler.setLevel(logging.WARNING)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    colored_formatter = ColoredFormatter()
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(colored_formatter)

    # Add the handlers to the logger
    logger = logging.getLogger()
    # Set base logging level as high as possible (Debug)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    aria.set_log_level(aria.Level.Info)

    handler = DiagnosticsHandler()
    handler.diagnostics_capture(output_path)

    # Zip the temporary directory containing diagnostics artifacts
    zip_folder(output_path, Path() / "diagnostics.zip")

    print(
        colored_formatter.successMessage(
            "All diagnostics artifacts are written to diagnostics.zip file in the current directory. Please upload it for debugging assistance !!"
        )
    )

    # Cleanup the Temporary directory once there is no more use
    output_dir.cleanup()


if __name__ == "__main__":
    main()
