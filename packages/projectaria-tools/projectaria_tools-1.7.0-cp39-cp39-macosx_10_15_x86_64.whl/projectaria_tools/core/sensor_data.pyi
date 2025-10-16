from __future__ import annotations
import projectaria_tools.core.stream_id
import collections.abc
import numpy
import typing
__all__ = ['AFTER', 'AUDIO', 'AudioConfig', 'AudioData', 'AudioDataRecord', 'BAROMETER', 'BEFORE', 'BLUETOOTH', 'BarometerConfigRecord', 'BarometerData', 'BluetoothBeaconConfigRecord', 'BluetoothBeaconData', 'CLOSEST', 'DEVICE_TIME', 'GPS', 'GpsConfigRecord', 'GpsData', 'HOST_TIME', 'IMAGE', 'IMU', 'ImageConfigRecord', 'ImageData', 'ImageDataRecord', 'MAGNETOMETER', 'MotionConfigRecord', 'MotionData', 'NOT_VALID', 'PixelFrame', 'RECORD_TIME', 'SensorConfiguration', 'SensorData', 'SensorDataType', 'TIC_SYNC', 'TIME_CODE', 'TimeDomain', 'TimeQueryOptions', 'TimeSyncMode', 'WPS', 'WifiBeaconConfigRecord', 'WifiBeaconData', 'get_sensor_data_type_name', 'get_time_domain_name', 'has_calibration', 'supports_host_time_domain']
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
class GpsConfigRecord:
    """
    Gps sensor configuration type
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
    def stream_id(self) -> int:
        ...
    @stream_id.setter
    def stream_id(self, arg0: typing.SupportsInt) -> None:
        ...
class GpsData:
    """
    Gps data type, note that GPS sensor data are already rectified
    """
    provider: str
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
class PixelFrame:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
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
class SensorConfiguration:
    """
    Configuration of a sensor stream, such as stream id, nominal frame rate
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self, arg0: None | projectaria_tools.core.sensor_data.ImageConfigRecord | projectaria_tools.core.sensor_data.MotionConfigRecord | projectaria_tools.core.sensor_data.GpsConfigRecord | projectaria_tools.core.sensor_data.WifiBeaconConfigRecord | projectaria_tools.core.sensor_data.AudioConfig | projectaria_tools.core.sensor_data.BarometerConfigRecord | projectaria_tools.core.sensor_data.BluetoothBeaconConfigRecord, arg1: SensorDataType) -> None:
        ...
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
    def get_nominal_rate_hz(self) -> float:
        """
        Returns the nominal frame rate of the sensor
        """
    def gps_configuration(self) -> GpsConfigRecord:
        """
        Returns the sensor configuration as GpsConfigRecord
        """
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
    def sensor_data_type(self) -> SensorDataType:
        """
        Returns the type of sensor data 
        """
    def wps_configuration(self) -> WifiBeaconConfigRecord:
        """
        Returns the sensor configuration as WifiBeaconConfigRecord
        """
class SensorData:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self, arg0: projectaria_tools.core.stream_id.StreamId, arg1: None | tuple[ImageData, ImageDataRecord] | projectaria_tools.core.sensor_data.MotionData | projectaria_tools.core.sensor_data.GpsData | projectaria_tools.core.sensor_data.WifiBeaconData | tuple[AudioData, AudioDataRecord] | projectaria_tools.core.sensor_data.BarometerData | projectaria_tools.core.sensor_data.BluetoothBeaconData, arg2: SensorDataType, arg3: typing.SupportsInt, arg4: collections.abc.Mapping[TimeSyncMode, typing.SupportsInt]) -> None:
        ...
    def audio_data_and_record(self) -> tuple[AudioData, AudioDataRecord]:
        ...
    def barometer_data(self) -> BarometerData:
        ...
    def bluetooth_data(self) -> BluetoothBeaconData:
        ...
    def get_time_ns(self, time_domain: TimeDomain) -> int:
        ...
    def gps_data(self) -> GpsData:
        ...
    def image_data_and_record(self) -> tuple[ImageData, ImageDataRecord]:
        ...
    def imu_data(self) -> MotionData:
        ...
    def magnetometer_data(self) -> MotionData:
        ...
    def sensor_data_type(self) -> SensorDataType:
        ...
    def stream_id(self) -> projectaria_tools.core.stream_id.StreamId:
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
    """
    AUDIO: typing.ClassVar[SensorDataType]  # value = <SensorDataType.AUDIO: 5>
    BAROMETER: typing.ClassVar[SensorDataType]  # value = <SensorDataType.BAROMETER: 6>
    BLUETOOTH: typing.ClassVar[SensorDataType]  # value = <SensorDataType.BLUETOOTH: 7>
    GPS: typing.ClassVar[SensorDataType]  # value = <SensorDataType.GPS: 3>
    IMAGE: typing.ClassVar[SensorDataType]  # value = <SensorDataType.IMAGE: 1>
    IMU: typing.ClassVar[SensorDataType]  # value = <SensorDataType.IMU: 2>
    MAGNETOMETER: typing.ClassVar[SensorDataType]  # value = <SensorDataType.MAGNETOMETER: 8>
    NOT_VALID: typing.ClassVar[SensorDataType]  # value = <SensorDataType.NOT_VALID: 0>
    WPS: typing.ClassVar[SensorDataType]  # value = <SensorDataType.WPS: 4>
    __members__: typing.ClassVar[typing.Dict[str, SensorDataType]]  # value = {'NOT_VALID': <SensorDataType.NOT_VALID: 0>, 'IMAGE': <SensorDataType.IMAGE: 1>, 'IMU': <SensorDataType.IMU: 2>, 'GPS': <SensorDataType.GPS: 3>, 'WPS': <SensorDataType.WPS: 4>, 'AUDIO': <SensorDataType.AUDIO: 5>, 'BAROMETER': <SensorDataType.BAROMETER: 6>, 'BLUETOOTH': <SensorDataType.BLUETOOTH: 7>, 'MAGNETOMETER': <SensorDataType.MAGNETOMETER: 8>}
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
class TimeDomain:
    """
    Enum class for different types of timestamps used in projectaria_tools
    
    Members:
    
      RECORD_TIME : timestamp directly stored in vrs index, fast to access, but not guaranteed which time domain
    
      DEVICE_TIME : capture time in device's timedomain, <b>accurate</b>. All sensors on the same Aria glass share the same device time domain as they are issued from the same clock. We <b>strongly recommend</b> to always work with the device timestamp when dealing with <b>single-device</b> Aria data.
    
      HOST_TIME : arrival time in host computer's timedomain, may not be accurate
    
      TIME_CODE : capture in TimeSync server's timedomain, accurate across devices in a <b>multi-device</b> data capture.
    
      TIC_SYNC : capture in TimeSync server's timedomain where the server can be an Aria device, accurate across devices in a <b>multi-device</b> data capture
    """
    DEVICE_TIME: typing.ClassVar[TimeDomain]  # value = <TimeDomain.DEVICE_TIME: 1>
    HOST_TIME: typing.ClassVar[TimeDomain]  # value = <TimeDomain.HOST_TIME: 2>
    RECORD_TIME: typing.ClassVar[TimeDomain]  # value = <TimeDomain.RECORD_TIME: 0>
    TIC_SYNC: typing.ClassVar[TimeDomain]  # value = <TimeDomain.TIC_SYNC: 4>
    TIME_CODE: typing.ClassVar[TimeDomain]  # value = <TimeDomain.TIME_CODE: 3>
    __members__: typing.ClassVar[typing.Dict[str, TimeDomain]]  # value = {'RECORD_TIME': <TimeDomain.RECORD_TIME: 0>, 'DEVICE_TIME': <TimeDomain.DEVICE_TIME: 1>, 'HOST_TIME': <TimeDomain.HOST_TIME: 2>, 'TIME_CODE': <TimeDomain.TIME_CODE: 3>, 'TIC_SYNC': <TimeDomain.TIC_SYNC: 4>}
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
    """
    TIC_SYNC: typing.ClassVar[TimeSyncMode]  # value = <TimeSyncMode.TIC_SYNC: 1>
    TIME_CODE: typing.ClassVar[TimeSyncMode]  # value = <TimeSyncMode.TIME_CODE: 0>
    __members__: typing.ClassVar[typing.Dict[str, TimeSyncMode]]  # value = {'TIME_CODE': <TimeSyncMode.TIME_CODE: 0>, 'TIC_SYNC': <TimeSyncMode.TIC_SYNC: 1>}
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
AUDIO: SensorDataType  # value = <SensorDataType.AUDIO: 5>
BAROMETER: SensorDataType  # value = <SensorDataType.BAROMETER: 6>
BEFORE: TimeQueryOptions  # value = <TimeQueryOptions.BEFORE: 0>
BLUETOOTH: SensorDataType  # value = <SensorDataType.BLUETOOTH: 7>
CLOSEST: TimeQueryOptions  # value = <TimeQueryOptions.CLOSEST: 2>
DEVICE_TIME: TimeDomain  # value = <TimeDomain.DEVICE_TIME: 1>
GPS: SensorDataType  # value = <SensorDataType.GPS: 3>
HOST_TIME: TimeDomain  # value = <TimeDomain.HOST_TIME: 2>
IMAGE: SensorDataType  # value = <SensorDataType.IMAGE: 1>
IMU: SensorDataType  # value = <SensorDataType.IMU: 2>
MAGNETOMETER: SensorDataType  # value = <SensorDataType.MAGNETOMETER: 8>
NOT_VALID: SensorDataType  # value = <SensorDataType.NOT_VALID: 0>
RECORD_TIME: TimeDomain  # value = <TimeDomain.RECORD_TIME: 0>
TIC_SYNC: TimeSyncMode  # value = <TimeSyncMode.TIC_SYNC: 1>
TIME_CODE: TimeSyncMode  # value = <TimeSyncMode.TIME_CODE: 0>
WPS: SensorDataType  # value = <SensorDataType.WPS: 4>
