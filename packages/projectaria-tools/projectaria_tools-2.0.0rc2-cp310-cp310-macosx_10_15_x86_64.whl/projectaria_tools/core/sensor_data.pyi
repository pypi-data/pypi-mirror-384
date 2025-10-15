from __future__ import annotations
import projectaria_tools.core.stream_id
import collections.abc
import numpy
import numpy.typing
import typing
__all__ = ['AFTER', 'ALS', 'AUDIO', 'AlsConfiguration', 'AlsData', 'AudioConfig', 'AudioData', 'AudioDataRecord', 'BAD', 'BAROMETER', 'BEFORE', 'BLUETOOTH', 'BarometerConfigRecord', 'BarometerData', 'BluetoothBeaconConfigRecord', 'BluetoothBeaconData', 'CLOSEST', 'DEVICE_TIME', 'EYE_GAZE', 'EyeGazeConfiguration', 'FILTER_NOT_INITIALIZED', 'FrontendOutput', 'GOOD', 'GPS', 'GpsConfigRecord', 'GpsData', 'HAND_POSE', 'HOST_TIME', 'HandPoseConfiguration', 'IMAGE', 'IMU', 'INVALID', 'ImageConfigRecord', 'ImageData', 'ImageDataRecord', 'ImuMeasurementModelParametersFloat', 'MAGNETOMETER', 'MotionConfigRecord', 'MotionData', 'NOT_VALID', 'OnlineCalibState', 'PPG', 'PixelFrame', 'PpgConfiguration', 'PpgData', 'ProjectionModelParametersFloat', 'RECORD_TIME', 'SUBGHZ', 'SensorConfiguration', 'SensorData', 'SensorDataType', 'TIC_SYNC', 'TIME_CODE', 'TemperatureConfiguration', 'TemperatureData', 'TimeDomain', 'TimeQueryOptions', 'TimeSyncMode', 'TrackingQuality', 'UNKNOWN', 'UNRECOVERABLE', 'UTC', 'VALID', 'VIO', 'VIO_HIGH_FREQ', 'VioConfiguration', 'VioHighFreqConfiguration', 'VioStatus', 'VisualTrackingQuality', 'WPS', 'WifiBeaconConfigRecord', 'WifiBeaconData', 'get_sensor_data_type_name', 'get_time_domain_name', 'has_calibration', 'supports_host_time_domain']
class AlsConfiguration:
    """
    ALS sensor configuration type
    """
    sensor_model: str
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def device_id(self) -> int:
        ...
    @device_id.setter
    def device_id(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def nominal_rate_hz(self) -> float:
        ...
    @nominal_rate_hz.setter
    def nominal_rate_hz(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def stream_id(self) -> int:
        ...
    @stream_id.setter
    def stream_id(self, arg0: typing.SupportsInt) -> None:
        ...
class AlsData:
    """
    ALS data type
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def blue_channel_normalized(self) -> float:
        ...
    @blue_channel_normalized.setter
    def blue_channel_normalized(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def capture_timestamp_ns(self) -> int:
        ...
    @capture_timestamp_ns.setter
    def capture_timestamp_ns(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def cct(self) -> float:
        ...
    @cct.setter
    def cct(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def clear_channel_normalized(self) -> float:
        ...
    @clear_channel_normalized.setter
    def clear_channel_normalized(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def clear_flux_watt_per_square_meter(self) -> float:
        ...
    @clear_flux_watt_per_square_meter.setter
    def clear_flux_watt_per_square_meter(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def exposure_time_us(self) -> int:
        ...
    @exposure_time_us.setter
    def exposure_time_us(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def gain_blue(self) -> int:
        ...
    @gain_blue.setter
    def gain_blue(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def gain_clear(self) -> int:
        ...
    @gain_clear.setter
    def gain_clear(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def gain_green(self) -> int:
        ...
    @gain_green.setter
    def gain_green(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def gain_ir(self) -> int:
        ...
    @gain_ir.setter
    def gain_ir(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def gain_red(self) -> int:
        ...
    @gain_red.setter
    def gain_red(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def gain_uv(self) -> int:
        ...
    @gain_uv.setter
    def gain_uv(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def green_channel_normalized(self) -> float:
        ...
    @green_channel_normalized.setter
    def green_channel_normalized(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def ir_channel_normalized(self) -> float:
        ...
    @ir_channel_normalized.setter
    def ir_channel_normalized(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def ir_flux_watt_per_square_meter(self) -> float:
        ...
    @ir_flux_watt_per_square_meter.setter
    def ir_flux_watt_per_square_meter(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def lux(self) -> float:
        ...
    @lux.setter
    def lux(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def red_channel_normalized(self) -> float:
        ...
    @red_channel_normalized.setter
    def red_channel_normalized(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def uv_channel_normalized(self) -> float:
        ...
    @uv_channel_normalized.setter
    def uv_channel_normalized(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def uv_flux_watt_per_square_meter(self) -> float:
        ...
    @uv_flux_watt_per_square_meter.setter
    def uv_flux_watt_per_square_meter(self, arg0: typing.SupportsFloat) -> None:
        ...
class AudioConfig:
    """
    Audio sensor configuration type
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def num_channels(self) -> int:
        ...
    @num_channels.setter
    def num_channels(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def sample_format(self) -> int:
        ...
    @sample_format.setter
    def sample_format(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def sample_rate(self) -> int:
        ...
    @sample_rate.setter
    def sample_rate(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def stream_id(self) -> int:
        ...
    @stream_id.setter
    def stream_id(self, arg0: typing.SupportsInt) -> None:
        ...
class AudioData:
    """
    Audio sensor data type: the audio value
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def data(self) -> list[int]:
        ...
    @data.setter
    def data(self, arg0: collections.abc.Sequence[typing.SupportsInt]) -> None:
        ...
    @property
    def max_amplitude(self) -> float:
        ...
    @max_amplitude.setter
    def max_amplitude(self, arg0: typing.SupportsFloat) -> None:
        ...
class AudioDataRecord:
    """
    Audio meta data
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def audio_muted(self) -> int:
        ...
    @audio_muted.setter
    def audio_muted(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def capture_timestamps_ns(self) -> list[int]:
        ...
    @capture_timestamps_ns.setter
    def capture_timestamps_ns(self, arg0: collections.abc.Sequence[typing.SupportsInt]) -> None:
        ...
class BarometerConfigRecord:
    """
    Barometer sensor configuration type
    """
    sensor_model_name: str
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def sample_rate(self) -> float:
        ...
    @sample_rate.setter
    def sample_rate(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def stream_id(self) -> int:
        ...
    @stream_id.setter
    def stream_id(self, arg0: typing.SupportsInt) -> None:
        ...
class BarometerData:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def capture_timestamp_ns(self) -> int:
        ...
    @capture_timestamp_ns.setter
    def capture_timestamp_ns(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def pressure(self) -> float:
        ...
    @pressure.setter
    def pressure(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def temperature(self) -> float:
        ...
    @temperature.setter
    def temperature(self, arg0: typing.SupportsFloat) -> None:
        ...
class BluetoothBeaconConfigRecord:
    """
    Bluetooth sensor configuration type
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def sample_rate_hz(self) -> float:
        ...
    @sample_rate_hz.setter
    def sample_rate_hz(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def streamId(self) -> int:
        ...
    @streamId.setter
    def streamId(self, arg0: typing.SupportsInt) -> None:
        ...
class BluetoothBeaconData:
    unique_id: str
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def board_scan_request_complete_timestamp_ns(self) -> int:
        ...
    @board_scan_request_complete_timestamp_ns.setter
    def board_scan_request_complete_timestamp_ns(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def board_scan_request_start_timestamp_ns(self) -> int:
        ...
    @board_scan_request_start_timestamp_ns.setter
    def board_scan_request_start_timestamp_ns(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def board_timestamp_ns(self) -> int:
        ...
    @board_timestamp_ns.setter
    def board_timestamp_ns(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def freq_mhz(self) -> float:
        ...
    @freq_mhz.setter
    def freq_mhz(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def rssi(self) -> float:
        ...
    @rssi.setter
    def rssi(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def system_timestamp_ns(self) -> int:
        ...
    @system_timestamp_ns.setter
    def system_timestamp_ns(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def tx_power(self) -> float:
        ...
    @tx_power.setter
    def tx_power(self, arg0: typing.SupportsFloat) -> None:
        ...
class EyeGazeConfiguration:
    """
    Eye gaze sensor configuration type
    """
    user_calibrated: bool
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def nominal_rate_hz(self) -> float:
        ...
    @nominal_rate_hz.setter
    def nominal_rate_hz(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def stream_id(self) -> int:
        ...
    @stream_id.setter
    def stream_id(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def user_calibration_error(self) -> float:
        ...
    @user_calibration_error.setter
    def user_calibration_error(self, arg0: typing.SupportsFloat) -> None:
        ...
class FrontendOutput:
    """
    
            FrontendOutput class holds the output data from the on-device VIO stream.
            It includes session identifiers, timestamps, status, and various pose and velocity data.
        
    """
    frontend_session_uid: str
    online_calib: OnlineCalibState
    pose_quality: TrackingQuality
    status: VioStatus
    transform_bodyimu_device: SE3f
    transform_odometry_bodyimu: SE3f
    visual_tracking_quality: VisualTrackingQuality
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def angular_velocity_in_bodyimu(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float32], "[3, 1]"]:
        ...
    @angular_velocity_in_bodyimu.setter
    def angular_velocity_in_bodyimu(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float32, "[3, 1]"]) -> None:
        ...
    @property
    def camera_serials(self) -> list[str]:
        ...
    @camera_serials.setter
    def camera_serials(self, arg0: collections.abc.Sequence[str]) -> None:
        ...
    @property
    def capture_timestamp_ns(self) -> int:
        ...
    @capture_timestamp_ns.setter
    def capture_timestamp_ns(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def frame_id(self) -> int:
        ...
    @frame_id.setter
    def frame_id(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def gravity_in_odometry(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float32], "[3, 1]"]:
        ...
    @gravity_in_odometry.setter
    def gravity_in_odometry(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float32, "[3, 1]"]) -> None:
        ...
    @property
    def linear_velocity_in_odometry(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float32], "[3, 1]"]:
        ...
    @linear_velocity_in_odometry.setter
    def linear_velocity_in_odometry(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float32, "[3, 1]"]) -> None:
        ...
    @property
    def unix_timestamp_ns(self) -> int:
        ...
    @unix_timestamp_ns.setter
    def unix_timestamp_ns(self, arg0: typing.SupportsInt) -> None:
        ...
class GpsConfigRecord:
    """
    Gps sensor configuration type
    """
    provider: str
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def sample_rate_hz(self) -> float:
        ...
    @sample_rate_hz.setter
    def sample_rate_hz(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def stream_id(self) -> int:
        ...
    @stream_id.setter
    def stream_id(self, arg0: typing.SupportsInt) -> None:
        ...
class GpsData:
    """
    Gps data type, note that GPS sensor data are already rectified
    """
    navigation_messages: str
    provider: str
    raw_measurements: str
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def accuracy(self) -> float:
        ...
    @accuracy.setter
    def accuracy(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def altitude(self) -> float:
        ...
    @altitude.setter
    def altitude(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def capture_timestamp_ns(self) -> int:
        ...
    @capture_timestamp_ns.setter
    def capture_timestamp_ns(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def constellations_enabled(self) -> list[str]:
        ...
    @constellations_enabled.setter
    def constellations_enabled(self, arg0: collections.abc.Sequence[str]) -> None:
        ...
    @property
    def latitude(self) -> float:
        ...
    @latitude.setter
    def latitude(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def longitude(self) -> float:
        ...
    @longitude.setter
    def longitude(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def raw_data(self) -> list[str]:
        ...
    @raw_data.setter
    def raw_data(self, arg0: collections.abc.Sequence[str]) -> None:
        ...
    @property
    def speed(self) -> float:
        ...
    @speed.setter
    def speed(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def utc_time_ms(self) -> int:
        ...
    @utc_time_ms.setter
    def utc_time_ms(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def verticalAccuracy(self) -> float:
        ...
    @verticalAccuracy.setter
    def verticalAccuracy(self, arg0: typing.SupportsFloat) -> None:
        ...
class HandPoseConfiguration:
    """
    Hand pose sensor configuration type
    """
    is_wrist_palm_only: bool
    user_profile: str
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def nominal_rate_hz(self) -> float:
        ...
    @nominal_rate_hz.setter
    def nominal_rate_hz(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def stream_id(self) -> int:
        ...
    @stream_id.setter
    def stream_id(self, arg0: typing.SupportsInt) -> None:
        ...
class ImageConfigRecord:
    description: str
    device_serial: str
    device_type: str
    device_version: str
    factory_calibration: str
    online_calibration: str
    sensor_model: str
    sensor_serial: str
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def camera_id(self) -> int:
        ...
    @camera_id.setter
    def camera_id(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def exposure_duration_max(self) -> float:
        ...
    @exposure_duration_max.setter
    def exposure_duration_max(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def exposure_duration_min(self) -> float:
        ...
    @exposure_duration_min.setter
    def exposure_duration_min(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def gain_max(self) -> float:
        ...
    @gain_max.setter
    def gain_max(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def gain_min(self) -> float:
        ...
    @gain_min.setter
    def gain_min(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def gamma_factor(self) -> float:
        ...
    @gamma_factor.setter
    def gamma_factor(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def image_height(self) -> int:
        ...
    @image_height.setter
    def image_height(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def image_stride(self) -> int:
        ...
    @image_stride.setter
    def image_stride(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def image_width(self) -> int:
        ...
    @image_width.setter
    def image_width(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def nominal_rate_hz(self) -> float:
        ...
    @nominal_rate_hz.setter
    def nominal_rate_hz(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def pixel_format(self) -> int:
        ...
    @pixel_format.setter
    def pixel_format(self, arg0: typing.SupportsInt) -> None:
        ...
class ImageData:
    pixel_frame: PixelFrame
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    def at(self, x: typing.SupportsInt, y: typing.SupportsInt, channel: typing.SupportsInt = ...) -> float | int | int | int | ...:
        """
        Returns pixel value at (x, y, channel)
        """
    def get_height(self) -> int:
        """
        Returns number of rows in image
        """
    def get_pixel_format(self) -> int:
        """
        Returns the format of the pixel
        """
    def get_width(self) -> int:
        """
        Returns number of columns in image
        """
    def is_valid(self) -> bool:
        """
        Returns if image is empty
        """
    def to_numpy_array(self) -> numpy.typing.NDArray[numpy.float32] | numpy.typing.NDArray[numpy.uint8] | numpy.typing.NDArray[numpy.uint16] | numpy.typing.NDArray[numpy.uint64] | numpy.typing.NDArray[...]:
        """
        Converts to numpy array
        """
class ImageDataRecord:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def arrival_timestamp_ns(self) -> int:
        ...
    @arrival_timestamp_ns.setter
    def arrival_timestamp_ns(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def camera_id(self) -> int:
        ...
    @camera_id.setter
    def camera_id(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def capture_timestamp_ns(self) -> int:
        ...
    @capture_timestamp_ns.setter
    def capture_timestamp_ns(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def exposure_duration(self) -> float:
        ...
    @exposure_duration.setter
    def exposure_duration(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def frame_number(self) -> int:
        ...
    @frame_number.setter
    def frame_number(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def gain(self) -> float:
        ...
    @gain.setter
    def gain(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def group_id(self) -> int:
        ...
    @group_id.setter
    def group_id(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def group_mask(self) -> int:
        ...
    @group_mask.setter
    def group_mask(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def temperature(self) -> float:
        ...
    @temperature.setter
    def temperature(self, arg0: typing.SupportsFloat) -> None:
        ...
class ImuMeasurementModelParametersFloat:
    t_imu_body_imu: SE3f
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    def reset(self) -> None:
        """
        Reset to default values.
        """
    @property
    def accel_bias_m_sec2(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float32], "[3, 1]"]:
        ...
    @accel_bias_m_sec2.setter
    def accel_bias_m_sec2(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float32, "[3, 1]"]) -> None:
        ...
    @property
    def accel_nonorth(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float32], "[3, 3]"]:
        ...
    @accel_nonorth.setter
    def accel_nonorth(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float32, "[3, 3]"]) -> None:
        ...
    @property
    def accel_saturation_threshold_m_sec2(self) -> float:
        ...
    @accel_saturation_threshold_m_sec2.setter
    def accel_saturation_threshold_m_sec2(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def accel_scale_vec(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float32], "[3, 1]"]:
        ...
    @accel_scale_vec.setter
    def accel_scale_vec(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float32, "[3, 1]"]) -> None:
        ...
    @property
    def dt_reference_accel_sec(self) -> float:
        ...
    @dt_reference_accel_sec.setter
    def dt_reference_accel_sec(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def dt_reference_gyro_sec(self) -> float:
        ...
    @dt_reference_gyro_sec.setter
    def dt_reference_gyro_sec(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def gyro_bias_rad_sec(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float32], "[3, 1]"]:
        ...
    @gyro_bias_rad_sec.setter
    def gyro_bias_rad_sec(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float32, "[3, 1]"]) -> None:
        ...
    @property
    def gyro_g_sensitivity_rad_sec_per_m_sec2(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float32], "[3, 3]"]:
        ...
    @gyro_g_sensitivity_rad_sec_per_m_sec2.setter
    def gyro_g_sensitivity_rad_sec_per_m_sec2(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float32, "[3, 3]"]) -> None:
        ...
    @property
    def gyro_nonorth(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float32], "[3, 3]"]:
        ...
    @gyro_nonorth.setter
    def gyro_nonorth(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float32, "[3, 3]"]) -> None:
        ...
    @property
    def gyro_saturation_threshold_rad_sec(self) -> float:
        ...
    @gyro_saturation_threshold_rad_sec.setter
    def gyro_saturation_threshold_rad_sec(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def gyro_scale_vec(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float32], "[3, 1]"]:
        ...
    @gyro_scale_vec.setter
    def gyro_scale_vec(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float32, "[3, 1]"]) -> None:
        ...
    @property
    def nominal_sampling_period_sec(self) -> float:
        ...
    @nominal_sampling_period_sec.setter
    def nominal_sampling_period_sec(self, arg0: typing.SupportsFloat) -> None:
        ...
class MotionConfigRecord:
    description: str
    device_serial: str
    device_type: str
    factory_calibration: str
    has_accelerometer: bool
    has_gyroscope: bool
    has_magnetometer: bool
    online_calibration: str
    sensor_model: str
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def device_id(self) -> int:
        ...
    @device_id.setter
    def device_id(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def nominal_rate_hz(self) -> float:
        ...
    @nominal_rate_hz.setter
    def nominal_rate_hz(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def stream_index(self) -> int:
        ...
    @stream_index.setter
    def stream_index(self, arg0: typing.SupportsInt) -> None:
        ...
class MotionData:
    accel_valid: bool
    gyro_valid: bool
    mag_valid: bool
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def accel_msec2(self) -> typing.Annotated[list[float], "FixedSize(3)"]:
        ...
    @accel_msec2.setter
    def accel_msec2(self, arg0: typing.Annotated[collections.abc.Sequence[typing.SupportsFloat], "FixedSize(3)"]) -> None:
        ...
    @property
    def arrival_timestamp_ns(self) -> int:
        ...
    @arrival_timestamp_ns.setter
    def arrival_timestamp_ns(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def capture_timestamp_ns(self) -> int:
        ...
    @capture_timestamp_ns.setter
    def capture_timestamp_ns(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def gyro_radsec(self) -> typing.Annotated[list[float], "FixedSize(3)"]:
        ...
    @gyro_radsec.setter
    def gyro_radsec(self, arg0: typing.Annotated[collections.abc.Sequence[typing.SupportsFloat], "FixedSize(3)"]) -> None:
        ...
    @property
    def mag_tesla(self) -> typing.Annotated[list[float], "FixedSize(3)"]:
        ...
    @mag_tesla.setter
    def mag_tesla(self, arg0: typing.Annotated[collections.abc.Sequence[typing.SupportsFloat], "FixedSize(3)"]) -> None:
        ...
    @property
    def temperature(self) -> float:
        ...
    @temperature.setter
    def temperature(self, arg0: typing.SupportsFloat) -> None:
        ...
class OnlineCalibState:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    def num_cameras(self) -> int:
        """
        Get the number of cameras.
        """
    def reset(self) -> None:
        """
        Reset the calibration state.
        """
    @property
    def cam_parameters(self) -> list[ProjectionModelParametersFloat]:
        ...
    @cam_parameters.setter
    def cam_parameters(self, arg0: collections.abc.Sequence[ProjectionModelParametersFloat]) -> None:
        ...
    @property
    def dt_ref_cam(self) -> list[int]:
        ...
    @dt_ref_cam.setter
    def dt_ref_cam(self, arg0: collections.abc.Sequence[typing.SupportsInt]) -> None:
        ...
    @property
    def imu_model_parameters(self) -> list[ImuMeasurementModelParametersFloat]:
        ...
    @imu_model_parameters.setter
    def imu_model_parameters(self, arg0: collections.abc.Sequence[ImuMeasurementModelParametersFloat]) -> None:
        ...
    @property
    def t_cam_body_imu(self) -> list[SE3f]:
        ...
    @t_cam_body_imu.setter
    def t_cam_body_imu(self, arg0: collections.abc.Sequence[SE3f]) -> None:
        ...
class PixelFrame:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: typing.SupportsInt, arg1: typing.SupportsInt, arg2: typing.SupportsInt, arg3: typing.SupportsInt, arg4: typing.SupportsInt, arg5: typing.SupportsInt, arg6: str, arg7: typing.SupportsInt, arg8: typing.SupportsFloat, arg9: typing.SupportsInt, arg10: collections.abc.Sequence[typing.SupportsInt]) -> None:
        """
        Initialize a PixelFrame with the complete information.
        """
    def get_buffer(self) -> list[int]:
        """
        Get image data buffer
        """
    def get_height(self) -> int:
        """
        Return number of rows in image
        """
    def get_width(self) -> int:
        """
        Return number of columns in image
        """
    def normalize_frame(self, arg0: bool) -> PixelFrame:
        """
        Normalize an input frame if possible and as necessary
        """
    def swap(self, arg0: PixelFrame) -> None:
        """
        Swap the image data
        """
class PpgConfiguration:
    """
    PPG sensor configuration type
    """
    description: str
    sensor_model: str
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def device_id(self) -> int:
        ...
    @device_id.setter
    def device_id(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def nominal_rate_hz(self) -> float:
        ...
    @nominal_rate_hz.setter
    def nominal_rate_hz(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def stream_id(self) -> int:
        ...
    @stream_id.setter
    def stream_id(self, arg0: typing.SupportsInt) -> None:
        ...
class PpgData:
    """
    PPG data type
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def capture_timestamp_ns(self) -> int:
        ...
    @capture_timestamp_ns.setter
    def capture_timestamp_ns(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def integration_time_us(self) -> float:
        ...
    @integration_time_us.setter
    def integration_time_us(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def led_current_ma(self) -> float:
        ...
    @led_current_ma.setter
    def led_current_ma(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def value(self) -> int:
        ...
    @value.setter
    def value(self, arg0: typing.SupportsInt) -> None:
        ...
class ProjectionModelParametersFloat:
    image_size: ...
    type: str
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def intrinsics(self) -> list[float]:
        ...
    @intrinsics.setter
    def intrinsics(self, arg0: collections.abc.Sequence[typing.SupportsFloat]) -> None:
        ...
    @property
    def max_radius_squared(self) -> float:
        ...
    @max_radius_squared.setter
    def max_radius_squared(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def readout_time_sec(self) -> float:
        ...
    @readout_time_sec.setter
    def readout_time_sec(self, arg0: typing.SupportsFloat) -> None:
        ...
class SensorConfiguration:
    """
    Configuration of a sensor stream, such as stream id, nominal frame rate
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self, arg0: None | projectaria_tools.core.sensor_data.ImageConfigRecord | projectaria_tools.core.sensor_data.MotionConfigRecord | projectaria_tools.core.sensor_data.GpsConfigRecord | projectaria_tools.core.sensor_data.WifiBeaconConfigRecord | projectaria_tools.core.sensor_data.AudioConfig | projectaria_tools.core.sensor_data.BarometerConfigRecord | ... | projectaria_tools.core.sensor_data.BluetoothBeaconConfigRecord | projectaria_tools.core.sensor_data.PpgConfiguration | projectaria_tools.core.sensor_data.AlsConfiguration | projectaria_tools.core.sensor_data.TemperatureConfiguration | projectaria_tools.core.sensor_data.EyeGazeConfiguration | projectaria_tools.core.sensor_data.HandPoseConfiguration | projectaria_tools.core.sensor_data.VioConfiguration | projectaria_tools.core.sensor_data.VioHighFreqConfiguration, arg1: SensorDataType) -> None:
        ...
    def als_configuration(self) -> AlsConfiguration:
        """
        Returns the sensor configuration as AlsConfiguration
        """
    def audio_configuration(self) -> AudioConfig:
        """
        Returns the sensor configuration as AudioConfig
        """
    def barometer_configuration(self) -> BarometerConfigRecord:
        """
        Returns the sensor configuration as BarometerConfigRecord
        """
    def bluetooth_configuration(self) -> BluetoothBeaconConfigRecord:
        """
        Returns the sensor configuration as Bluetooth
        """
    def eye_gaze_configuration(self) -> EyeGazeConfiguration:
        ...
    def get_nominal_rate_hz(self) -> float:
        """
        Returns the nominal frame rate of the sensor
        """
    def gps_configuration(self) -> GpsConfigRecord:
        """
        Returns the sensor configuration as GpsConfigRecord
        """
    def hand_pose_configuration(self) -> HandPoseConfiguration:
        ...
    def image_configuration(self) -> ImageConfigRecord:
        """
        Returns the sensor configuration as ImageConfigRecord
        """
    def magnetometer_configuration(self) -> MotionConfigRecord:
        """
        Returns the sensor configuration as MotionConfigRecord
        """
    def motion_configuration(self) -> MotionConfigRecord:
        """
        Returns the sensor configuration as MotionConfigRecord
        """
    def ppg_configuration(self) -> PpgConfiguration:
        """
        Returns the sensor configuration as PpgConfiguration
        """
    def sensor_data_type(self) -> SensorDataType:
        """
        Returns the type of sensor data 
        """
    def temperature_configuration(self) -> TemperatureConfiguration:
        """
        Returns the sensor configuration as TemperatureConfiguration
        """
    def vio_configuration(self) -> VioConfiguration:
        ...
    def vio_high_freq_configuration(self) -> VioHighFreqConfiguration:
        ...
    def wps_configuration(self) -> WifiBeaconConfigRecord:
        """
        Returns the sensor configuration as WifiBeaconConfigRecord
        """
class SensorData:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self, arg0: projectaria_tools.core.stream_id.StreamId, arg1: None | tuple[ImageData, ImageDataRecord] | projectaria_tools.core.sensor_data.MotionData | projectaria_tools.core.sensor_data.GpsData | projectaria_tools.core.sensor_data.WifiBeaconData | tuple[AudioData, AudioDataRecord] | projectaria_tools.core.sensor_data.BarometerData | ... | projectaria_tools.core.sensor_data.BluetoothBeaconData | projectaria_tools.core.sensor_data.PpgData | projectaria_tools.core.sensor_data.AlsData | projectaria_tools.core.sensor_data.TemperatureData | projectaria_tools.core.sensor_data.FrontendOutput | ... | ... | ..., arg2: SensorDataType, arg3: typing.SupportsInt, arg4: collections.abc.Mapping[TimeSyncMode, typing.SupportsInt]) -> None:
        ...
    def als_data(self) -> AlsData:
        ...
    def audio_data_and_record(self) -> tuple[AudioData, AudioDataRecord]:
        ...
    def barometer_data(self) -> BarometerData:
        ...
    def bluetooth_data(self) -> BluetoothBeaconData:
        ...
    def eye_gaze_data(self) -> ...:
        ...
    def get_time_ns(self, time_domain: TimeDomain) -> int:
        ...
    def gps_data(self) -> GpsData:
        ...
    def hand_pose_data(self) -> ...:
        ...
    def image_data_and_record(self) -> tuple[ImageData, ImageDataRecord]:
        ...
    def imu_data(self) -> MotionData:
        ...
    def magnetometer_data(self) -> MotionData:
        ...
    def ppg_data(self) -> PpgData:
        ...
    def sensor_data_type(self) -> SensorDataType:
        ...
    def stream_id(self) -> projectaria_tools.core.stream_id.StreamId:
        ...
    def temperature_data(self) -> TemperatureData:
        ...
    def vio_data(self) -> FrontendOutput:
        ...
    def vio_high_freq_data(self) -> ...:
        ...
    def wps_data(self) -> WifiBeaconData:
        ...
class SensorDataType:
    """
    Enum class for different types of sensor data used in projectaria_tools
    
    Members:
    
      NOT_VALID
    
      IMAGE : camera image streams
    
      IMU : Inertial measurement unit (IMU) data streams, including accelerometer and gyroscope, note that magnetometer is a different stream
    
      GPS : Global positioning system (GPS) data streams
    
      WPS : Wifi beacon data streams
    
      AUDIO : Audio data streams
    
      BAROMETER : Barometer data streams
    
      BLUETOOTH : Bluetooth data streams
    
      MAGNETOMETER : Magnetometer data streams
    
      PPG : Photoplethysmogram (PPG) data streams
    
      ALS : Ambient Light Sensor (ALS) data streams
    
      EYE_GAZE : EyeGaze data streams
    
      HAND_POSE : HandPose data streams
    
      VIO_HIGH_FREQ : Vio high frequency data streams
    
      VIO : Vio data streams
    """
    ALS: typing.ClassVar[SensorDataType]  # value = <SensorDataType.ALS: 10>
    AUDIO: typing.ClassVar[SensorDataType]  # value = <SensorDataType.AUDIO: 5>
    BAROMETER: typing.ClassVar[SensorDataType]  # value = <SensorDataType.BAROMETER: 6>
    BLUETOOTH: typing.ClassVar[SensorDataType]  # value = <SensorDataType.BLUETOOTH: 7>
    EYE_GAZE: typing.ClassVar[SensorDataType]  # value = <SensorDataType.EYE_GAZE: 15>
    GPS: typing.ClassVar[SensorDataType]  # value = <SensorDataType.GPS: 3>
    HAND_POSE: typing.ClassVar[SensorDataType]  # value = <SensorDataType.HAND_POSE: 16>
    IMAGE: typing.ClassVar[SensorDataType]  # value = <SensorDataType.IMAGE: 1>
    IMU: typing.ClassVar[SensorDataType]  # value = <SensorDataType.IMU: 2>
    MAGNETOMETER: typing.ClassVar[SensorDataType]  # value = <SensorDataType.MAGNETOMETER: 8>
    NOT_VALID: typing.ClassVar[SensorDataType]  # value = <SensorDataType.NOT_VALID: 0>
    PPG: typing.ClassVar[SensorDataType]  # value = <SensorDataType.PPG: 9>
    VIO: typing.ClassVar[SensorDataType]  # value = <SensorDataType.VIO: 13>
    VIO_HIGH_FREQ: typing.ClassVar[SensorDataType]  # value = <SensorDataType.VIO_HIGH_FREQ: 14>
    WPS: typing.ClassVar[SensorDataType]  # value = <SensorDataType.WPS: 4>
    __members__: typing.ClassVar[typing.Dict[str, SensorDataType]]  # value = {'NOT_VALID': <SensorDataType.NOT_VALID: 0>, 'IMAGE': <SensorDataType.IMAGE: 1>, 'IMU': <SensorDataType.IMU: 2>, 'GPS': <SensorDataType.GPS: 3>, 'WPS': <SensorDataType.WPS: 4>, 'AUDIO': <SensorDataType.AUDIO: 5>, 'BAROMETER': <SensorDataType.BAROMETER: 6>, 'BLUETOOTH': <SensorDataType.BLUETOOTH: 7>, 'MAGNETOMETER': <SensorDataType.MAGNETOMETER: 8>, 'PPG': <SensorDataType.PPG: 9>, 'ALS': <SensorDataType.ALS: 10>, 'EYE_GAZE': <SensorDataType.EYE_GAZE: 15>, 'HAND_POSE': <SensorDataType.HAND_POSE: 16>, 'VIO_HIGH_FREQ': <SensorDataType.VIO_HIGH_FREQ: 14>, 'VIO': <SensorDataType.VIO: 13>}
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: object) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: object) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(arg0: SensorDataType) -> int:
        ...
class TemperatureConfiguration:
    """
    Temperature sensor configuration type
    """
    sensor_model: str
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def device_id(self) -> int:
        ...
    @device_id.setter
    def device_id(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def nominal_rate_hz(self) -> float:
        ...
    @nominal_rate_hz.setter
    def nominal_rate_hz(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def stream_id(self) -> int:
        ...
    @stream_id.setter
    def stream_id(self, arg0: typing.SupportsInt) -> None:
        ...
class TemperatureData:
    """
    Temperature data type
    """
    sensor_name: str
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def capture_timestamp_ns(self) -> int:
        ...
    @capture_timestamp_ns.setter
    def capture_timestamp_ns(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def temperature_celsius(self) -> float:
        ...
    @temperature_celsius.setter
    def temperature_celsius(self, arg0: typing.SupportsFloat) -> None:
        ...
class TimeDomain:
    """
    Enum class for different types of timestamps used in projectaria_tools
    
    Members:
    
      RECORD_TIME : timestamp directly stored in vrs index, fast to access, but not guaranteed which time domain
    
      DEVICE_TIME : capture time in device's timedomain, <b>accurate</b>. All sensors on the same Aria glass share the same device time domain as they are issued from the same clock. We <b>strongly recommend</b> to always work with the device timestamp when dealing with <b>single-device</b> Aria data.
    
      HOST_TIME : arrival time in host computer's timedomain, may not be accurate
    
      TIME_CODE : capture in TimeSync server's timedomain, accurate across devices in a <b>multi-device</b> data capture.
    
      TIC_SYNC : capture in TimeSync server's timedomain where the server can be an Aria device, accurate across devices in a <b>multi-device</b> data capture
    
      SUBGHZ : capture in SubGhz timedomain, accurate across devices in a <b>multi-device</b> data
    
      UTC : capture in UTC timedomain, captured at 1 sample per minute
    """
    DEVICE_TIME: typing.ClassVar[TimeDomain]  # value = <TimeDomain.DEVICE_TIME: 1>
    HOST_TIME: typing.ClassVar[TimeDomain]  # value = <TimeDomain.HOST_TIME: 2>
    RECORD_TIME: typing.ClassVar[TimeDomain]  # value = <TimeDomain.RECORD_TIME: 0>
    SUBGHZ: typing.ClassVar[TimeDomain]  # value = <TimeDomain.SUBGHZ: 5>
    TIC_SYNC: typing.ClassVar[TimeDomain]  # value = <TimeDomain.TIC_SYNC: 4>
    TIME_CODE: typing.ClassVar[TimeDomain]  # value = <TimeDomain.TIME_CODE: 3>
    UTC: typing.ClassVar[TimeDomain]  # value = <TimeDomain.UTC: 6>
    __members__: typing.ClassVar[typing.Dict[str, TimeDomain]]  # value = {'RECORD_TIME': <TimeDomain.RECORD_TIME: 0>, 'DEVICE_TIME': <TimeDomain.DEVICE_TIME: 1>, 'HOST_TIME': <TimeDomain.HOST_TIME: 2>, 'TIME_CODE': <TimeDomain.TIME_CODE: 3>, 'TIC_SYNC': <TimeDomain.TIC_SYNC: 4>, 'SUBGHZ': <TimeDomain.SUBGHZ: 5>, 'UTC': <TimeDomain.UTC: 6>}
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: object) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: object) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(arg0: TimeDomain) -> int:
        ...
class TimeQueryOptions:
    """
    Members:
    
      BEFORE : the last valid data with `timestamp <= t_query
    
      AFTER : the first valid data with `timestamp >= t_query
    
      CLOSEST : the data whose `|timestamp - t_query|` is smallest
    """
    AFTER: typing.ClassVar[TimeQueryOptions]  # value = <TimeQueryOptions.AFTER: 1>
    BEFORE: typing.ClassVar[TimeQueryOptions]  # value = <TimeQueryOptions.BEFORE: 0>
    CLOSEST: typing.ClassVar[TimeQueryOptions]  # value = <TimeQueryOptions.CLOSEST: 2>
    __members__: typing.ClassVar[typing.Dict[str, TimeQueryOptions]]  # value = {'BEFORE': <TimeQueryOptions.BEFORE: 0>, 'AFTER': <TimeQueryOptions.AFTER: 1>, 'CLOSEST': <TimeQueryOptions.CLOSEST: 2>}
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: object) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: object) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(arg0: TimeQueryOptions) -> int:
        ...
class TimeSyncMode:
    """
    Members:
    
      TIME_CODE : TIMECODE mode
    
      TIC_SYNC : TIC_SYNC mode
    
      SUBGHZ : SUBGHZ mode
    
      UTC : UTC mode
    """
    SUBGHZ: typing.ClassVar[TimeSyncMode]  # value = <TimeSyncMode.SUBGHZ: 2>
    TIC_SYNC: typing.ClassVar[TimeSyncMode]  # value = <TimeSyncMode.TIC_SYNC: 1>
    TIME_CODE: typing.ClassVar[TimeSyncMode]  # value = <TimeSyncMode.TIME_CODE: 0>
    UTC: typing.ClassVar[TimeSyncMode]  # value = <TimeSyncMode.UTC: 3>
    __members__: typing.ClassVar[typing.Dict[str, TimeSyncMode]]  # value = {'TIME_CODE': <TimeSyncMode.TIME_CODE: 0>, 'TIC_SYNC': <TimeSyncMode.TIC_SYNC: 1>, 'SUBGHZ': <TimeSyncMode.SUBGHZ: 2>, 'UTC': <TimeSyncMode.UTC: 3>}
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: object) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: object) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(arg0: TimeSyncMode) -> int:
        ...
class TrackingQuality:
    """
    Members:
    
      UNKNOWN
    
      GOOD
    
      BAD
    
      UNRECOVERABLE
    """
    BAD: typing.ClassVar[TrackingQuality]  # value = <TrackingQuality.BAD: 2>
    GOOD: typing.ClassVar[TrackingQuality]  # value = <TrackingQuality.GOOD: 1>
    UNKNOWN: typing.ClassVar[TrackingQuality]  # value = <TrackingQuality.UNKNOWN: 0>
    UNRECOVERABLE: typing.ClassVar[TrackingQuality]  # value = <TrackingQuality.UNRECOVERABLE: 3>
    __members__: typing.ClassVar[typing.Dict[str, TrackingQuality]]  # value = {'UNKNOWN': <TrackingQuality.UNKNOWN: 0>, 'GOOD': <TrackingQuality.GOOD: 1>, 'BAD': <TrackingQuality.BAD: 2>, 'UNRECOVERABLE': <TrackingQuality.UNRECOVERABLE: 3>}
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: object) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: object) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(arg0: TrackingQuality) -> int:
        ...
class VioConfiguration:
    """
    Vio sensor configuration type
    """
    message_version: str
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def nominal_rate_hz(self) -> float:
        ...
    @nominal_rate_hz.setter
    def nominal_rate_hz(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def stream_id(self) -> int:
        ...
    @stream_id.setter
    def stream_id(self, arg0: typing.SupportsInt) -> None:
        ...
class VioHighFreqConfiguration:
    """
    Vio high frequency sensor configuration type
    """
    message_version: str
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def nominal_rate_hz(self) -> float:
        ...
    @nominal_rate_hz.setter
    def nominal_rate_hz(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def stream_id(self) -> int:
        ...
    @stream_id.setter
    def stream_id(self, arg0: typing.SupportsInt) -> None:
        ...
class VioStatus:
    """
    Members:
    
      VALID
    
      FILTER_NOT_INITIALIZED
    
      INVALID
    """
    FILTER_NOT_INITIALIZED: typing.ClassVar[VioStatus]  # value = <VioStatus.FILTER_NOT_INITIALIZED: 1>
    INVALID: typing.ClassVar[VioStatus]  # value = <VioStatus.INVALID: 2>
    VALID: typing.ClassVar[VioStatus]  # value = <VioStatus.VALID: 0>
    __members__: typing.ClassVar[typing.Dict[str, VioStatus]]  # value = {'VALID': <VioStatus.VALID: 0>, 'FILTER_NOT_INITIALIZED': <VioStatus.FILTER_NOT_INITIALIZED: 1>, 'INVALID': <VioStatus.INVALID: 2>}
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: object) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: object) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(arg0: VioStatus) -> int:
        ...
class VisualTrackingQuality:
    """
    Members:
    
      UNKNOWN
    
      BAD
    
      GOOD
    """
    BAD: typing.ClassVar[VisualTrackingQuality]  # value = <VisualTrackingQuality.BAD: 1>
    GOOD: typing.ClassVar[VisualTrackingQuality]  # value = <VisualTrackingQuality.GOOD: 2>
    UNKNOWN: typing.ClassVar[VisualTrackingQuality]  # value = <VisualTrackingQuality.UNKNOWN: 0>
    __members__: typing.ClassVar[typing.Dict[str, VisualTrackingQuality]]  # value = {'UNKNOWN': <VisualTrackingQuality.UNKNOWN: 0>, 'BAD': <VisualTrackingQuality.BAD: 1>, 'GOOD': <VisualTrackingQuality.GOOD: 2>}
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: object) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: object) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(arg0: VisualTrackingQuality) -> int:
        ...
class WifiBeaconConfigRecord:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def stream_id(self) -> int:
        ...
    @stream_id.setter
    def stream_id(self, arg0: typing.SupportsInt) -> None:
        ...
class WifiBeaconData:
    bssid_mac: str
    ssid: str
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def board_scan_request_complete_timestamp_ns(self) -> int:
        ...
    @board_scan_request_complete_timestamp_ns.setter
    def board_scan_request_complete_timestamp_ns(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def board_scan_request_start_timestamp_ns(self) -> int:
        ...
    @board_scan_request_start_timestamp_ns.setter
    def board_scan_request_start_timestamp_ns(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def board_timestamp_ns(self) -> int:
        ...
    @board_timestamp_ns.setter
    def board_timestamp_ns(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def freq_mhz(self) -> float:
        ...
    @freq_mhz.setter
    def freq_mhz(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def rssi(self) -> float:
        ...
    @rssi.setter
    def rssi(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def rssi_per_antenna(self) -> list[float]:
        ...
    @rssi_per_antenna.setter
    def rssi_per_antenna(self, arg0: collections.abc.Sequence[typing.SupportsFloat]) -> None:
        ...
    @property
    def system_timestamp_ns(self) -> int:
        ...
    @system_timestamp_ns.setter
    def system_timestamp_ns(self, arg0: typing.SupportsInt) -> None:
        ...
def get_sensor_data_type_name(arg0: SensorDataType) -> str:
    """
    converts the enum to readable string
    """
def get_time_domain_name(arg0: TimeDomain) -> str:
    """
    A helper function to return a descriptive name for a given TimeDomain enum
    """
def has_calibration(type: SensorDataType) -> bool:
    """
    checks if calibration exists for a specific stream
    """
def supports_host_time_domain(type: SensorDataType) -> bool:
    """
    checks if host time domain is supported by a type. Note we encourage user to avoid using host time domains as arrival timestamps are inaccurate.
    """
AFTER: TimeQueryOptions  # value = <TimeQueryOptions.AFTER: 1>
ALS: SensorDataType  # value = <SensorDataType.ALS: 10>
AUDIO: SensorDataType  # value = <SensorDataType.AUDIO: 5>
BAD: VisualTrackingQuality  # value = <VisualTrackingQuality.BAD: 1>
BAROMETER: SensorDataType  # value = <SensorDataType.BAROMETER: 6>
BEFORE: TimeQueryOptions  # value = <TimeQueryOptions.BEFORE: 0>
BLUETOOTH: SensorDataType  # value = <SensorDataType.BLUETOOTH: 7>
CLOSEST: TimeQueryOptions  # value = <TimeQueryOptions.CLOSEST: 2>
DEVICE_TIME: TimeDomain  # value = <TimeDomain.DEVICE_TIME: 1>
EYE_GAZE: SensorDataType  # value = <SensorDataType.EYE_GAZE: 15>
FILTER_NOT_INITIALIZED: VioStatus  # value = <VioStatus.FILTER_NOT_INITIALIZED: 1>
GOOD: VisualTrackingQuality  # value = <VisualTrackingQuality.GOOD: 2>
GPS: SensorDataType  # value = <SensorDataType.GPS: 3>
HAND_POSE: SensorDataType  # value = <SensorDataType.HAND_POSE: 16>
HOST_TIME: TimeDomain  # value = <TimeDomain.HOST_TIME: 2>
IMAGE: SensorDataType  # value = <SensorDataType.IMAGE: 1>
IMU: SensorDataType  # value = <SensorDataType.IMU: 2>
INVALID: VioStatus  # value = <VioStatus.INVALID: 2>
MAGNETOMETER: SensorDataType  # value = <SensorDataType.MAGNETOMETER: 8>
NOT_VALID: SensorDataType  # value = <SensorDataType.NOT_VALID: 0>
PPG: SensorDataType  # value = <SensorDataType.PPG: 9>
RECORD_TIME: TimeDomain  # value = <TimeDomain.RECORD_TIME: 0>
SUBGHZ: TimeSyncMode  # value = <TimeSyncMode.SUBGHZ: 2>
TIC_SYNC: TimeSyncMode  # value = <TimeSyncMode.TIC_SYNC: 1>
TIME_CODE: TimeSyncMode  # value = <TimeSyncMode.TIME_CODE: 0>
UNKNOWN: VisualTrackingQuality  # value = <VisualTrackingQuality.UNKNOWN: 0>
UNRECOVERABLE: TrackingQuality  # value = <TrackingQuality.UNRECOVERABLE: 3>
UTC: TimeSyncMode  # value = <TimeSyncMode.UTC: 3>
VALID: VioStatus  # value = <VioStatus.VALID: 0>
VIO: SensorDataType  # value = <SensorDataType.VIO: 13>
VIO_HIGH_FREQ: SensorDataType  # value = <SensorDataType.VIO_HIGH_FREQ: 14>
WPS: SensorDataType  # value = <SensorDataType.WPS: 4>
