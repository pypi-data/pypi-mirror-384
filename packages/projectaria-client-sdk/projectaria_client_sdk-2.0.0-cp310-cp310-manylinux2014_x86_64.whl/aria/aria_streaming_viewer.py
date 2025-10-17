# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

import argparse
import signal
import sys
from datetime import timedelta

import aria.sdk_gen2 as sdk_gen2
import aria.stream_receiver as receiver
import numpy as np
from projectaria_tools.core.calibration import DeviceCalibration
from projectaria_tools.core.mps import hand_tracking, interpolate_hand_tracking_result
from projectaria_tools.core.sensor_data import ImageData, ImageDataRecord
from projectaria_tools.tools.aria_rerun_viewer.aria_data_plotter import (
    AriaDataViewer,
    AriaDataViewerConfig,
)


# Global set to track functions that have already warned
_warned_functions = set()

DEFAULT_HAND_POSE_INTERPOLATION_PERIOD_MS = 100  # 100ms interpolation period


def warn_once(func, message):
    """
    Utility function to issue a warning only once per function.
    Uses the 'warn once' pattern to prevent spam when called repeatedly.

    Args:
        func: The function object to associate the warning with
        message: The warning message to display
    """
    # Create a unique identifier for the function
    func_id = f"{func.__qualname__}:{message}"
    if func_id not in _warned_functions:
        print(f"[aria_streaming_viewer][WARNING]: {message}")
        _warned_functions.add(func_id)


class AriaStreamManager:
    """
    Aria Stream Manager class that manages both streaming data interface and visualization.
    This class encapsulates the stream handler and viewer to ensure proper lifetime management.
    """

    def __init__(
        self,
        enable_real_time: bool = False,
        interpolate: bool = False,
        jpeg_quality: int = 50,
    ):
        """Initialize the Aria Stream Manager with streaming and viewing components."""
        # Initialize the streaming viewer
        self.viewer = AriaStreamingViewer(
            interpolate=interpolate, jpeg_quality=jpeg_quality
        )

        # Create the stream handler
        self.stream_receiver = receiver.StreamReceiver(
            enable_image_decoding=True, enable_raw_stream=False
        )

        # Set up all callbacks
        self._setup_callbacks()

        # enable real-time queue size
        if enable_real_time:
            self._setup_real_time()

    def _setup_real_time(self):
        # Set up queue sizes to be small for real time
        self.stream_receiver.set_rgb_queue_size(2)
        self.stream_receiver.set_slam_queue_size(8)
        self.stream_receiver.set_et_queue_size(4)
        self.stream_receiver.set_imu_queue_size(800)
        self.stream_receiver.set_imu_batch_queue_size(1)
        self.stream_receiver.set_vio_queue_size(10)
        self.stream_receiver.set_vio_high_freq_queue_size(800)
        self.stream_receiver.set_vio_high_freq_batch_queue_size(1)
        self.stream_receiver.set_eye_gaze_queue_size(10)
        self.stream_receiver.set_hand_pose_queue_size(10)

    def _setup_callbacks(self):
        """Set up all callbacks between stream handler and viewer."""
        self.stream_receiver.register_device_calib_callback(self.viewer.calib_callback)
        self.stream_receiver.register_rgb_callback(self.viewer.image_callback)
        self.stream_receiver.register_slam_callback(self.viewer.image_callback)
        self.stream_receiver.register_et_callback(self.viewer.image_callback)
        self.stream_receiver.register_imu_batch_callback(self.viewer.imu_batch_callback)

        self.stream_receiver.register_audio_callback(self.viewer.audio_callback)
        self.stream_receiver.register_barometer_callback(self.viewer.barometer_callback)
        self.stream_receiver.register_magnetometer_callback(
            self.viewer.magnetometer_callback
        )
        self.stream_receiver.register_gps_callback(self.viewer.gps_callback)
        self.stream_receiver.register_hand_pose_callback(self.viewer.hand_pose_callback)
        self.stream_receiver.register_eye_gaze_callback(self.viewer.eye_gaze_callback)
        self.stream_receiver.register_vio_high_frequency_callback(
            self.viewer.vio_high_frequency_callback
        )
        self.stream_receiver.register_vio_callback(self.viewer.vio_callback)

    def get_stream_receiver(self):
        """Get the underlying stream handler for use with the server."""
        return self.stream_receiver


class AriaStreamingViewer:
    """
    Aria Streaming Viewer class that encapsulates AriaDataViewer and all sensor callbacks.
    """

    def __init__(self, interpolate: bool = False, jpeg_quality: int = 50):
        """Initialize the Aria Streaming Viewer."""
        self.aria_data_viewer = None
        self.interpolate = interpolate
        self.viewer_config = AriaDataViewerConfig()
        self.viewer_config.jpeg_quality = jpeg_quality
        self.aria_data_viewer = AriaDataViewer(
            config=self.viewer_config,
            device_calibration=None,
        )

        # count vio high frequency callback for downsampling
        self.vio_high_frequency_data_count = 0

        # add visualization queue to sync plotting for RGB and SLAM images
        self.hand_pose_viz_queue = []
        self.hand_pose_viz_matching_index = {}
        self.eye_gaze_viz_queue = []
        self.eye_gaze_matching_index = {}

    def _get_gen2_camera_label_from_camera_id(self, camera_id: int):
        """
        Get the mapping between camera IDs and their corresponding stream labels.

        Returns:
            dict: Mapping of camera ID (int) to stream label (str)
        """
        gen2_camera_id_to_label = {
            1: "slam-front-left",
            2: "slam-front-right",
            4: "slam-side-left",
            8: "slam-side-right",
            16: "camera-et-left",
            32: "camera-et-right",
            64: "camera-rgb",
        }
        if camera_id not in gen2_camera_id_to_label:
            raise RuntimeError(
                f"Invalid camera id provided: {camera_id}. Can not find corresponding camera label."
            )

        return gen2_camera_id_to_label[camera_id]

    def calib_callback(
        self,
        device_calibration: DeviceCalibration,
    ):
        """Calibration callback - set rescaled device calibration in AriaDataViewer."""
        # Parse calibration
        if device_calibration is None:
            print("Failed to initialize AriaDataViewer - invalid calibration data")
            return

        self.aria_data_viewer.set_device_calibration(device_calibration)

    def find_data_closest(self, query_time_sec, viz_queue):
        if len(viz_queue) == 0:
            return None, None
        min_time_interval_sec = DEFAULT_HAND_POSE_INTERPOLATION_PERIOD_MS / 2.0 * 1e-3
        best_matching_data = None
        best_matching_index = -1
        for reverse_index, data in enumerate(reversed(viz_queue)):
            index = len(viz_queue) - 1 - reverse_index
            if data is None:
                continue
            delta_time = abs(data.tracking_timestamp.total_seconds() - query_time_sec)
            if delta_time <= min_time_interval_sec:
                min_time_interval_sec = delta_time
                best_matching_data = data
                best_matching_index = index
        return best_matching_index, best_matching_data

    def find_hand_pose_interpolate(self, query_time_sec, viz_queue):
        if len(viz_queue) == 0:
            return None, None

        data_before = None
        data_after = None
        time_to_before_sec = 1.0
        time_to_after_sec = 1.0

        index_before = -1
        index_after = -1

        for reverse_index, data in enumerate(reversed(viz_queue)):
            index = len(viz_queue) - 1 - reverse_index
            if data is None:
                continue
            data_time = data.tracking_timestamp.total_seconds()

            if data_time > query_time_sec:
                data_after = data
                index_after = index
                time_to_after_sec = data_time - query_time_sec
            elif data_time <= query_time_sec and data_before is None:
                time_to_before_sec = query_time_sec - data_time
                data_before = data
                index_before = index
                break

        if data_before is not None and data_after is not None:
            query_time_us = int(query_time_sec * 1e6)
            interpolated_hand_pose = interpolate_hand_tracking_result(
                data_before, data_after, query_time_us
            )
            if interpolated_hand_pose is not None:
                return index_before, interpolated_hand_pose

        # cannot find hand pose, use the closest and <= 100ms
        if (
            (time_to_before_sec <= time_to_after_sec)
            and time_to_before_sec
            <= DEFAULT_HAND_POSE_INTERPOLATION_PERIOD_MS / 2.0 * 1e-3
        ):
            return index_before, data_before

        if (
            (time_to_after_sec < time_to_before_sec)
            and time_to_after_sec
            <= DEFAULT_HAND_POSE_INTERPOLATION_PERIOD_MS / 2.0 * 1e-3
        ):
            return index_after, data_after

        return None, None

    def image_callback(self, image_data: ImageData, image_record: ImageDataRecord):
        """RGB/SLAM/ET camera callback."""
        if self.aria_data_viewer is not None:
            camera_label = self._get_gen2_camera_label_from_camera_id(
                image_record.camera_id
            )

            # plot images
            img_array = np.array(image_data.to_numpy_array())
            self.aria_data_viewer.plot_image(
                img_array, camera_label, image_record.capture_timestamp_ns
            )

            if camera_label is None:
                warn_once(
                    self.image_callback,
                    f"invalid camera id:{image_record.camera_id}! Skipped.",
                )
                return

            if (
                camera_label == "camera-rgb"
                or camera_label == "slam-front-right"
                or camera_label == "slam-front-left"
            ):
                # plot hand pose with or without interpolation
                if self.interpolate:
                    hand_pose_index, hand_pose = self.find_hand_pose_interpolate(
                        image_record.capture_timestamp_ns * 1e-9,
                        self.hand_pose_viz_queue,
                    )
                else:
                    hand_pose_index, hand_pose = self.find_data_closest(
                        image_record.capture_timestamp_ns * 1e-9,
                        self.hand_pose_viz_queue,
                    )
                if hand_pose is not None:
                    self.hand_pose_viz_matching_index[camera_label] = hand_pose_index
                else:
                    # when no hand_pose data, provide a dummy hand pose to clear the canvas
                    hand_pose = hand_tracking.HandTrackingResult()
                    hand_pose.tracking_timestamp = timedelta(
                        microseconds=image_record.capture_timestamp_ns * 1e-3
                    )
                self.aria_data_viewer.plot_hand_pose_data_2d(hand_pose, camera_label)
                # plot eye gaze with closest
                eye_gaze_index, eye_gaze_data = self.find_data_closest(
                    image_record.capture_timestamp_ns * 1e-9, self.eye_gaze_viz_queue
                )
                if eye_gaze_data is not None:
                    self.eye_gaze_matching_index[camera_label] = eye_gaze_index
                    self.aria_data_viewer.plot_eye_gaze_data(eye_gaze_data)

            # remove data queue when not needed
            if (
                len(self.hand_pose_viz_queue) > 1000
                and len(self.hand_pose_viz_matching_index) == 3
            ):
                min_index = min(self.hand_pose_viz_matching_index.values())
                del self.hand_pose_viz_queue[:min_index]
                self.hand_pose_viz_matching_index = {}
            if (
                len(self.eye_gaze_viz_queue) > 1000
                and len(self.eye_gaze_matching_index) >= 3
            ):
                min_index = min(self.eye_gaze_matching_index.values())
                del self.eye_gaze_viz_queue[:min_index]
                self.eye_gaze_matching_index = {}

    def imu_callback(self, imu_data, sensor_label):
        """IMU sensor callback."""
        if self.aria_data_viewer is not None:
            self.aria_data_viewer.plot_imu(imu_data, sensor_label)

    def imu_batch_callback(self, imu_data_batch, sensor_label):
        """IMU batch sensor callback."""
        if self.aria_data_viewer is not None:
            self.aria_data_viewer.plot_imu_batch_vectorized(
                imu_data_batch, sensor_label
            )

    def magnetometer_callback(self, mag_data, sensor_label):
        """Magnetometer sensor callback."""
        if self.aria_data_viewer is not None:
            self.aria_data_viewer.plot_magnetometer(mag_data)

    def barometer_callback(self, baro_data):
        """Barometer sensor callback."""
        if self.aria_data_viewer is not None:
            self.aria_data_viewer.plot_barometer(baro_data)

    def audio_callback(self, audio_data, audio_record, num_audio_channels):
        """Audio sensor callback."""
        if self.aria_data_viewer is not None:
            # No need to set a timestamp for audio data, which contains a batch of audio samples.
            # Each audio sample contains its own timestamp.
            # The timestamp assignment will be handled within the plot_audio method.
            self.aria_data_viewer.plot_audio(
                [audio_data, audio_record], num_audio_channels
            )

    def eye_gaze_callback(self, eye_gaze_data):
        """Eye gaze callback."""
        if self.aria_data_viewer is not None:
            self.eye_gaze_viz_queue.append(eye_gaze_data)

    def hand_pose_callback(self, hand_pose_data):
        """Hand pose callback."""
        if self.aria_data_viewer is not None:
            self.aria_data_viewer.plot_hand_pose_data_3d(hand_pose_data)
            self.hand_pose_viz_queue.append(hand_pose_data)

    def vio_high_frequency_callback(self, vio_high_frequency_data):
        """VIO high frequency callback."""
        self.vio_high_frequency_data_count += 1
        if (
            self.vio_high_frequency_data_count
            % self.viewer_config.vio_high_freq_subsample_rate
            != 0
        ):
            return
        if self.aria_data_viewer is not None:
            self.aria_data_viewer.plot_vio_high_freq_data(vio_high_frequency_data)

    def vio_callback(self, vio_data):
        """VIO callback."""
        if self.aria_data_viewer is not None:
            self.aria_data_viewer.plot_vio_data(vio_data)

    def gps_callback(self, gps_data):
        """GPS sensor callback. gps_provider should either be APP or GPS"""
        if self.aria_data_viewer is not None:
            self.aria_data_viewer.plot_gps(gps_data)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--real-time",
        default=False,
        action="store_true",
        help="Enable real-time streaming. If not enabled, the streaming visualization might be lagging",
    )
    parser.add_argument(
        "--interpolate",
        default=False,
        action="store_true",
        help="Interpolate data (hand pose) for visualization. (DEFAULT use the closest data)",
    )
    parser.add_argument(
        "--jpeg-quality",
        default=50,
        help="Set jpeg quality for image visualization (DEFAULT 50)",
    )
    return parser.parse_args()


def main():
    """Main function to start the Aria streaming viewer server."""
    args = parse_args()
    # Local list to keep references to AriaStreamManager instances to prevent garbage collection
    stream_managers = []
    config = sdk_gen2.HttpServerConfig()
    config.address = "0.0.0.0"
    config.port = 6768
    stream_managers = []
    stream_manager = AriaStreamManager(
        args.real_time, args.interpolate, args.jpeg_quality
    )
    stream_managers.append(stream_manager)

    stream_receiver = stream_manager.get_stream_receiver()
    stream_receiver.set_server_config(config)
    stream_receiver.start_server()

    def signal_handler(sig, frame):
        print("CTRL+C pressed, shutting down server")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    while True:
        signal.pause()


if __name__ == "__main__":
    main()
