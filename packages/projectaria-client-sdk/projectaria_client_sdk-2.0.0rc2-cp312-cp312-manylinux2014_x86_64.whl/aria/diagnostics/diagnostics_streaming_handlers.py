# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

import logging
from contextlib import AbstractContextManager
from typing import Sequence

import aria.sdk as aria
import numpy as np
from projectaria_tools.core.sensor_data import (
    BarometerData,
    ImageDataRecord,
    MotionData,
)


class DeviceContextManager(AbstractContextManager):
    """
    Device context manager class which ensures that the connection to the device is handled as RAII
    NOTE: Make sure to check device_init state since device initialization can fail
    """

    def __init__(self, device_serial: str):
        self._device_serial = device_serial
        self._device_client = None
        self._device = None
        self.device_init = False

    def __enter__(self):
        try:
            self._device_client = aria.DeviceClient()
            client_config = aria.DeviceClientConfig()
            client_config.device_serial = self._device_serial
            self._device_client.set_client_config(client_config)
            # 2. Connect to Aria
            self._device = self._device_client.connect()
            self.device_init = True
        except Exception as e:
            logging.error(f"Unable to connect to device:{self._device_serial} - {e}")
            self.device_init = False
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logging.error(f"DeviceContextManager Exception type: {exc_type.__name__}")
            logging.error(f"DeviceContextManager Exception value: {exc_val}")
            logging.error(
                "DeviceContextManager Traceback:", exc_info=(exc_type, exc_val, exc_tb)
            )
        try:
            if self._device and self._device_client:
                self._device_client.disconnect(self._device)
                logging.info(f"Disconnected device:{self._device_serial}")
        except Exception as e:
            logging.error(f"Unable to disconnect device:{self._device_serial} - {e}")

    def get_device(self):
        return self._device

    def log_device_status(self):
        if not self._device:
            logging.error(
                f"Unable to retrieve device_status for Device:{self._device_serial}. Device not connected"
            )
            return
        try:
            device_status = self._device.status
            logging.info(f"battery_level: {device_status.battery_level}")
            logging.info(f"charger_connected: {device_status.charger_connected}")
            logging.info(f"charging: {device_status.charging}")
            logging.info(f"wifi_enabled: {device_status.wifi_enabled}")
            logging.info(f"wifi_configured: {device_status.wifi_configured}")
            logging.info(f"wifi_connected: {device_status.wifi_connected}")
            logging.info(f"wifi_ip_address: {device_status.wifi_ip_address}")
            logging.info(f"wifi_device_name: {device_status.wifi_device_name}")
            logging.info(f"wifi_ssid: {device_status.wifi_ssid}")
            logging.info(f"logged_in: {device_status.logged_in}")
            logging.info(f"developer_mode: {device_status.developer_mode}")
            logging.info(f"adb_enabled: {device_status.adb_enabled}")
            logging.info(
                f"thermal_mitigation_triggered: {device_status.thermal_mitigation_triggered}"
            )
            logging.info(f"skin_temp_celsius: {device_status.skin_temp_celsius}")
            logging.info(
                f"default_recording_profile: {device_status.default_recording_profile}"
            )
            logging.info(f"is_recording_allowed: {device_status.is_recording_allowed}")
            logging.info(f"device_mode: {device_status.device_mode}")
        except Exception as e:
            logging.error(
                f"Unable to retrieve device_status for Device:{self._device_serial}. Exception: {e}"
            )

    def log_device_info(self):
        if not self._device:
            logging.error(
                f"Unable to retrieve device_info for Device:{self._device_serial}. Device not connected"
            )
            return
        try:
            device_info = self._device.info
            logging.info(f"board: {device_info.board}")
            logging.info(f"bootloader: {device_info.bootloader}")
            logging.info(f"brand: {device_info.brand}")
            logging.info(f"device: {device_info.device}")
            logging.info(f"host: {device_info.host}")
            logging.info(f"id: {device_info.id}")
            logging.info(f"manufacturer: {device_info.manufacturer}")
            logging.info(f"model: {device_info.model}")
            logging.info(f"product: {device_info.product}")
            logging.info(f"serial: {device_info.serial}")
            logging.info(f"time: {device_info.time}")
            logging.info(f"type: {device_info.type}")
            logging.info(f"user: {device_info.user}")
        except Exception as e:
            logging.error(
                f"Unable to retrieve device_info for Device:{self._device_serial}. Exception: {e}"
            )


class DiagnosticsStreamingClientObserver:
    """
    Diagnostics Streaming client observer class.
    NOTE: This is very simplistic for now and only increments counts upon callback
    """

    def __init__(self):
        self._image_callback_count = 0
        self._imu_callback_count = 0
        self._magneto_callback_count = 0
        self._baro_callback_count = 0
        self._streaming_failure_callback_count = 0

    def on_image_received(self, image: np.array, record: ImageDataRecord) -> None:
        self._image_callback_count += 1

    def on_imu_received(self, samples: Sequence[MotionData], imu_idx: int) -> None:
        self._imu_callback_count += 1

    def on_magneto_received(self, sample: MotionData) -> None:
        self._magneto_callback_count += 1

    def on_baro_received(self, sample: BarometerData) -> None:
        self._baro_callback_count += 1

    def on_streaming_client_failure(self, reason: aria.ErrorCode, message: str) -> None:
        self._streaming_failure_callback_count += 1

    def summarize(self):
        logging.info("Streaming Summary")
        logging.info(f"image_callback_count: {self._image_callback_count}")
        logging.info(f"imu_callback_count: {self._imu_callback_count}")
        logging.info(f"magneto_callback_count: {self._magneto_callback_count}")
        logging.info(f"baro_callback_count: {self._baro_callback_count}")
        logging.info(
            f"streaming_failure_callback_count: {self._streaming_failure_callback_count}"
        )


class StreamingContextManager(AbstractContextManager):
    """
    Streaming context manager class which ensures that the streaming is handled as RAII
    Enter starts streaming and exits stop the streaming saving streaming results to log
    NOTE: Make sure to check streaming_started state since setting up / starting streaming can fail
    """

    def __init__(self, device: aria.Device):
        self._device = device
        self._streaming_manager = None
        self._streaming_client = None
        self._streaming_client_observer = DiagnosticsStreamingClientObserver()
        self._streaming_state = aria.StreamingState.NotStarted
        self.streaming_started = False

    def __enter__(self):
        try:
            self._streaming_manager = self._device.streaming_manager
            self._streaming_client = self._streaming_manager.streaming_client
            streaming_state = self._streaming_manager.streaming_state
            # Handle case where the streaming is already in progress for this device
            if streaming_state == aria.StreamingState.Streaming:
                logging.warning(
                    f"Streaming is already in progress. Stopping streaming for this test. Device:{self._device.info.serial}"
                )
                self._streaming_manager.stop_streaming()
            streaming_config = aria.StreamingConfig()
            streaming_config.profile_name = "profile18"
            streaming_config.streaming_interface = aria.StreamingInterface.Usb
            streaming_config.security_options.use_ephemeral_certs = True
            self._streaming_manager.streaming_config = streaming_config
            self._streaming_manager.start_streaming()
            self._streaming_state = self._streaming_manager.streaming_state
            logging.info(f"Streaming state: {self._streaming_state}")
            self._streaming_client.set_streaming_client_observer(
                self._streaming_client_observer
            )
            self._streaming_client.subscribe()
            self.streaming_started = True
        except Exception as e:
            logging.error(
                f"Unable to start streaming. Device:{self._device.info.serial} Exception: {e}"
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logging.error(
                f"StreamingContextManager Exception type: {exc_type.__name__}"
            )
            logging.error(f"StreamingContextManager Exception value: {exc_val}")
            logging.error(
                "StreamingContextManager Traceback:",
                exc_info=(exc_type, exc_val, exc_tb),
            )
        try:
            if self._streaming_client and self._streaming_client.is_subscribed():
                self._streaming_client.unsubscribe()
            if (
                self._streaming_state == aria.StreamingState.Streaming
                or self._streaming_state == aria.StreamingState.Started
            ):
                self._streaming_client_observer.summarize()
                self._streaming_manager.stop_streaming()
            logging.info(f"Streaming stopped for Device:{self._device.info.serial}")
        except Exception as e:
            logging.error(f"Unable to stop streaming. Exception: {e}")
