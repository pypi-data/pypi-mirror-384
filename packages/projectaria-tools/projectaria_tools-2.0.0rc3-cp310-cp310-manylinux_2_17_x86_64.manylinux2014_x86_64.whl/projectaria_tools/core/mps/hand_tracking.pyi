from __future__ import annotations
import datetime
import typing
__all__ = ['HandLandmark', 'HandTrackingResult', 'Handedness', 'INDEX_DISTAL', 'INDEX_FINGERTIP', 'INDEX_INTERMEDIATE', 'INDEX_PROXIMAL', 'MIDDLE_DISTAL', 'MIDDLE_FINGERTIP', 'MIDDLE_INTERMEDIATE', 'MIDDLE_PROXIMAL', 'NUM_LANDMARKS', 'PALM_CENTER', 'PINKY_DISTAL', 'PINKY_FINGERTIP', 'PINKY_INTERMEDIATE', 'PINKY_PROXIMAL', 'RING_DISTAL', 'RING_FINGERTIP', 'RING_INTERMEDIATE', 'RING_PROXIMAL', 'THUMB_DISTAL', 'THUMB_FINGERTIP', 'THUMB_INTERMEDIATE', 'WRIST', 'WristAndPalmPose', 'kHandJointConnections', 'kNumHandJointConnections', 'kNumHandLandmarks', 'read_hand_tracking_results', 'read_wrist_and_palm_poses']
class HandLandmark:
    """
    Members:
    
      THUMB_FINGERTIP
    
      INDEX_FINGERTIP
    
      MIDDLE_FINGERTIP
    
      RING_FINGERTIP
    
      PINKY_FINGERTIP
    
      WRIST
    
      THUMB_INTERMEDIATE
    
      THUMB_DISTAL
    
      INDEX_PROXIMAL
    
      INDEX_INTERMEDIATE
    
      INDEX_DISTAL
    
      MIDDLE_PROXIMAL
    
      MIDDLE_INTERMEDIATE
    
      MIDDLE_DISTAL
    
      RING_PROXIMAL
    
      RING_INTERMEDIATE
    
      RING_DISTAL
    
      PINKY_PROXIMAL
    
      PINKY_INTERMEDIATE
    
      PINKY_DISTAL
    
      PALM_CENTER
    
      NUM_LANDMARKS
    """
    INDEX_DISTAL: typing.ClassVar[HandLandmark]  # value = <HandLandmark.INDEX_DISTAL: 10>
    INDEX_FINGERTIP: typing.ClassVar[HandLandmark]  # value = <HandLandmark.INDEX_FINGERTIP: 1>
    INDEX_INTERMEDIATE: typing.ClassVar[HandLandmark]  # value = <HandLandmark.INDEX_INTERMEDIATE: 9>
    INDEX_PROXIMAL: typing.ClassVar[HandLandmark]  # value = <HandLandmark.INDEX_PROXIMAL: 8>
    MIDDLE_DISTAL: typing.ClassVar[HandLandmark]  # value = <HandLandmark.MIDDLE_DISTAL: 13>
    MIDDLE_FINGERTIP: typing.ClassVar[HandLandmark]  # value = <HandLandmark.MIDDLE_FINGERTIP: 2>
    MIDDLE_INTERMEDIATE: typing.ClassVar[HandLandmark]  # value = <HandLandmark.MIDDLE_INTERMEDIATE: 12>
    MIDDLE_PROXIMAL: typing.ClassVar[HandLandmark]  # value = <HandLandmark.MIDDLE_PROXIMAL: 11>
    NUM_LANDMARKS: typing.ClassVar[HandLandmark]  # value = <HandLandmark.NUM_LANDMARKS: 21>
    PALM_CENTER: typing.ClassVar[HandLandmark]  # value = <HandLandmark.PALM_CENTER: 20>
    PINKY_DISTAL: typing.ClassVar[HandLandmark]  # value = <HandLandmark.PINKY_DISTAL: 19>
    PINKY_FINGERTIP: typing.ClassVar[HandLandmark]  # value = <HandLandmark.PINKY_FINGERTIP: 4>
    PINKY_INTERMEDIATE: typing.ClassVar[HandLandmark]  # value = <HandLandmark.PINKY_INTERMEDIATE: 18>
    PINKY_PROXIMAL: typing.ClassVar[HandLandmark]  # value = <HandLandmark.PINKY_PROXIMAL: 17>
    RING_DISTAL: typing.ClassVar[HandLandmark]  # value = <HandLandmark.RING_DISTAL: 16>
    RING_FINGERTIP: typing.ClassVar[HandLandmark]  # value = <HandLandmark.RING_FINGERTIP: 3>
    RING_INTERMEDIATE: typing.ClassVar[HandLandmark]  # value = <HandLandmark.RING_INTERMEDIATE: 15>
    RING_PROXIMAL: typing.ClassVar[HandLandmark]  # value = <HandLandmark.RING_PROXIMAL: 14>
    THUMB_DISTAL: typing.ClassVar[HandLandmark]  # value = <HandLandmark.THUMB_DISTAL: 7>
    THUMB_FINGERTIP: typing.ClassVar[HandLandmark]  # value = <HandLandmark.THUMB_FINGERTIP: 0>
    THUMB_INTERMEDIATE: typing.ClassVar[HandLandmark]  # value = <HandLandmark.THUMB_INTERMEDIATE: 6>
    WRIST: typing.ClassVar[HandLandmark]  # value = <HandLandmark.WRIST: 5>
    __members__: typing.ClassVar[typing.Dict[str, HandLandmark]]  # value = {'THUMB_FINGERTIP': <HandLandmark.THUMB_FINGERTIP: 0>, 'INDEX_FINGERTIP': <HandLandmark.INDEX_FINGERTIP: 1>, 'MIDDLE_FINGERTIP': <HandLandmark.MIDDLE_FINGERTIP: 2>, 'RING_FINGERTIP': <HandLandmark.RING_FINGERTIP: 3>, 'PINKY_FINGERTIP': <HandLandmark.PINKY_FINGERTIP: 4>, 'WRIST': <HandLandmark.WRIST: 5>, 'THUMB_INTERMEDIATE': <HandLandmark.THUMB_INTERMEDIATE: 6>, 'THUMB_DISTAL': <HandLandmark.THUMB_DISTAL: 7>, 'INDEX_PROXIMAL': <HandLandmark.INDEX_PROXIMAL: 8>, 'INDEX_INTERMEDIATE': <HandLandmark.INDEX_INTERMEDIATE: 9>, 'INDEX_DISTAL': <HandLandmark.INDEX_DISTAL: 10>, 'MIDDLE_PROXIMAL': <HandLandmark.MIDDLE_PROXIMAL: 11>, 'MIDDLE_INTERMEDIATE': <HandLandmark.MIDDLE_INTERMEDIATE: 12>, 'MIDDLE_DISTAL': <HandLandmark.MIDDLE_DISTAL: 13>, 'RING_PROXIMAL': <HandLandmark.RING_PROXIMAL: 14>, 'RING_INTERMEDIATE': <HandLandmark.RING_INTERMEDIATE: 15>, 'RING_DISTAL': <HandLandmark.RING_DISTAL: 16>, 'PINKY_PROXIMAL': <HandLandmark.PINKY_PROXIMAL: 17>, 'PINKY_INTERMEDIATE': <HandLandmark.PINKY_INTERMEDIATE: 18>, 'PINKY_DISTAL': <HandLandmark.PINKY_DISTAL: 19>, 'PALM_CENTER': <HandLandmark.PALM_CENTER: 20>, 'NUM_LANDMARKS': <HandLandmark.NUM_LANDMARKS: 21>}
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
    def value(arg0: HandLandmark) -> int:
        ...
class HandTrackingResult:
    """
    An object representing hand tracking output at a single timestamp.
    """
    left_hand: ... | None
    right_hand: ... | None
    tracking_timestamp: datetime.timedelta
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    def __repr__(self) -> str:
        ...
class Handedness:
    """
    Members:
    
      LEFT
    
      RIGHT
    """
    LEFT: typing.ClassVar[Handedness]  # value = <Handedness.LEFT: 0>
    RIGHT: typing.ClassVar[Handedness]  # value = <Handedness.RIGHT: 1>
    __members__: typing.ClassVar[typing.Dict[str, Handedness]]  # value = {'LEFT': <Handedness.LEFT: 0>, 'RIGHT': <Handedness.RIGHT: 1>}
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
    def value(arg0: Handedness) -> int:
        ...
class WristAndPalmPose:
    """
    An object representing WristAndPalmPose output at a single timestamp.
    """
    left_hand: ... | None
    right_hand: ... | None
    tracking_timestamp: datetime.timedelta
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    def __repr__(self) -> str:
        ...
def read_hand_tracking_results(path: str) -> list[HandTrackingResult]:
    """
    Read hand tracking results from the hand tracking output generated via MPS.
        Parameters
        __________
        path: Path to the hand tracking results csv file.
    """
def read_wrist_and_palm_poses(path: str) -> list[WristAndPalmPose]:
    """
    Read Wrist and Palm poses from the hand tracking output generated via MPS.
        Parameters
        __________
        path: Path to the wrist and palm poses csv file.
    """
INDEX_DISTAL: HandLandmark  # value = <HandLandmark.INDEX_DISTAL: 10>
INDEX_FINGERTIP: HandLandmark  # value = <HandLandmark.INDEX_FINGERTIP: 1>
INDEX_INTERMEDIATE: HandLandmark  # value = <HandLandmark.INDEX_INTERMEDIATE: 9>
INDEX_PROXIMAL: HandLandmark  # value = <HandLandmark.INDEX_PROXIMAL: 8>
MIDDLE_DISTAL: HandLandmark  # value = <HandLandmark.MIDDLE_DISTAL: 13>
MIDDLE_FINGERTIP: HandLandmark  # value = <HandLandmark.MIDDLE_FINGERTIP: 2>
MIDDLE_INTERMEDIATE: HandLandmark  # value = <HandLandmark.MIDDLE_INTERMEDIATE: 12>
MIDDLE_PROXIMAL: HandLandmark  # value = <HandLandmark.MIDDLE_PROXIMAL: 11>
NUM_LANDMARKS: HandLandmark  # value = <HandLandmark.NUM_LANDMARKS: 21>
PALM_CENTER: HandLandmark  # value = <HandLandmark.PALM_CENTER: 20>
PINKY_DISTAL: HandLandmark  # value = <HandLandmark.PINKY_DISTAL: 19>
PINKY_FINGERTIP: HandLandmark  # value = <HandLandmark.PINKY_FINGERTIP: 4>
PINKY_INTERMEDIATE: HandLandmark  # value = <HandLandmark.PINKY_INTERMEDIATE: 18>
PINKY_PROXIMAL: HandLandmark  # value = <HandLandmark.PINKY_PROXIMAL: 17>
RING_DISTAL: HandLandmark  # value = <HandLandmark.RING_DISTAL: 16>
RING_FINGERTIP: HandLandmark  # value = <HandLandmark.RING_FINGERTIP: 3>
RING_INTERMEDIATE: HandLandmark  # value = <HandLandmark.RING_INTERMEDIATE: 15>
RING_PROXIMAL: HandLandmark  # value = <HandLandmark.RING_PROXIMAL: 14>
THUMB_DISTAL: HandLandmark  # value = <HandLandmark.THUMB_DISTAL: 7>
THUMB_FINGERTIP: HandLandmark  # value = <HandLandmark.THUMB_FINGERTIP: 0>
THUMB_INTERMEDIATE: HandLandmark  # value = <HandLandmark.THUMB_INTERMEDIATE: 6>
WRIST: HandLandmark  # value = <HandLandmark.WRIST: 5>
kHandJointConnections: list  # value = [(<HandLandmark.WRIST: 5>, <HandLandmark.PINKY_PROXIMAL: 17>), (<HandLandmark.PINKY_PROXIMAL: 17>, <HandLandmark.PINKY_INTERMEDIATE: 18>), (<HandLandmark.PINKY_INTERMEDIATE: 18>, <HandLandmark.PINKY_DISTAL: 19>), (<HandLandmark.PINKY_DISTAL: 19>, <HandLandmark.PINKY_FINGERTIP: 4>), (<HandLandmark.WRIST: 5>, <HandLandmark.RING_PROXIMAL: 14>), (<HandLandmark.RING_PROXIMAL: 14>, <HandLandmark.RING_INTERMEDIATE: 15>), (<HandLandmark.RING_INTERMEDIATE: 15>, <HandLandmark.RING_DISTAL: 16>), (<HandLandmark.RING_DISTAL: 16>, <HandLandmark.RING_FINGERTIP: 3>), (<HandLandmark.WRIST: 5>, <HandLandmark.MIDDLE_PROXIMAL: 11>), (<HandLandmark.MIDDLE_PROXIMAL: 11>, <HandLandmark.MIDDLE_INTERMEDIATE: 12>), (<HandLandmark.MIDDLE_INTERMEDIATE: 12>, <HandLandmark.MIDDLE_DISTAL: 13>), (<HandLandmark.MIDDLE_DISTAL: 13>, <HandLandmark.MIDDLE_FINGERTIP: 2>), (<HandLandmark.WRIST: 5>, <HandLandmark.INDEX_PROXIMAL: 8>), (<HandLandmark.INDEX_PROXIMAL: 8>, <HandLandmark.INDEX_INTERMEDIATE: 9>), (<HandLandmark.INDEX_INTERMEDIATE: 9>, <HandLandmark.INDEX_DISTAL: 10>), (<HandLandmark.INDEX_DISTAL: 10>, <HandLandmark.INDEX_FINGERTIP: 1>), (<HandLandmark.WRIST: 5>, <HandLandmark.THUMB_INTERMEDIATE: 6>), (<HandLandmark.THUMB_INTERMEDIATE: 6>, <HandLandmark.THUMB_DISTAL: 7>), (<HandLandmark.THUMB_DISTAL: 7>, <HandLandmark.THUMB_FINGERTIP: 0>), (<HandLandmark.THUMB_INTERMEDIATE: 6>, <HandLandmark.INDEX_PROXIMAL: 8>), (<HandLandmark.INDEX_PROXIMAL: 8>, <HandLandmark.MIDDLE_PROXIMAL: 11>), (<HandLandmark.MIDDLE_PROXIMAL: 11>, <HandLandmark.RING_PROXIMAL: 14>), (<HandLandmark.RING_PROXIMAL: 14>, <HandLandmark.PINKY_PROXIMAL: 17>)]
kNumHandJointConnections: int = 23
kNumHandLandmarks: int = 21
