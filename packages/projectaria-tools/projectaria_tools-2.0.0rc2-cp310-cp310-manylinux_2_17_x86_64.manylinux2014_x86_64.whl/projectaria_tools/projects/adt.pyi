from __future__ import annotations
import projectaria_tools.core.data_provider
import projectaria_tools.core.image
import projectaria_tools.core.mps
import projectaria_tools.core.sensor_data
import collections.abc
import numpy
import numpy.typing
import typing
__all__ = ['Aria3dPose', 'Aria3dPoseDataWithDt', 'AriaDigitalTwinDataPaths', 'AriaDigitalTwinDataPathsProvider', 'AriaDigitalTwinDataProvider', 'AriaDigitalTwinSkeletonProvider', 'AriaImageDataWithDt', 'BoundingBox2dData', 'BoundingBox2dDataWithDt', 'BoundingBox3dData', 'BoundingBox3dDataWithDt', 'CanonicalPose', 'DEFORMABLE', 'DYNAMIC', 'DepthData', 'DepthDataWithDt', 'EyeGazeWithDt', 'HUMAN', 'InstanceInfo', 'InstanceType', 'MotionType', 'OBJECT', 'RIGID', 'RigidityType', 'RotationalSymmetry', 'RotationalSymmetryAxis', 'STATIC', 'SegmentationData', 'SegmentationDataWithDt', 'SkeletonFrame', 'SkeletonFrameWithDt', 'SyntheticData', 'SyntheticDataWithDt', 'UNKNOWN', 'bbox2d_to_image_coordinates', 'bbox2d_to_image_line_coordinates', 'bbox3d_to_coordinates', 'bbox3d_to_line_coordinates', 'get_interpolated_aria_3d_pose_at_timestamp_ns', 'get_interpolated_object_3d_boundingboxes_at_timestamp_ns', 'is_dataset_corrupt']
class Aria3dPose:
    """
    a simple struct to represent the pose of an Aria device at a certain time
    """
    graph_uid: str
    transform_scene_device: SE3
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def device_linear_velocity(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        ...
    @device_linear_velocity.setter
    def device_linear_velocity(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> None:
        ...
    @property
    def device_rotational_velocity(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        ...
    @device_rotational_velocity.setter
    def device_rotational_velocity(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> None:
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
class Aria3dPoseDataWithDt:
    """
    query result containing Aria device pose
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def data(self) -> Aria3dPose:
        ...
    def dt_ns(self) -> int:
        ...
    def is_valid(self) -> bool:
        ...
class AriaDigitalTwinDataPaths:
    """
    A struct that includes the file paths of all ADT data files for one sequence of one device.
    """
    aria_trajectory_filepath: str
    aria_vrs_filepath: str
    boundingboxes_2d_filepath: str
    depth_images_filepath: str
    eyegazes_filepath: str
    instances_filepath: str
    metadata_filepath: str
    mps: projectaria_tools.core.mps.MpsDataPaths
    object_boundingbox_3d_filepath: str
    object_trajectories_filepath: str
    segmentations_filepath: str
    sequence_name: str
    skeleton_metadata_filepath: str
    synthetic_vrs_filepath: str
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def skeletons_filepaths(self) -> dict[int, str]:
        ...
    @skeletons_filepaths.setter
    def skeletons_filepaths(self, arg0: collections.abc.Mapping[typing.SupportsInt, str]) -> None:
        ...
class AriaDigitalTwinDataPathsProvider:
    """
     This class is to load all data file paths from ADT data structure given a sequence path.  This class supports both v1.X dataset versions as well as v2.X dataset versions (and beyond)  which have different formats:  v1.X: Each ADT collection sequence may contain more than one Aria device wearers. The data  associated with each Aria device is called a subsequence:  ├── sequencePath         │   ├── subsequence1_Name  │   │   ├── 2d_bounding_box.csv  │   │   ├── 2d_bounding_box_with_skeleton.csv  │   │   ├── 3d_bounding_box.csv  │   │   ├── Skeleton_C.json  │   │   ├── skeleton_aria_association.json  │   │   ├── aria_trajectory.csv  │   │   ├── depth_images.vrs  │   │   ├── depth_images_with_skeleton.vrs  │   │   ├── eyegaze.csv  │   │   ├── instances.csv  │   │   ├── scene_objects.csv  │   │   ├── segmentations.vrs  │   │   ├── segmentations_with_skeleton.vrs  │   │   └── video.vrs  │   ├── subsequence2_Name  │   │   ├── 2d_bounding_box.csv  │   │   ├── ...  │   └── metadata.json  v2.X and beyond: We have removed the concept of subsequence. Each sequence can only contain one  Aria recording, and concurrent recordings can be fetched by looking the field in the metadata  file. This means we have the following file structure:  ├── sequencePath         │   ├── 2d_bounding_box.csv  │   ├── 2d_bounding_box_with_skeleton.csv  │   ├── 3d_bounding_box.csv  │   ├── Skeleton_C.json  │   ├── skeleton_aria_association.json  │   ├── aria_trajectory.csv  │   ├── depth_images.vrs  │   ├── depth_images_with_skeleton.vrs  │   ├── eyegaze.csv  │   ├── instances.csv  │   ├── scene_objects.csv  │   ├── segmentations.vrs  │   ├── segmentations_with_skeleton.vrs  │   └── video.vrs  │   └── metadata.json 
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self, arg0: str) -> None:
        ...
    def get_concurrent_sequence_name(self) -> str | None:
        """
        return string with name of sequence collected at the same time (if multi-sequence), return null otherwise
        """
    def get_datapaths(self, skeleton_flag: bool = ...) -> projectaria_tools.project.adt.AriaDigitalTwinDataPaths | None:
        """
        retrieve the DataPaths for this sequene. If loading a sequence that has version < 2.0 and has multiple subsequences, this will return the data paths associated with the first device serial
        """
    def get_datapaths_by_device_num(self, device_num: typing.SupportsInt, skeleton_flag: bool = ...) -> projectaria_tools.project.adt.AriaDigitalTwinDataPaths | None:
        """
        retrieve the DataPaths from a device based on its index. DEPRECATION NOTE: With dataset versions 2.0 and beyond, this function has been deprecated since there is only one device per sequence. If you are using this on older data, it will still work.If using on new data, it will only work if deviceNum is 0. 
        """
    def get_datapaths_by_device_serial(self, device_serial: str, skeleton_flag: bool = ...) -> projectaria_tools.project.adt.AriaDigitalTwinDataPaths | None:
        """
        retrieve the DataPaths from a device based on its serial number. DEPRECATION NOTE: With dataset versions 2.0 and beyond, this function has been deprecated since there is only one device per sequence. This function will still work with old or newer data as long as you are querying with the correct serial associated with this sequence.
        """
    def get_device_serial_number(self) -> str:
        """
        get the device serial number for this sequence. If loading a sequence that has version < 2.0 and has multiple subsequences, this will return the first device serial
        """
    def get_device_serial_numbers(self) -> list[str]:
        """
        get all device serial numbers in the recording sequence.DEPRECATION NOTE: With dataset versions 2.0 and beyond, this function has been deprecated since there is only one device per sequence. This function will still work with old or newer data, however, we recommend using getDeviceSerialNumber instead for newer data & @return a const reference to a vector of string
        """
    def get_num_skeletons(self) -> int:
        """
        get the number of skeletons in the current sequence
        """
    def get_scene_name(self) -> str:
        """
        get the scene name of the recording sequence
        """
    def is_multi_person(self) -> bool:
        """
        check if the sequence is a multi-person sequence
        """
class AriaDigitalTwinDataProvider:
    """
    This is the core data loader that should provide all the data access you will need foran ADT sequence. Note that each sequence may contain multiple devices, you should create one`AriaDigitalTwinDataProvider` instance for each device.
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self, arg0: AriaDigitalTwinDataPaths) -> None:
        ...
    def depth_data_provider_ptr(self) -> projectaria_tools.core.data_provider.VrsDataProvider:
        """
        get a pointer to the depth data provider
        """
    def get_aria_3d_pose_by_timestamp_ns(self, device_timestamp_ns: typing.SupportsInt, time_query_options: projectaria_tools.core.sensor_data.TimeQueryOptions = ...) -> Aria3dPoseDataWithDt:
        """
        Query the device pose of the Aria unit in the trajectory, by timestamp.
        """
    def get_aria_camera_calibration(self, stream_id: ...) -> projectaria_tools.core.calibration.CameraCalibration | None:
        """
        Get the camera calibration of an Aria camera, including intrinsics, distortion params,and projection functions.
        """
    def get_aria_device_capture_timestamps_ns(self, stream_id: ...) -> list[int]:
        """
        Get all timestamps (in ns) of all observations of an Aria sensor, in `TimeDomain::DeviceTime`.
        """
    def get_aria_image_by_timestamp_ns(self, device_time_stamp_ns: typing.SupportsInt, stream_id: ..., time_query_options: projectaria_tools.core.sensor_data.TimeQueryOptions = ...) -> AriaImageDataWithDt:
        """
        Query an Aria camera image by timestamp
        """
    def get_aria_transform_device_camera(self, stream_id: ...) -> SE3:
        """
        Get the pose of an Aria camera in the device coordinate frame.
        """
    def get_depth_image_by_timestamp_ns(self, device_timestamp_ns: typing.SupportsInt, stream_id: ..., time_query_options: projectaria_tools.core.sensor_data.TimeQueryOptions = ...) -> DepthDataWithDt:
        """
        Query a camera's depth image by timestamp
        """
    def get_device_time_from_timecode_ns(self, timecode_ns: typing.SupportsInt) -> int:
        """
        ADT uses Timecode to synchronize multiple Aria devices. Use this function to convert a timestamp from `TimeDomain::TimeCode` to `TimeDomain::DeviceTime`. See `adt_multiperson_tutorial.ipynb` for usage example.
        """
    def get_end_time_ns(self) -> int:
        """
        get the end time of the Aria poses in nanoseconds
        """
    def get_eyegaze_by_timestamp_ns(self, device_timestamp_ns: typing.SupportsInt, time_query_options: projectaria_tools.core.sensor_data.TimeQueryOptions = ...) -> EyeGazeWithDt:
        """
        Query eye gaze by timestamp. The eye gaze is in Central-Pupil-Frame (CPF).
        """
    def get_instance_ids(self) -> list[int]:
        """
        get all instances in a sequence. An instance can be any type of InstanceType
        """
    def get_instance_info_by_id(self, instance_id: typing.SupportsInt) -> InstanceInfo:
        """
        get instance information by instance id.
        """
    def get_object_2d_boundingboxes_by_timestamp_ns(self, device_timestamp_ns: typing.SupportsInt, stream_id: ..., time_query_options: projectaria_tools.core.sensor_data.TimeQueryOptions = ...) -> BoundingBox2dDataWithDt:
        """
        Query 2D object bounding boxes by timestamp, in the view of a given camera.
        """
    def get_object_3d_boundingboxes_by_timestamp_ns(self, device_timestamp_ns: typing.SupportsInt, time_query_options: projectaria_tools.core.sensor_data.TimeQueryOptions = ...) -> BoundingBox3dDataWithDt:
        """
        Query object 3D bounding boxes by timestamp.
        """
    def get_object_ids(self) -> list[int]:
        """
        get all instance ids as a vector whose `InstanceType == OBJECT`.
        """
    def get_segmentation_image_by_timestamp_ns(self, device_timestamp_ns: typing.SupportsInt, stream_id: ..., time_query_options: projectaria_tools.core.sensor_data.TimeQueryOptions = ...) -> SegmentationDataWithDt:
        """
        Query a camera's segmentation image by timestamp
        """
    def get_skeleton_2d_boundingboxes_by_timestamp_ns(self, device_timestamp_ns: typing.SupportsInt, stream_id: ..., time_query_options: projectaria_tools.core.sensor_data.TimeQueryOptions = ...) -> BoundingBox2dDataWithDt:
        """
        Query 2D skeleton bounding boxes by timestamp, in the view of a given camera.
        """
    def get_skeleton_by_timestamp_ns(self, device_timeStamp_ns: typing.SupportsInt, instance_id: typing.SupportsInt, time_query_options: projectaria_tools.core.sensor_data.TimeQueryOptions = ...) -> SkeletonFrameWithDt:
        """
        Query the skeleton frame by timestamp for a specific skeleton.
        """
    def get_skeleton_ids(self) -> list[int]:
        """
        get all instance ids as a vector whose `InstanceType == HUMAN`.
        """
    def get_skeleton_provider(self, instance_id: typing.SupportsInt) -> AriaDigitalTwinSkeletonProvider:
        """
        return the skeleton provider for a given human instance
        """
    def get_start_time_ns(self) -> int:
        """
        get the start time of the Aria poses in nanoseconds
        """
    def get_synthetic_image_by_timestamp_ns(self, device_timestamp_ns: typing.SupportsInt, stream_id: ..., time_query_options: projectaria_tools.core.sensor_data.TimeQueryOptions = ...) -> SyntheticDataWithDt:
        """
        Query a camera's synthetic image by timestamp
        """
    def get_timecode_from_device_time_ns(self, device_time_ns: typing.SupportsInt) -> int:
        """
         `adt_multiperson_tutorial.ipynb` for usage example.
        """
    def has_aria_3d_poses(self) -> bool:
        ...
    def has_aria_data(self) -> bool:
        ...
    def has_depth_images(self) -> bool:
        ...
    def has_eyegaze(self) -> bool:
        ...
    def has_instance_2d_boundingboxes(self) -> bool:
        ...
    def has_instance_id(self, instance_id: typing.SupportsInt) -> bool:
        """
        query if an instance exists in current data.
        """
    def has_instances_info(self) -> bool:
        ...
    def has_mps(self) -> bool:
        ...
    def has_object_3d_boundingboxes(self) -> bool:
        ...
    def has_segmentation_images(self) -> bool:
        ...
    def has_skeleton(self) -> bool:
        ...
    def has_synthetic_images(self) -> bool:
        ...
    def mps_data_provider_ptr(self) -> projectaria_tools.core.mps.MpsDataProvider:
        """
        return the MPS data provider
        """
    def raw_data_provider_ptr(self) -> projectaria_tools.core.data_provider.VrsDataProvider:
        """
        get a pointer to the raw data provider
        """
    def segmentation_data_provider_ptr(self) -> projectaria_tools.core.data_provider.VrsDataProvider:
        """
        get a pointer to the segmentation data provider
        """
    def synthetic_data_provider_ptr(self) -> projectaria_tools.core.data_provider.VrsDataProvider:
        """
        get a pointer to the synthetic data provider
        """
class AriaDigitalTwinSkeletonProvider:
    """
    Class for loading and accessing skeleton marker and joint information from an ADT sequence. Motive (the software running Optitrack) generates a frame of marker positions for eachcapture corresponding to each bodysuit in the scene. It then estimates the person's jointpositions for each of these marker frames. ADT converts these measurements to the Scene frame tobe consistent with all ground truth data and this class allows the user to load and query thatdata. We provide a separate class from the main AriaDigitalTwinDataProvider to separate out theskeleton loading and allow users to call this API without loading all other ADT data.
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    @staticmethod
    def get_joint_connections() -> list[tuple[int, int]]:
        """
        get the connections between joint IDs. (e.g, head id -> neck id)
        """
    @staticmethod
    def get_joint_labels() -> list[str]:
        """
        get the labels associated with each joint where the i^th element in the vector corresponds to joint Id i
        """
    @staticmethod
    def get_marker_labels() -> list[str]:
        """
        get the labels associated with each marker where the i^th element in the vector corresponds to maker Id i
        """
    def __init__(self, arg0: str) -> None:
        ...
    def get_skeleton_by_timestamp_ns(self, device_timestamp_ns: typing.SupportsInt, time_query_options: projectaria_tools.core.sensor_data.TimeQueryOptions = ...) -> SkeletonFrameWithDt:
        """
        Gets a skeleton frame by timestamp
        """
class AriaImageDataWithDt:
    """
    query result containing Aria image
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def data(self) -> projectaria_tools.core.sensor_data.ImageData:
        ...
    def dt_ns(self) -> int:
        ...
    def is_valid(self) -> bool:
        ...
class BoundingBox2dData:
    """
    a simple struct to represent a 2D bounding box for an instance
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def box_range(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float32], "[4, 1]"]:
        ...
    @box_range.setter
    def box_range(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float32, "[4, 1]"]) -> None:
        ...
    @property
    def visibility_ratio(self) -> float:
        ...
    @visibility_ratio.setter
    def visibility_ratio(self, arg0: typing.SupportsFloat) -> None:
        ...
class BoundingBox2dDataWithDt:
    """
    query result containing an instance 2D bounding box
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def data(self) -> dict[int, BoundingBox2dData]:
        ...
    def dt_ns(self) -> int:
        ...
    def is_valid(self) -> bool:
        ...
class BoundingBox3dData:
    """
    a simple struct to represent a 3D bounding box for an instance
    """
    transform_scene_object: SE3
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def aabb(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[6, 1]"]:
        ...
    @aabb.setter
    def aabb(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[6, 1]"]) -> None:
        ...
class BoundingBox3dDataWithDt:
    """
    query result containing an instance 3D bounding box
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def data(self) -> dict[int, BoundingBox3dData]:
        ...
    def dt_ns(self) -> int:
        ...
    def is_valid(self) -> bool:
        ...
class CanonicalPose:
    """
    Canonical pose defines the transformation so that prototypes in the category face a consistent direction
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __repr__(self) -> str:
        ...
    @property
    def front_vector(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        ...
    @front_vector.setter
    def front_vector(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> None:
        ...
    @property
    def up_vector(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        ...
    @up_vector.setter
    def up_vector(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> None:
        ...
class DepthData:
    """
    A class to represent depth image
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    def at(self, x: typing.SupportsInt, y: typing.SupportsInt) -> int:
        ...
    def get_height(self) -> int:
        ...
    def get_visualizable(self) -> projectaria_tools.core.image.ManagedImageU8:
        """
        Get stored image as 3-channel uint8 format
        """
    def get_width(self) -> int:
        ...
    def is_valid(self) -> bool:
        ...
    def to_numpy_array(self) -> numpy.typing.NDArray[numpy.float32] | numpy.typing.NDArray[numpy.uint8] | numpy.typing.NDArray[numpy.uint16] | numpy.typing.NDArray[numpy.uint64] | numpy.typing.NDArray[...]:
        ...
class DepthDataWithDt:
    """
    query result containing depth image
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def data(self) -> DepthData:
        ...
    def dt_ns(self) -> int:
        ...
    def is_valid(self) -> bool:
        ...
class EyeGazeWithDt:
    """
    query result containing eye gaze data
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def data(self) -> projectaria_tools.core.mps.EyeGaze:
        ...
    def dt_ns(self) -> int:
        ...
    def is_valid(self) -> bool:
        ...
class InstanceInfo:
    """
    A struct that represents the information of an instance, where an instance can either be a human or an object.
    """
    associated_device_serial: str
    canonical_pose: CanonicalPose
    category: str
    instance_type: InstanceType
    motion_type: MotionType
    name: str
    prototype_name: str
    rigidity_type: RigidityType
    rotational_symmetry: RotationalSymmetry
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __repr__(self) -> str:
        ...
    @property
    def category_uid(self) -> int:
        ...
    @category_uid.setter
    def category_uid(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def id(self) -> int:
        ...
    @id.setter
    def id(self, arg0: typing.SupportsInt) -> None:
        ...
class InstanceType:
    """
    Members:
    
      UNKNOWN
    
      OBJECT
    
      HUMAN
    """
    HUMAN: typing.ClassVar[InstanceType]  # value = <InstanceType.HUMAN: 2>
    OBJECT: typing.ClassVar[InstanceType]  # value = <InstanceType.OBJECT: 1>
    UNKNOWN: typing.ClassVar[InstanceType]  # value = <InstanceType.UNKNOWN: 0>
    __members__: typing.ClassVar[typing.Dict[str, InstanceType]]  # value = {'UNKNOWN': <InstanceType.UNKNOWN: 0>, 'OBJECT': <InstanceType.OBJECT: 1>, 'HUMAN': <InstanceType.HUMAN: 2>}
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
    def value(arg0: InstanceType) -> int:
        ...
class MotionType:
    """
    Members:
    
      UNKNOWN
    
      STATIC
    
      DYNAMIC
    """
    DYNAMIC: typing.ClassVar[MotionType]  # value = <MotionType.DYNAMIC: 2>
    STATIC: typing.ClassVar[MotionType]  # value = <MotionType.STATIC: 1>
    UNKNOWN: typing.ClassVar[MotionType]  # value = <MotionType.UNKNOWN: 0>
    __members__: typing.ClassVar[typing.Dict[str, MotionType]]  # value = {'UNKNOWN': <MotionType.UNKNOWN: 0>, 'STATIC': <MotionType.STATIC: 1>, 'DYNAMIC': <MotionType.DYNAMIC: 2>}
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
    def value(arg0: MotionType) -> int:
        ...
class RigidityType:
    """
    Members:
    
      UNKNOWN
    
      RIGID
    
      DEFORMABLE
    """
    DEFORMABLE: typing.ClassVar[RigidityType]  # value = <RigidityType.DEFORMABLE: 2>
    RIGID: typing.ClassVar[RigidityType]  # value = <RigidityType.RIGID: 1>
    UNKNOWN: typing.ClassVar[RigidityType]  # value = <RigidityType.UNKNOWN: 0>
    __members__: typing.ClassVar[typing.Dict[str, RigidityType]]  # value = {'UNKNOWN': <RigidityType.UNKNOWN: 0>, 'RIGID': <RigidityType.RIGID: 1>, 'DEFORMABLE': <RigidityType.DEFORMABLE: 2>}
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
    def value(arg0: RigidityType) -> int:
        ...
class RotationalSymmetry:
    """
    A struct representing the rotational symmetry properties of an instance
    """
    is_annotated: bool
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __repr__(self) -> str:
        ...
    @property
    def axes(self) -> list[RotationalSymmetryAxis]:
        ...
    @axes.setter
    def axes(self, arg0: collections.abc.Sequence[RotationalSymmetryAxis]) -> None:
        ...
class RotationalSymmetryAxis:
    """
    A struct representing the rotational symmetry axis of an instance
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __repr__(self) -> str:
        ...
    @property
    def angle_degree(self) -> float:
        ...
    @angle_degree.setter
    def angle_degree(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def axis(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        ...
    @axis.setter
    def axis(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> None:
        ...
class SegmentationData:
    """
    A class to represent segmentation image
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    def at(self, x: typing.SupportsInt, y: typing.SupportsInt) -> int:
        ...
    def get_height(self) -> int:
        ...
    def get_visualizable(self) -> projectaria_tools.core.image.ManagedImage3U8:
        """
        Get stored image as 3-channel uint8 format
        """
    def get_width(self) -> int:
        ...
    def is_valid(self) -> bool:
        ...
    def to_numpy_array(self) -> numpy.typing.NDArray[numpy.float32] | numpy.typing.NDArray[numpy.uint8] | numpy.typing.NDArray[numpy.uint16] | numpy.typing.NDArray[numpy.uint64] | numpy.typing.NDArray[...]:
        ...
class SegmentationDataWithDt:
    """
    query result containing segmentation image
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def data(self) -> SegmentationData:
        ...
    def dt_ns(self) -> int:
        ...
    def is_valid(self) -> bool:
        ...
class SkeletonFrame:
    """
    A simple struct to represent a frame of skeleton data
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def joints(self) -> list[typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]]:
        ...
    @joints.setter
    def joints(self, arg0: collections.abc.Sequence[typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]]) -> None:
        ...
    @property
    def markers(self) -> list[typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]]:
        ...
    @markers.setter
    def markers(self, arg0: collections.abc.Sequence[typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]]) -> None:
        ...
class SkeletonFrameWithDt:
    """
    query result containing skeleton frame data
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def data(self) -> SkeletonFrame:
        ...
    def dt_ns(self) -> int:
        ...
    def is_valid(self) -> bool:
        ...
class SyntheticData:
    """
    A class to represent synthetic image
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    def at(self, x: typing.SupportsInt, y: typing.SupportsInt, channel: typing.SupportsInt = ...) -> float | int | int | int | ...:
        ...
    def get_height(self) -> int:
        ...
    def get_visualizable(self) -> projectaria_tools.core.image.ImageU8 | ... | projectaria_tools.core.image.Image3U8 | ... | ... | ... | projectaria_tools.core.image.ImageU16 | ... | ... | ... | ... | ... | ... | ... | projectaria_tools.core.image.ImageF32 | ... | ... | ... | projectaria_tools.core.image.ImageU64:
        """
        Get stored image as an image variant
        """
    def get_width(self) -> int:
        ...
    def is_valid(self) -> bool:
        ...
    def to_numpy_array(self) -> numpy.typing.NDArray[numpy.float32] | numpy.typing.NDArray[numpy.uint8] | numpy.typing.NDArray[numpy.uint16] | numpy.typing.NDArray[numpy.uint64] | numpy.typing.NDArray[...]:
        ...
class SyntheticDataWithDt:
    """
    query result containing synthetic image
    """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def data(self) -> SyntheticData:
        ...
    def dt_ns(self) -> int:
        ...
    def is_valid(self) -> bool:
        ...
def bbox2d_to_image_coordinates(bbox: typing.Annotated[numpy.typing.ArrayLike, numpy.float32, "[4, 1]"]) -> list[typing.Annotated[numpy.typing.NDArray[numpy.float64], "[2, 1]"]]:
    """
    helper function to convert a 2D bounding box [xmin, xmax, ymin, ymax] to the 4 image coordinates [(x1, y1), (x2, y2), (x3, y3), (x4, y4)]
    """
def bbox2d_to_image_line_coordinates(bbox: typing.Annotated[numpy.typing.ArrayLike, numpy.float32, "[4, 1]"]) -> list[typing.Annotated[numpy.typing.NDArray[numpy.float64], "[2, 1]"]]:
    """
    helper function to convert a 2D bounding box [xmin, xmax, ymin, ymax] to the 5 coordinates that draw the lines in the image completing the full bounding box [(x1, y1), (x2, y2), (x3, y3), (x4, y4), (x1, y1)]
    """
def bbox3d_to_coordinates(bbox: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[6, 1]"]) -> list[typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]]:
    """
    helper function to convert a 3d bounding box [xmin, xmax, ymin, ymax, zmin, zmax] to the 8 corner coordinates in the object frame [b1, b2, b3, b4, t1, t2, t3, t4] where b is for bottom and t is for top
    """
def bbox3d_to_line_coordinates(bbox: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[6, 1]"]) -> list[typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]]:
    """
    helper function to convert a 3d bounding box [xmin, xmax, ymin, ymax, zmin, zmax] to the 16 coordinates that draw the lines completing the full bounding box [b1, b2, b3, b4, b1, t1, t2, t3, t4, t1, t2, b2, b3, t3, t4, b4] where b is for bottom and t is for top
    """
def get_interpolated_aria_3d_pose_at_timestamp_ns(provider: AriaDigitalTwinDataProvider, device_time_stamp_ns: typing.SupportsInt) -> Aria3dPoseDataWithDt:
    """
    helper function to return an interpolated Aria3dPose given a query timestamp
    """
def get_interpolated_object_3d_boundingboxes_at_timestamp_ns(provider: AriaDigitalTwinDataProvider, device_time_stamp_ns: typing.SupportsInt) -> BoundingBox3dDataWithDt:
    """
    helper function to return an interpolated object 3D bounding box given a query timestamp
    """
def is_dataset_corrupt(arg0: str) -> bool:
    ...
DEFORMABLE: RigidityType  # value = <RigidityType.DEFORMABLE: 2>
DYNAMIC: MotionType  # value = <MotionType.DYNAMIC: 2>
HUMAN: InstanceType  # value = <InstanceType.HUMAN: 2>
OBJECT: InstanceType  # value = <InstanceType.OBJECT: 1>
RIGID: RigidityType  # value = <RigidityType.RIGID: 1>
STATIC: MotionType  # value = <MotionType.STATIC: 1>
UNKNOWN: MotionType  # value = <MotionType.UNKNOWN: 0>
