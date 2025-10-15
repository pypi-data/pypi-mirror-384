from __future__ import annotations
import projectaria_tools.core.calibration
import projectaria_tools.core.sensor_data
import collections.abc
import datetime
import numpy
import numpy.typing
import typing
from . import hand_tracking
__all__ = ['ClosedLoopTrajectoryPose', 'EyeGaze', 'EyeGazeVergence', 'GlobalPointPosition', 'HandTrackingDataPaths', 'MpsDataPaths', 'MpsDataPathsProvider', 'MpsDataProvider', 'MpsEyegazeDataPaths', 'MpsSlamDataPaths', 'OnlineCalibration', 'OpenLoopTrajectoryPose', 'PointObservation', 'StaticCameraCalibration', 'StreamCompressionMode', 'compute_depth_and_combined_gaze_direction', 'get_eyegaze_point_at_depth', 'get_gaze_intersection_point', 'get_gaze_vectors', 'get_unit_vector_from_yaw_pitch', 'hand_tracking', 'interpolate_hand_tracking_result', 'read_closed_loop_trajectory', 'read_eyegaze', 'read_global_point_cloud', 'read_online_calibration', 'read_open_loop_trajectory', 'read_point_observations', 'read_static_camera_calibrations']
class ClosedLoopTrajectoryPose:
    """
    
              Closed loop trajectory is the pose estimation output by our mapping process, in an arbitrary
      gravity aligned world coordinate frame. The estimation includes pose and dynamics (translational
      and angular velocities).
    
      Closed loop trajectories are fully bundle adjusted with detected loop closures, reducing the VIO
      drift which is present in the open loop trajectories. However, due to the loop closure
      correction, the “relative” and “local” trajectory accuracy within a short time span (i.e.
      seconds) might be worse compared to open loop trajectories.
    
      In some datasets we also share and use this format for trajectory pose ground truth from
      simulation or Optitrack
        
    """
    graph_uid: str
    tracking_timestamp: datetime.timedelta
    transform_world_device: SE3
    utc_timestamp: datetime.timedelta
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    def __repr__(self) -> str:
        ...
    @property
    def angular_velocity_device(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        ...
    @angular_velocity_device.setter
    def angular_velocity_device(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> None:
        ...
    @property
    def device_linear_velocity_device(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        ...
    @device_linear_velocity_device.setter
    def device_linear_velocity_device(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> None:
        ...
    @property
    def gravity_world(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        ...
    @gravity_world.setter
    def gravity_world(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> None:
        ...
    @property
    def quality_score(self) -> float:
        ...
    @quality_score.setter
    def quality_score(self, arg0: typing.SupportsFloat) -> None:
        ...
class EyeGaze:
    """
    An object representing single Eye gaze output.
    """
    combined_gaze_valid: bool
    session_uid: str
    spatial_gaze_point_valid: bool
    tracking_timestamp: datetime.timedelta
    vergence: EyeGazeVergence
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __getstate__(self) -> tuple:
        ...
    def __init__(self) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: tuple) -> None:
        ...
    @property
    def combined_gaze_origin_in_cpf(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float32], "[3, 1]"]:
        ...
    @combined_gaze_origin_in_cpf.setter
    def combined_gaze_origin_in_cpf(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float32, "[3, 1]"]) -> None:
        ...
    @property
    def depth(self) -> float:
        ...
    @depth.setter
    def depth(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def pitch(self) -> float:
        ...
    @pitch.setter
    def pitch(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def pitch_high(self) -> float:
        ...
    @pitch_high.setter
    def pitch_high(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def pitch_low(self) -> float:
        ...
    @pitch_low.setter
    def pitch_low(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def spatial_gaze_point_in_cpf(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float32], "[3, 1]"]:
        ...
    @spatial_gaze_point_in_cpf.setter
    def spatial_gaze_point_in_cpf(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float32, "[3, 1]"]) -> None:
        ...
    @property
    def yaw(self) -> float:
        ...
    @yaw.setter
    def yaw(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def yaw_high(self) -> float:
        ...
    @yaw_high.setter
    def yaw_high(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def yaw_low(self) -> float:
        ...
    @yaw_low.setter
    def yaw_low(self, arg0: typing.SupportsFloat) -> None:
        ...
class EyeGazeVergence:
    left_blink: bool
    left_blink_valid: bool
    left_gaze_valid: bool
    right_blink: bool
    right_blink_valid: bool
    right_gaze_valid: bool
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __getstate__(self) -> tuple:
        ...
    def __init__(self) -> None:
        ...
    def __setstate__(self, arg0: tuple) -> None:
        ...
    @property
    def left_pitch(self) -> float:
        ...
    @left_pitch.setter
    def left_pitch(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def left_yaw(self) -> float:
        ...
    @left_yaw.setter
    def left_yaw(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def left_yaw_high(self) -> float:
        ...
    @left_yaw_high.setter
    def left_yaw_high(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def left_yaw_low(self) -> float:
        ...
    @left_yaw_low.setter
    def left_yaw_low(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def right_pitch(self) -> float:
        ...
    @right_pitch.setter
    def right_pitch(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def right_yaw(self) -> float:
        ...
    @right_yaw.setter
    def right_yaw(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def right_yaw_high(self) -> float:
        ...
    @right_yaw_high.setter
    def right_yaw_high(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def right_yaw_low(self) -> float:
        ...
    @right_yaw_low.setter
    def right_yaw_low(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def tx_left_eye(self) -> float:
        ...
    @tx_left_eye.setter
    def tx_left_eye(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def tx_right_eye(self) -> float:
        ...
    @tx_right_eye.setter
    def tx_right_eye(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def ty_left_eye(self) -> float:
        ...
    @ty_left_eye.setter
    def ty_left_eye(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def ty_right_eye(self) -> float:
        ...
    @ty_right_eye.setter
    def ty_right_eye(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def tz_left_eye(self) -> float:
        ...
    @tz_left_eye.setter
    def tz_left_eye(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def tz_right_eye(self) -> float:
        ...
    @tz_right_eye.setter
    def tz_right_eye(self, arg0: typing.SupportsFloat) -> None:
        ...
class GlobalPointPosition:
    graph_uid: str
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __repr__(self) -> str:
        ...
    @property
    def distance_std(self) -> float:
        ...
    @distance_std.setter
    def distance_std(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def inverse_distance_std(self) -> float:
        ...
    @inverse_distance_std.setter
    def inverse_distance_std(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def position_world(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        ...
    @position_world.setter
    def position_world(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> None:
        ...
    @property
    def uid(self) -> int:
        ...
    @uid.setter
    def uid(self, arg0: typing.SupportsInt) -> None:
        ...
class HandTrackingDataPaths:
    """
    A struct that includes the file paths of all MPS Hand Tracking data for a VRS sequence processed by MPS.
    """
    hand_tracking_results: str
    summary: str
    wrist_and_palm_poses: str
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __repr__(self) -> str:
        ...
class MpsDataPaths:
    """
    A struct that includes the file paths of all MPS data for a sequence.
    """
    eyegaze: ...
    hand_tracking: ...
    root: str
    slam: ...
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    def __repr__(self) -> str:
        ...
class MpsDataPathsProvider:
    """
    This class is allows you to get all MPS data paths associated with an Aria sequence. 
    Note that all Aria open datasets will have MPS results which fit the format specified in this data provider.
    Use this data provider to avoid breaking changes in your code due to changes in MPS files
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self, arg0: str) -> None:
        ...
    def get_data_paths(self) -> MpsDataPaths:
        """
        Get the resulting data paths
        """
class MpsDataProvider:
    """
    This class is to load all MPS data given an MpsDataPaths object, and also provide all API needed to query that data. NOTE: to minimize disk usage, this data provider only loads data from disk after that data type is first queried.
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self, arg0: MpsDataPaths) -> None:
        ...
    def get_closed_loop_pose(self, device_timestamp_ns: typing.SupportsInt, time_query_options: projectaria_tools.core.sensor_data.TimeQueryOptions = ...) -> projectaria_tools.core.mps.ClosedLoopTrajectoryPose | None:
        """
        Query MPS for ClosedLoopTrajectoryPose at a specific timestamp. This will throw an exception if open loop trajectory data is not available. Check for data availability first using `has_closed_loop_poses()`
        """
    def get_eyegaze_version(self) -> str | None:
        """
        Get the MPS eye gaze version.
        """
    def get_general_eyegaze(self, device_timestamp_ns: typing.SupportsInt, time_query_options: projectaria_tools.core.sensor_data.TimeQueryOptions = ...) -> projectaria_tools.core.mps.EyeGaze | None:
        """
        Query MPS for general EyeGaze at a specific timestamp. This will throw an exception if general eye gaze data is not available. Check for data availability first using: `has_general_eyegaze()`
        """
    def get_hand_tracking_result(self, capture_timestamp_ns: typing.SupportsInt, time_query_options: projectaria_tools.core.sensor_data.TimeQueryOptions = ...) -> ... | None:
        """
        Get the MPS hand tracking result (landmarks, wrist transform, wrist and palm normals, etc.). This will throw an exception if the hand tracking results are not available.Check for data availability first using 'has_hand_tracking_results()'
        """
    def get_hand_tracking_version(self) -> str | None:
        """
        Get the MPS hand tracking version.
        """
    def get_interpolated_closed_loop_pose(self, device_timestamp_ns: typing.SupportsInt) -> projectaria_tools.core.mps.ClosedLoopTrajectoryPose | None:
        """
        Query MPS for ClosedLoopTrajectoryPose at a specific timestamp.interpolate between two poses if the timestamp is not exactly matched,and return None if query time is out of trajectory's time range.
        """
    def get_interpolated_hand_tracking_result(self, capture_timestamp_ns: typing.SupportsInt) -> ... | None:
        """
        Get the interploated MPS hand tracking result (landmarks, wrist transform, wrist and palm normals, etc.). This will return None if the interpolation fails. Check the return value for validity.
        """
    def get_online_calibration(self, device_timestamp_ns: typing.SupportsInt, time_query_options: projectaria_tools.core.sensor_data.TimeQueryOptions = ...) -> projectaria_tools.core.mps.OnlineCalibration | None:
        """
        Query MPS for OnlineCalibration at a specific timestamp. This will throw an exception if online calibration data is not available. Check for data availability first using `has_online_calibrations()`
        """
    def get_open_loop_pose(self, device_timestamp_ns: typing.SupportsInt, time_query_options: projectaria_tools.core.sensor_data.TimeQueryOptions = ...) -> projectaria_tools.core.mps.OpenLoopTrajectoryPose | None:
        """
        Query MPS for OpenLoopTrajectoryPose at a specific timestamp. This will throw an exception if open loop trajectory data is not available. Check for data availability first using `has_open_loop_poses()`
        """
    def get_personalized_eyegaze(self, device_timestamp_ns: typing.SupportsInt, time_query_options: projectaria_tools.core.sensor_data.TimeQueryOptions = ...) -> projectaria_tools.core.mps.EyeGaze | None:
        """
        Query MPS for personalized EyeGaze at a specific timestamp. This will throw an exception if personalized eye gaze data is not available. Check for data availability first using `has_personalized_eyegaze()`
        """
    def get_rgb_corrected_closed_loop_pose(self, device_timestamp_ns: typing.SupportsInt, time_query_options: projectaria_tools.core.sensor_data.TimeQueryOptions = ...) -> SE3 | None:
        """
        Get the corrected rgb frame pose based on the online calibration.
        """
    def get_rgb_corrected_timestamp_ns(self, device_timestamp_ns: typing.SupportsInt, time_query_options: projectaria_tools.core.sensor_data.TimeQueryOptions = ...) -> int | None:
        """
        Get the corrected rgb frame timestamp based on the online calibration.
        """
    def get_semidense_observations(self) -> list[PointObservation]:
        """
        Get the MPS point observations. This will throw an exception if the observations are not available. Check for data availability first using 'has_semidense_observations()'
        """
    def get_semidense_point_cloud(self) -> list[GlobalPointPosition]:
        """
        Get the MPS semidense point cloud. This will throw an exception if the point cloud is not available. Check for data availability first using 'has_semidense_point_cloud()'
        """
    def get_slam_version(self) -> str | None:
        """
        Get the MPS SLAM version.
        """
    def get_wrist_and_palm_pose(self, capture_timestamp_ns: typing.SupportsInt, time_query_options: projectaria_tools.core.sensor_data.TimeQueryOptions = ...) -> ... | None:
        """
        Get the MPS wrist and palm pose. This will throw an exception if the wrist and palm poses are not available. Check for data availability first using 'has_wrist_and_palm_poses()'
        """
    def has_closed_loop_poses(self) -> bool:
        """
        Check if closed loop poses are available in the MPS data paths
        """
    def has_general_eyegaze(self) -> bool:
        """
        Check if general eye gaze data is available in the MPS data paths
        """
    def has_hand_tracking_results(self) -> bool:
        """
        Check if hand tracking results are available in the MPS data paths
        """
    def has_online_calibrations(self) -> bool:
        """
        Check if online calibrations are available in the MPS data paths
        """
    def has_open_loop_poses(self) -> bool:
        """
        Check if open loop poses are available in the MPS data paths
        """
    def has_personalized_eyegaze(self) -> bool:
        """
        Check if personalized eye gaze data is available in the MPS data paths
        """
    def has_semidense_observations(self) -> bool:
        """
        Check if semidense observations are available in the MPS data paths
        """
    def has_semidense_point_cloud(self) -> bool:
        """
        Check if semidense point cloud data is available in the MPS data paths
        """
    def has_wrist_and_palm_poses(self) -> bool:
        """
        Check if wrist and palm poses are available in the MPS data paths
        """
class MpsEyegazeDataPaths:
    """
    A struct that includes the file paths of all MPS eye gaze data for a sequence.
    """
    general_eyegaze: str
    personalized_eyegaze: str
    summary: str
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __repr__(self) -> str:
        ...
class MpsSlamDataPaths:
    """
    A struct that includes the file paths of all MPS SLAM data for a VRS sequence processed by MPS.
    """
    closed_loop_trajectory: str
    online_calibrations: str
    open_loop_trajectory: str
    semidense_observations: str
    semidense_points: str
    summary: str
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __repr__(self) -> str:
        ...
class OnlineCalibration:
    tracking_timestamp: datetime.timedelta
    utc_timestamp: datetime.timedelta
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def get_camera_calib(self, label: str) -> projectaria_tools.core.calibration.CameraCalibration | None:
        """
        Helper function to get the camera calibration of a specific camera label
        """
    @property
    def camera_calibs(self) -> list[projectaria_tools.core.calibration.CameraCalibration]:
        ...
    @camera_calibs.setter
    def camera_calibs(self, arg0: collections.abc.Sequence[projectaria_tools.core.calibration.CameraCalibration]) -> None:
        ...
    @property
    def imu_calibs(self) -> list[projectaria_tools.core.calibration.ImuCalibration]:
        ...
    @imu_calibs.setter
    def imu_calibs(self, arg0: collections.abc.Sequence[projectaria_tools.core.calibration.ImuCalibration]) -> None:
        ...
class OpenLoopTrajectoryPose:
    """
    
            Open loop trajectory is the odometry estimation output by the visual-inertial odometry (VIO), in
            an arbitrary odometry coordinate frame. The estimation includes pose and dynamics (translational
            and angular velocities).
    
            The open loop trajectory has good “relative” and “local” accuracy: the relative transformation
            between two frames is accurate when the time span between two frames is short (within a few
            minutes). However, the open loop trajectory has increased drift error accumulated over time spent
            and travel distance. Consider using closed loop trajectory if you are looking for trajectory
            without drift error.
        
    """
    session_uid: str
    tracking_timestamp: datetime.timedelta
    transform_odometry_device: SE3
    utc_timestamp: datetime.timedelta
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    def __repr__(self) -> str:
        ...
    @property
    def angular_velocity_device(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        ...
    @angular_velocity_device.setter
    def angular_velocity_device(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> None:
        ...
    @property
    def device_linear_velocity_odometry(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        ...
    @device_linear_velocity_odometry.setter
    def device_linear_velocity_odometry(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> None:
        ...
    @property
    def gravity_odometry(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        ...
    @gravity_odometry.setter
    def gravity_odometry(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> None:
        ...
    @property
    def quality_score(self) -> float:
        ...
    @quality_score.setter
    def quality_score(self, arg0: typing.SupportsFloat) -> None:
        ...
class PointObservation:
    """
    2D observations of the point
    """
    camera_serial: str
    frame_capture_timestamp: datetime.timedelta
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __repr__(self) -> str:
        ...
    @property
    def point_uid(self) -> int:
        ...
    @point_uid.setter
    def point_uid(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def uv(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float32], "[2, 1]"]:
        ...
    @uv.setter
    def uv(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float32, "[2, 1]"]) -> None:
        ...
class StaticCameraCalibration:
    """
    Static camera intrinsic calibration and extrinsics in the world frame
    """
    camera_uid: str
    graph_uid: str
    intrinsics_type: str
    transform_world_cam: SE3
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __repr__(self) -> str:
        ...
    @property
    def end_frame_idx(self) -> int | None:
        ...
    @end_frame_idx.setter
    def end_frame_idx(self, arg0: typing.SupportsInt | None) -> None:
        ...
    @property
    def height(self) -> int:
        ...
    @height.setter
    def height(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def intrinsics(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float32], "[8, 1]"]:
        ...
    @intrinsics.setter
    def intrinsics(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float32, "[8, 1]"]) -> None:
        ...
    @property
    def quality(self) -> int:
        ...
    @quality.setter
    def quality(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def start_frame_idx(self) -> int | None:
        ...
    @start_frame_idx.setter
    def start_frame_idx(self, arg0: typing.SupportsInt | None) -> None:
        ...
    @property
    def width(self) -> int:
        ...
    @width.setter
    def width(self, arg0: typing.SupportsInt) -> None:
        ...
class StreamCompressionMode:
    """
    Stream compression mode
    
    Members:
    
      NONE : No compression
    
      GZIP : GZIP compression
    """
    GZIP: typing.ClassVar[StreamCompressionMode]  # value = <StreamCompressionMode.GZIP: 1>
    NONE: typing.ClassVar[StreamCompressionMode]  # value = <StreamCompressionMode.NONE: 0>
    __members__: typing.ClassVar[typing.Dict[str, StreamCompressionMode]]  # value = {'NONE': <StreamCompressionMode.NONE: 0>, 'GZIP': <StreamCompressionMode.GZIP: 1>}
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
    def value(arg0: StreamCompressionMode) -> int:
        ...
def compute_depth_and_combined_gaze_direction(left_yaw_rads: typing.SupportsFloat, right_yaw_rads: typing.SupportsFloat, pitch_rads: typing.SupportsFloat) -> tuple[float, float, float]:
    """
     Given the left and right yaw angles and common pitch get the combined gaze angles and depth in CPF frame.
      Parameters
      __________
      left_yaw_rads: Left Yaw angle in radians in CPF frame.
      right_yaw_rads: Right Yaw angle in radians in CPF frame.
      pitch_rads: Pitch angle in radians in CPF frame.
    """
def get_eyegaze_point_at_depth(yaw_rads: typing.SupportsFloat, pitch_rads: typing.SupportsFloat, depth_m: typing.SupportsFloat) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
    """
     Given the yaw and pitch angles of the eye gaze and a depth, return the gaze 3D point in CPF frame.
      Parameters
      __________
      yaw_rads: Yaw angle in radians in CPF frame.
      pitch_rads: Pitch angle in radians in CPF frame.
      depth_m: Depth of the point in meters.
    """
def get_gaze_intersection_point(left_yaw_rads: typing.SupportsFloat, right_yaw_rads: typing.SupportsFloat, pitch_rads: typing.SupportsFloat) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
    """
     Given the left and right yaw angles and common pitch get the intersection point in 3D in CPF frame.
      Parameters
      __________
      left_yaw_rads: Left Yaw angle in radians in CPF frame.
      right_yaw_rads: Right Yaw angle in radians in CPF frame.
      pitch_rads: Pitch angle in radians in CPF frame.
    """
def get_gaze_vectors(left_yaw_rads: typing.SupportsFloat, right_yaw_rads: typing.SupportsFloat, pitch_rads: typing.SupportsFloat) -> tuple[typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"], typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]]:
    """
     Given the left and right yaw angles and common pitch get the left and right gaze vectors from their respective origins in XYZ CPF frame.
      Parameters
      __________
      left_yaw_rads: Left Yaw angle in radians in CPF frame.
      right_yaw_rads: Right Yaw angle in radians in CPF frame.
      pitch_rads: Pitch angle in radians in CPF frame.
    """
def get_unit_vector_from_yaw_pitch(yaw_rads: typing.SupportsFloat, pitch_rads: typing.SupportsFloat) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
    """
     Get Gaze Direction as Vector 3D given yaw and pitch values.
      Parameters
      __________
      yaw_rads: Yaw angle in radians.
      pitch_rads: Pitch angle in radians.
    """
def interpolate_hand_tracking_result(hand_pose1: ..., hand_pose2: ..., target_timestamp_ms: typing.SupportsInt) -> ... | None:
    """
    Linear interpolation between two HandTrackingResult objects based on target timestamp.
           1. A hand (left/right) is only interpolated if both input results have valid data for that
      hand. If either input is missing a hand, the interpolated result will have nullopt for that hand.
           2. Returns nullopt if the time difference between input results exceeds 100ms (interpolation
      is considered unreliable beyond this threshold for landmark positions).
    """
def read_closed_loop_trajectory(path: str) -> list[ClosedLoopTrajectoryPose]:
    """
    Read Closed loop trajectory.
      Parameters
      __________
      path: Path to the closed loop trajectory csv file. Usually named 'closed_loop_trajectory.csv'
    """
def read_eyegaze(path: str) -> list[EyeGaze]:
    """
    Read Eye Gaze from the eye gaze output generated via MPS.
      Parameters
      __________
      path: Path to the eye gaze csv file.
    """
@typing.overload
def read_global_point_cloud(path: str, compression: StreamCompressionMode) -> list[GlobalPointPosition]:
    """
    Read global point cloud.
      Parameters
      __________
      path: Path to the global point cloud file. Usually named 'global_pointcloud.csv.gz'
      compression: Stream compression mode for reading csv file.
    """
@typing.overload
def read_global_point_cloud(path: str) -> list[GlobalPointPosition]:
    """
    Read global point cloud.
      Parameters
      __________
      path: Path to the global point cloud file. Usually named 'global_pointcloud' with a '.csv' or '.csv.gz'
    """
def read_online_calibration(path: str) -> list[OnlineCalibration]:
    """
    Read estimated online calibrations.
      Parameters
      __________
      path: Path to the online calibration jsonl file. Usually named 'online_calibration.jsonl'
    """
def read_open_loop_trajectory(path: str) -> list[OpenLoopTrajectoryPose]:
    """
    Read Open loop trajectory.
      Parameters
      __________
      path: Path to the open loop trajectory csv file. Usually named 'open_loop_trajectory.csv'
    """
@typing.overload
def read_point_observations(path: str, compression: StreamCompressionMode) -> list[PointObservation]:
    """
    Read point observations.
      Parameters
      __________
      path: Path to the point observations file. Usually named 'semidense_observations.csv.gz'
      compression: Stream compression mode for reading csv file.
    """
@typing.overload
def read_point_observations(path: str) -> list[PointObservation]:
    """
    Read point observations.
      Parameters
      __________
      path: Path to the point observations file. Usually named 'semidense_observations' with a '.csv' or '.csv.gz'
    """
def read_static_camera_calibrations(path: str) -> list[StaticCameraCalibration]:
    """
    Read static camera calibrations.
      Parameters
      __________
      path: Path to the static camera calibrations file.
    """
