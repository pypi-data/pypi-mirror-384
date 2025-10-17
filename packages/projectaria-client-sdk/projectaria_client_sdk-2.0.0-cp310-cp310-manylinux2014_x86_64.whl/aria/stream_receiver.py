# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

from aria.sdk_gen2 import (
    AriaGen2HandlerFactory,
    AriaGen2HttpServer,
    HttpServerConfig,
    StreamDataInterface,
)

from projectaria_tools.core.sensor_data import ImageData, ImageDataRecord
from projectaria_tools.core.xprs import (
    createDecoder,
    VideoCodec,
    VideoCodecFormat,
    XprsResult,
)


# Global set to track functions that have already warned
_warned_functions = set()

# Image default queue size
DEFAULT_RGB_QUEUE_SIZ = 100
DEFAULT_SLAM_QUEUE_SIZE = 1000
DEFAULT_ET_QUEUE_SIZE = 100

# IMU default queue size
DEFAULT_IMU_QUEUE_SIZE = 800
DEFAULT_IMU_BATCH_QUEUE_SIZE = 10

# Machine perception default queue size
DEFAULT_VIO_QUEUE_SIZE = 10
DEFAULT_VIO_HIGH_FREQ_QUEUE_SIZE = 800
DEFAULT_VIO_HIGH_FREQ_BATCH_QUEUE_SIZE = 10
DEFAULT_EYE_GAZE_QUEUE_SIZE = 10
DEFAULT_HAND_POSE_QUEUE_SIZE = 10


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
        print(f"[stream_receiver][WARNING]: {message}")
        _warned_functions.add(func_id)


class StreamReceiver:
    def __init__(self, enable_image_decoding=True, enable_raw_stream=False):
        self.enable_image_decoding = enable_image_decoding
        self._enable_python_decoding = enable_image_decoding
        self.enable_raw_stream = enable_raw_stream
        self.server_config = HttpServerConfig()
        self.vrs_path = ""

        try:
            import aria.internal_only as internal_only

            if enable_image_decoding and internal_only.is_internal_only():
                self._enable_python_decoding = False
                print("Using internal c++ image decoder.")
        except ImportError:
            self.enable_image_decoding = False
            print(f"Using python image decoder: {self._enable_python_decoding}")

        # initialize empty callbacks
        self._init_callback()

        # initialize queue sizes
        self._init_queue_size()

        # initialize camera id to label mapping
        self._gen2_camera_id_to_label = {
            1: "slam-front-left",
            2: "slam-front-right",
            4: "slam-side-left",
            8: "slam-side-right",
            16: "camera-et-left",
            32: "camera-et-right",
            64: "camera-rgb",
        }

        # create XPRS decoder
        self.image_decoders = {}
        # NOTE: opensourced XPRS decoder does not support HW acceleration yet
        self.hw_accel = False

    def _init_callback(self):
        self.rgb_callback = None
        self.slam_callback = None
        self.et_callback = None
        self.calib_callback = None
        self.device_calib_callback = None
        self.raw_message_callback = None
        self.imu_callback = None
        self.imu_batch_callback = None
        self.barometer_callback = None
        self.magnetometer_callback = None
        self.gps_callback = None
        self.hand_pose_callback = None
        self.eye_gaze_callback = None
        self.audio_callback = None
        self.vio_callback = None
        self.vio_high_frequency_callback = None

    def _init_queue_size(self):
        self.rgb_queue_size = DEFAULT_RGB_QUEUE_SIZ
        self.slam_queue_size = DEFAULT_SLAM_QUEUE_SIZE
        self.et_queue_size = DEFAULT_ET_QUEUE_SIZE

        self.imu_queue_size = DEFAULT_IMU_QUEUE_SIZE
        self.imu_batch_queue_size = DEFAULT_IMU_BATCH_QUEUE_SIZE

        self.vio_queue_size = DEFAULT_VIO_QUEUE_SIZE
        self.vio_high_freq_queue_size = DEFAULT_VIO_HIGH_FREQ_QUEUE_SIZE
        self.vio_high_freq_batch_queue_size = DEFAULT_VIO_HIGH_FREQ_BATCH_QUEUE_SIZE
        self.eye_gaze_queue_size = DEFAULT_EYE_GAZE_QUEUE_SIZE
        self.hand_pose_queue_size = DEFAULT_HAND_POSE_QUEUE_SIZE

    def set_rgb_queue_size(self, queue_size):
        self.rgb_queue_size = queue_size

    def set_slam_queue_size(self, queue_size):
        self.slam_queue_size = queue_size

    def set_imu_queue_size(self, queue_size):
        self.imu_queue_size = queue_size

    def set_imu_batch_queue_size(self, queue_size):
        self.imu_batch_queue_size = queue_size

    def set_et_queue_size(self, queue_size):
        self.et_queue_size = queue_size

    def set_vio_queue_size(self, queue_size):
        self.vio_queue_size = queue_size

    def set_vio_high_freq_queue_size(self, queue_size):
        self.vio_high_freq_queue_size = queue_size

    def set_vio_high_freq_batch_queue_size(self, queue_size):
        self.vio_high_freq_batch_queue_size = queue_size

    def set_eye_gaze_queue_size(self, queue_size):
        self.eye_gaze_queue_size = queue_size

    def set_hand_pose_queue_size(self, queue_size):
        self.hand_pose_queue_size = queue_size

    def get_rgb_queue_size(self):
        return self.rgb_queue_size

    def get_slam_queue_size(self):
        return self.slam_queue_size

    def get_imu_queue_size(self):
        return self.imu_queue_size

    def get_imu_batch_queue_size(self):
        return self.imu_batch_queue_size

    def get_et_queue_size(self):
        return self.et_queue_size

    def get_vio_queue_size(self):
        return self.vio_queue_size

    def get_vio_high_freq_queue_size(self):
        return self.vio_high_freq_queue_size

    def get_vio_high_freq_batch_queue_size(self):
        return self.vio_high_freq_batch_queue_size

    def get_eye_gaze_queue_size(self):
        return self.eye_gaze_queue_size

    def get_hand_pose_queue_size(self):
        return self.hand_pose_queue_size

    def record_to_vrs(self, vrs_path):
        self.vrs_path = vrs_path

    def register_rgb_callback(self, callback):
        self.rgb_callback = callback

    def register_slam_callback(self, callback):
        self.slam_callback = callback

    def register_et_callback(self, callback):
        self.et_callback = callback

    def register_calib_callback(self, callback):
        self.calib_callback = callback

    def register_device_calib_callback(self, callback):
        self.device_calib_callback = callback

    def register_raw_message_callback(self, callback):
        self.raw_message_callback = callback

    def register_imu_callback(self, callback):
        self.imu_callback = callback

    def register_imu_batch_callback(self, callback):
        self.imu_batch_callback = callback

    def register_barometer_callback(self, callback):
        self.barometer_callback = callback

    def register_magnetometer_callback(self, callback):
        self.magnetometer_callback = callback

    def register_gps_callback(self, callback):
        self.gps_callback = callback

    def register_hand_pose_callback(self, callback):
        self.hand_pose_callback = callback

    def register_eye_gaze_callback(self, callback):
        self.eye_gaze_callback = callback

    def register_audio_callback(self, callback):
        self.audio_callback = callback

    def register_vio_callback(self, callback):
        self.vio_callback = callback

    def register_vio_high_frequency_callback(self, callback):
        self.vio_high_frequency_callback = callback

    def set_server_config(self, server_config):
        self.server_config = server_config

    def start_server(self):
        self.factory = AriaGen2HandlerFactory.create_factory_handler(
            self._setup_stream_handler
        )
        self.server = AriaGen2HttpServer(self.server_config, self.factory)
        return self.server

    def _get_camera_name(self, camera_id):
        if self._gen2_camera_id_to_label.get(camera_id) is None:
            print("Warning: Camera id not found")
            return ""
        return self._gen2_camera_id_to_label.get(camera_id)

    def _is_slam(self, camera_id):
        if self._get_camera_name(camera_id).startswith("slam"):
            return True

    def _is_rgb(self, camera_id):
        if self._get_camera_name(camera_id) == "camera-rgb":
            return True

    # decode rgb image callback
    def _decode_rgb_callback(
        self, image_data: ImageData, image_record: ImageDataRecord
    ):
        decode_success = self._decode_image_impl(image_data, image_record)
        if not decode_success:
            print(
                f"Warning: Failed to decode rgb image data from camera {self._get_camera_name(image_record.camera_id)}"
            )

        self.rgb_callback(image_data, image_record)

    # decode slam image callback
    def _decode_slam_callback(
        self, image_data: ImageData, image_record: ImageDataRecord
    ):
        decode_success = self._decode_image_impl(image_data, image_record)
        if not decode_success:
            print(
                f"Warning: Failed to decode slam image data from camera {self._get_camera_name(image_record.camera_id)}"
            )

        self.slam_callback(image_data, image_record)

    # decode et image callback
    def _decode_et_callback(self, image_data: ImageData, image_record: ImageDataRecord):
        decode_success = self._decode_image_impl(image_data, image_record)
        if not decode_success:
            print(
                f"Warning: Failed to decode et image data from camera {self._get_camera_name(image_record.camera_id)}"
            )

        self.et_callback(image_data, image_record)

    def _decode_image_impl(self, image_data: ImageData, image_record: ImageDataRecord):
        camera_id = image_record.camera_id
        if self._get_camera_name(camera_id) == "":
            print(
                f"Error: Camera id not found. Unable to create decoder for camera id {camera_id}"
            )
            return False

        if camera_id not in self.image_decoders:
            codec = VideoCodec()
            codec.format = VideoCodecFormat.H265
            codec.hw_accel = self.hw_accel
            codec.implementation_name = "hevc"

            self.image_decoders[camera_id] = createDecoder(codec)
            xprsResult = self.image_decoders[camera_id].init(codec.hw_accel)
            if xprsResult != XprsResult.OK:
                print(
                    f"Failed to init decoder for camera: {self._get_camera_name(camera_id)} with error: {xprsResult}"
                )
        return self.image_decoders[camera_id].decode_oss_frame(image_data)

    def _setup_stream_handler(self):
        # NOTE: only enable external python decoding right now
        stream_handler = StreamDataInterface(
            self.enable_image_decoding, self.enable_raw_stream
        )

        if self.vrs_path != "":
            print(f"Recording to vrs: {self.vrs_path}")
            stream_handler.record_to_vrs(self.vrs_path)

        if self.enable_raw_stream:
            stream_handler.register_raw_message_callback(self.raw_message_callback)
            return stream_handler  # return early to avoid registering other callbacks

        if self.rgb_callback is not None:
            if self._enable_python_decoding:
                print("Registering RGB callback with image decoding")
                stream_handler.register_rgb_callback(self._decode_rgb_callback)
            else:
                stream_handler.register_rgb_callback(self.rgb_callback)

        if self.slam_callback is not None:
            if self._enable_python_decoding:
                print("Registering SLAM callback with image decoding")
                stream_handler.register_slam_callback(self._decode_slam_callback)
            else:
                stream_handler.register_slam_callback(self.slam_callback)

        if self.et_callback is not None:
            if self._enable_python_decoding:
                print("Registering ET callback with image decoding")
                stream_handler.register_et_callback(self._decode_et_callback)
            else:
                stream_handler.register_et_callback(self.et_callback)

        if self.calib_callback is not None:
            stream_handler.register_calib_callback(self.calib_callback)

        if self.imu_callback is not None:
            stream_handler.register_imu_callback(self.imu_callback)

        if self.imu_batch_callback is not None:
            stream_handler.register_imu_batch_callback(self.imu_batch_callback)

        if self.barometer_callback is not None:
            stream_handler.register_barometer_callback(self.barometer_callback)

        if self.magnetometer_callback is not None:
            stream_handler.register_magnetometer_callback(self.magnetometer_callback)

        if self.gps_callback is not None:
            stream_handler.register_gps_callback(self.gps_callback)

        if self.hand_pose_callback is not None:
            stream_handler.register_hand_pose_callback(self.hand_pose_callback)

        if self.eye_gaze_callback is not None:
            stream_handler.register_eye_gaze_callback(self.eye_gaze_callback)

        if self.audio_callback is not None:
            stream_handler.register_audio_callback(self.audio_callback)

        if self.vio_high_frequency_callback is not None:
            stream_handler.register_vio_high_frequency_callback(
                self.vio_high_frequency_callback
            )

        if self.vio_callback is not None:
            stream_handler.register_vio_callback(self.vio_callback)

        if self.device_calib_callback is not None:
            stream_handler.register_device_calib_callback(self.device_calib_callback)

        stream_handler.set_rgb_queue_size(self.rgb_queue_size)
        stream_handler.set_slam_queue_size(self.slam_queue_size)
        stream_handler.set_et_queue_size(self.et_queue_size)
        stream_handler.set_imu_queue_size(self.imu_queue_size)
        stream_handler.set_imu_batch_queue_size(self.imu_batch_queue_size)
        stream_handler.set_vio_queue_size(self.vio_queue_size)
        stream_handler.set_vio_high_freq_queue_size(self.vio_high_freq_queue_size)
        stream_handler.set_vio_high_freq_batch_queue_size(
            self.vio_high_freq_batch_queue_size
        )
        stream_handler.set_eye_gaze_queue_size(self.eye_gaze_queue_size)
        stream_handler.set_hand_pose_queue_size(self.hand_pose_queue_size)

        return stream_handler
