from __future__ import annotations
import typing
__all__ = ['Settings', 'run']
class Settings:
    """
    Vrs health check settings.
    """
    ignore_audio: bool
    ignore_bluetooth: bool
    ignore_gps: bool
    is_interactive: bool
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def default_gps_rate_hz(self) -> float:
        ...
    @default_gps_rate_hz.setter
    def default_gps_rate_hz(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def default_imu_period_us(self) -> float:
        ...
    @default_imu_period_us.setter
    def default_imu_period_us(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_allowed_rotation_accel_rad_per_s2(self) -> float:
        ...
    @max_allowed_rotation_accel_rad_per_s2.setter
    def max_allowed_rotation_accel_rad_per_s2(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_camera_exposure_ms(self) -> float:
        ...
    @max_camera_exposure_ms.setter
    def max_camera_exposure_ms(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_camera_gain(self) -> float:
        ...
    @max_camera_gain.setter
    def max_camera_gain(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_frame_drop_us(self) -> int:
        ...
    @max_frame_drop_us.setter
    def max_frame_drop_us(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def max_imu_skip_us(self) -> float:
        ...
    @max_imu_skip_us.setter
    def max_imu_skip_us(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_non_physical_accel(self) -> float:
        ...
    @max_non_physical_accel.setter
    def max_non_physical_accel(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_temp(self) -> float:
        ...
    @max_temp.setter
    def max_temp(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def min_alignment_score(self) -> float:
        ...
    @min_alignment_score.setter
    def min_alignment_score(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def min_audio_score(self) -> float:
        ...
    @min_audio_score.setter
    def min_audio_score(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def min_baro_score(self) -> float:
        ...
    @min_baro_score.setter
    def min_baro_score(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def min_camera_exposure_ms(self) -> float:
        ...
    @min_camera_exposure_ms.setter
    def min_camera_exposure_ms(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def min_camera_gain(self) -> float:
        ...
    @min_camera_gain.setter
    def min_camera_gain(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def min_camera_score(self) -> float:
        ...
    @min_camera_score.setter
    def min_camera_score(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def min_gps_accuracy(self) -> float:
        ...
    @min_gps_accuracy.setter
    def min_gps_accuracy(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def min_imu_score(self) -> float:
        ...
    @min_imu_score.setter
    def min_imu_score(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def min_temp(self) -> float:
        ...
    @min_temp.setter
    def min_temp(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def min_time_domain_mapping_score(self) -> float:
        ...
    @min_time_domain_mapping_score.setter
    def min_time_domain_mapping_score(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def physical_accel_threshold(self) -> float:
        ...
    @physical_accel_threshold.setter
    def physical_accel_threshold(self, arg0: typing.SupportsFloat) -> None:
        ...
def run(path: str, json_out_filename: str = ..., settings: Settings = ..., dropped_out_filename: str = ..., print_stats: bool = ..., disable_logging: bool = ...) -> int:
    """
    Run vrs health check.
    """
