from __future__ import annotations
import projectaria_tools.core.sensor_data
import typing
__all__ = ['ERR_FFMPEG', 'ERR_INVALID_FRAME', 'ERR_MUX_FAILURE', 'ERR_NOT_INITIALIZED', 'ERR_NO_FRAME', 'ERR_SYSTEM', 'H264', 'H265', 'IVideoDecoder', 'OK', 'VP9', 'VideoCodec', 'VideoCodecFormat', 'XprsResult', 'createDecoder']
class IVideoDecoder:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def decode_oss_frame(self, arg0: projectaria_tools.core.sensor_data.ImageData) -> bool:
        ...
    def init(self, arg0: bool) -> XprsResult:
        ...
class VideoCodec:
    format: VideoCodecFormat
    hw_accel: bool
    implementation_name: str
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
class VideoCodecFormat:
    """
    Members:
    
      H264
    
      H265
    
      VP9
    """
    H264: typing.ClassVar[VideoCodecFormat]  # value = <VideoCodecFormat.H264: 0>
    H265: typing.ClassVar[VideoCodecFormat]  # value = <VideoCodecFormat.H265: 1>
    VP9: typing.ClassVar[VideoCodecFormat]  # value = <VideoCodecFormat.VP9: 2>
    __members__: typing.ClassVar[typing.Dict[str, VideoCodecFormat]]  # value = {'H264': <VideoCodecFormat.H264: 0>, 'H265': <VideoCodecFormat.H265: 1>, 'VP9': <VideoCodecFormat.VP9: 2>}
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
    def value(arg0: VideoCodecFormat) -> int:
        ...
class XprsResult:
    """
    Members:
    
      OK
    
      ERR_NOT_INITIALIZED
    
      ERR_INVALID_FRAME
    
      ERR_NO_FRAME
    
      ERR_FFMPEG
    
      ERR_SYSTEM
    
      ERR_MUX_FAILURE
    """
    ERR_FFMPEG: typing.ClassVar[XprsResult]  # value = <XprsResult.ERR_FFMPEG: -6>
    ERR_INVALID_FRAME: typing.ClassVar[XprsResult]  # value = <XprsResult.ERR_INVALID_FRAME: -8>
    ERR_MUX_FAILURE: typing.ClassVar[XprsResult]  # value = <XprsResult.ERR_MUX_FAILURE: -11>
    ERR_NOT_INITIALIZED: typing.ClassVar[XprsResult]  # value = <XprsResult.ERR_NOT_INITIALIZED: -7>
    ERR_NO_FRAME: typing.ClassVar[XprsResult]  # value = <XprsResult.ERR_NO_FRAME: -4>
    ERR_SYSTEM: typing.ClassVar[XprsResult]  # value = <XprsResult.ERR_SYSTEM: -5>
    OK: typing.ClassVar[XprsResult]  # value = <XprsResult.OK: 0>
    __members__: typing.ClassVar[typing.Dict[str, XprsResult]]  # value = {'OK': <XprsResult.OK: 0>, 'ERR_NOT_INITIALIZED': <XprsResult.ERR_NOT_INITIALIZED: -7>, 'ERR_INVALID_FRAME': <XprsResult.ERR_INVALID_FRAME: -8>, 'ERR_NO_FRAME': <XprsResult.ERR_NO_FRAME: -4>, 'ERR_FFMPEG': <XprsResult.ERR_FFMPEG: -6>, 'ERR_SYSTEM': <XprsResult.ERR_SYSTEM: -5>, 'ERR_MUX_FAILURE': <XprsResult.ERR_MUX_FAILURE: -11>}
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
    def value(arg0: XprsResult) -> int:
        ...
def createDecoder(codec: VideoCodec) -> IVideoDecoder:
    ...
ERR_FFMPEG: XprsResult  # value = <XprsResult.ERR_FFMPEG: -6>
ERR_INVALID_FRAME: XprsResult  # value = <XprsResult.ERR_INVALID_FRAME: -8>
ERR_MUX_FAILURE: XprsResult  # value = <XprsResult.ERR_MUX_FAILURE: -11>
ERR_NOT_INITIALIZED: XprsResult  # value = <XprsResult.ERR_NOT_INITIALIZED: -7>
ERR_NO_FRAME: XprsResult  # value = <XprsResult.ERR_NO_FRAME: -4>
ERR_SYSTEM: XprsResult  # value = <XprsResult.ERR_SYSTEM: -5>
H264: VideoCodecFormat  # value = <VideoCodecFormat.H264: 0>
H265: VideoCodecFormat  # value = <VideoCodecFormat.H265: 1>
OK: XprsResult  # value = <XprsResult.OK: 0>
VP9: VideoCodecFormat  # value = <VideoCodecFormat.VP9: 2>
