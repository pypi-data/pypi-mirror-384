from enum import IntEnum, auto
from typing import TYPE_CHECKING, Annotated, Any, Dict, Generic, Literal, Optional, TypeVar, Union

from pydantic import BaseModel, Field, field_validator
from typing_extensions import TypeAliasType

from ._base import Device

FFMPEG_OUTPUT_8BIT = '-vf "scale=out_color_matrix=bt709:out_range=full,format=bgr24,scale=out_range=full" -c:v h264_nvenc -pix_fmt yuv420p -color_range full -colorspace bt709 -color_trc linear -tune hq -preset p4 -rc vbr -cq 12 -b:v 0M -metadata author="Allen Institute for Neural Dynamics" -maxrate 700M -bufsize 350M'
""" Default output arguments for 8-bit video encoding """

FFMPEG_OUTPUT_16BIT = '-vf "scale=out_color_matrix=bt709:out_range=full,format=rgb48le,scale=out_range=full" -c:v hevc_nvenc -pix_fmt p010le -color_range full -colorspace bt709 -color_trc linear -tune hq -preset p4 -rc vbr -cq 12 -b:v 0M -metadata author="Allen Institute for Neural Dynamics" -maxrate 700M -bufsize 350M'
""" Default output arguments for 16-bit video encoding """

FFMPEG_INPUT = "-colorspace bt709 -color_primaries bt709 -color_range full -color_trc linear"
""" Default input arguments """


class VideoWriterFfmpeg(BaseModel):
    video_writer_type: Literal["FFMPEG"] = Field(default="FFMPEG")
    frame_rate: int = Field(default=30, ge=0, description="Encoding frame rate")
    container_extension: str = Field(default="mp4", description="Container extension")
    output_arguments: str = Field(
        default=FFMPEG_OUTPUT_8BIT,
        description="Output arguments",
    )
    input_arguments: str = Field(
        default=FFMPEG_INPUT,
        description="Input arguments",
    )


class VideoWriterOpenCv(BaseModel):
    video_writer_type: Literal["OPENCV"] = Field(default="OPENCV")
    frame_rate: int = Field(default=30, ge=0, description="Encoding frame rate")
    container_extension: str = Field(default="avi", description="Container extension")
    four_cc: str = Field(default="FMP4", description="Four character code")


if TYPE_CHECKING:
    VideoWriter = Union[VideoWriterFfmpeg, VideoWriterOpenCv]
else:
    VideoWriter = TypeAliasType(
        "VideoWriter", Annotated[Union[VideoWriterFfmpeg, VideoWriterOpenCv], Field(discriminator="video_writer_type")]
    )


class VideoWriterFfmpegFactory:
    def __init__(self, bit_depth: Literal[8, 16] = 8, video_writer_ffmpeg_kwargs: Dict[str, Any] = None):
        self._bit_depth = bit_depth
        self.video_writer_ffmpeg_kwargs = video_writer_ffmpeg_kwargs or {}
        self._output_arguments: str
        self._input_arguments: str
        self._solve_strings()

    def _solve_strings(self):
        if self._bit_depth == 8:
            self._output_arguments = FFMPEG_OUTPUT_8BIT
        elif self._bit_depth == 16:
            self._output_arguments = FFMPEG_OUTPUT_16BIT
        else:
            raise ValueError(f"Bit depth {self._bit_depth} not supported")
        self._input_arguments = FFMPEG_INPUT

    def construct_video_writer_ffmpeg(self) -> VideoWriterFfmpeg:
        return VideoWriterFfmpeg(
            output_arguments=self._output_arguments,
            input_arguments=self._input_arguments,
            **self.video_writer_ffmpeg_kwargs,
        )

    def update_video_writer_ffmpeg_kwargs(self, video_writer: VideoWriterFfmpeg):
        return video_writer.model_copy(
            update={"output_arguments": self._output_arguments, "input_arguments": self._input_arguments}
        )


class WebCamera(Device):
    device_type: Literal["WebCamera"] = Field(default="WebCamera", description="Device type")
    index: int = Field(default=0, ge=0, description="Camera index")
    video_writer: Optional[VideoWriter] = Field(
        default=None, description="Video writer. If not provided, no video will be saved."
    )


class Point2f(BaseModel):
    x: float = Field(description="X coordinate of the point (px)")
    y: float = Field(description="Y coordinate of the point (px)")


class Rect(BaseModel):
    x: int = Field(default=0, ge=0, description="X coordinate of the top-left corner")
    y: int = Field(default=0, ge=0, description="Y coordinate of the top-left corner")
    width: int = Field(default=0, ge=0, description="Width of the rectangle")
    height: int = Field(default=0, ge=0, description="Height of the rectangle")


class Circle(BaseModel):
    center: Point2f = Field(default=Point2f(x=0, y=0), description="Center of the circle (px)", validate_default=True)
    radius: float = Field(default=1, ge=0, description="Radius of the circle (px)")


class SpinnakerCameraAdcBitDepth(IntEnum):
    ADC8BIT = 0
    ADC10BIT = 1
    ADC12BIT = 2


class SpinnakerCameraPixelFormat(IntEnum):
    MONO8 = 0
    MONO16 = auto()
    RGB8PACKED = auto()
    BAYERGR8 = auto()
    BAYERRG8 = auto()
    BAYERGB8 = auto()
    BAYERBG8 = auto()
    BAYERGR16 = auto()
    BAYERRG16 = auto()
    BAYERGB16 = auto()
    BAYERBG16 = auto()
    MONO12PACKED = auto()
    BAYERGR12PACKED = auto()
    BAYERRG12PACKED = auto()
    BAYERGB12PACKED = auto()
    BAYERBG12PACKED = auto()
    YUV411PACKED = auto()
    YUV422PACKED = auto()
    YUV444PACKED = auto()
    MONO12P = auto()
    BAYERGR12P = auto()
    BAYERRG12P = auto()
    BAYERGB12P = auto()
    BAYERBG12P = auto()
    YCBCR8 = auto()
    YCBCR422_8 = auto()
    YCBCR411_8 = auto()
    BGR8 = auto()
    BGRA8 = auto()
    MONO10PACKED = auto()
    BAYERGR10PACKED = auto()
    BAYERRG10PACKED = auto()
    BAYERGB10PACKED = auto()
    BAYERBG10PACKED = auto()
    MONO10P = auto()
    BAYERGR10P = auto()
    BAYERRG10P = auto()
    BAYERGB10P = auto()
    BAYERBG10P = auto()
    MONO1P = auto()
    MONO2P = auto()
    MONO4P = auto()
    MONO8S = auto()
    MONO10 = auto()
    MONO12 = auto()
    MONO14 = auto()
    MONO16S = auto()
    MONO32F = auto()
    BAYERBG10 = auto()
    BAYERBG12 = auto()
    BAYERGB10 = auto()
    BAYERGB12 = auto()
    BAYERGR10 = auto()
    BAYERGR12 = auto()
    BAYERRG10 = auto()
    BAYERRG12 = auto()
    RGBA8 = auto()
    RGBA10 = auto()
    RGBA10P = auto()
    RGBA12 = auto()
    RGBA12P = auto()
    RGBA14 = auto()
    RGBA16 = auto()
    RGB8 = auto()
    RGB8_PLANAR = auto()
    RGB10 = auto()
    RGB10_PLANAR = auto()
    RGB10P = auto()
    RGB10P32 = auto()
    RGB12 = auto()
    RGB12_PLANAR = auto()
    RGB12P = auto()
    RGB14 = auto()
    RGB16 = auto()
    RGB16S = auto()
    RGB32F = auto()
    RGB16_PLANAR = auto()
    RGB565P = auto()
    BGRA10 = auto()
    BGRA10P = auto()
    BGRA12 = auto()
    BGRA12P = auto()
    BGRA14 = auto()
    BGRA16 = auto()
    RGBA32F = auto()
    BGR10 = auto()
    BGR10P = auto()
    BGR12 = auto()
    BGR12P = auto()
    BGR14 = auto()
    BGR16 = auto()
    BGR565P = auto()
    R8 = auto()
    R10 = auto()
    R12 = auto()
    R16 = auto()
    G8 = auto()
    G10 = auto()
    G12 = auto()
    G16 = auto()
    B8 = auto()
    B10 = auto()
    B12 = auto()
    B16 = auto()
    COORD3D_ABC8 = auto()
    COORD3D_ABC8_PLANAR = auto()
    COORD3D_ABC10P = auto()
    COORD3D_ABC10P_PLANAR = auto()
    COORD3D_ABC12P = auto()
    COORD3D_ABC12P_PLANAR = auto()
    COORD3D_ABC16 = auto()
    COORD3D_ABC16_PLANAR = auto()
    COORD3D_ABC32F = auto()
    COORD3D_ABC32F_PLANAR = auto()
    COORD3D_AC8 = auto()
    COORD3D_AC8_PLANAR = auto()
    COORD3D_AC10P = auto()
    COORD3D_AC10P_PLANAR = auto()
    COORD3D_AC12P = auto()
    COORD3D_AC12P_PLANAR = auto()
    COORD3D_AC16 = auto()
    COORD3D_AC16_PLANAR = auto()
    COORD3D_AC32F = auto()
    COORD3D_AC32F_PLANAR = auto()
    COORD3D_A8 = auto()
    COORD3D_A10P = auto()
    COORD3D_A12P = auto()
    COORD3D_A16 = auto()
    COORD3D_A32F = auto()
    COORD3D_B8 = auto()
    COORD3D_B10P = auto()
    COORD3D_B12P = auto()
    COORD3D_B16 = auto()
    COORD3D_B32F = auto()
    COORD3D_C8 = auto()
    COORD3D_C10P = auto()
    COORD3D_C12P = auto()
    COORD3D_C16 = auto()
    COORD3D_C32F = auto()
    CONFIDENCE1 = auto()
    CONFIDENCE1P = auto()
    CONFIDENCE8 = auto()
    CONFIDENCE16 = auto()
    CONFIDENCE32F = auto()


class SpinnakerCamera(Device):
    device_type: Literal["SpinnakerCamera"] = Field(default="SpinnakerCamera", description="Device type")
    serial_number: str = Field(..., description="Camera serial number")
    binning: int = Field(default=1, ge=1, description="Binning")
    color_processing: Literal["Default", "NoColorProcessing"] = Field(default="Default", description="Color processing")
    exposure: int = Field(default=1000, ge=100, description="Exposure time")
    gain: float = Field(default=0, ge=0, description="Gain")
    gamma: Optional[float] = Field(default=None, ge=0, description="Gamma. If None, will disable gamma correction.")
    adc_bit_depth: Optional[SpinnakerCameraAdcBitDepth] = Field(
        default=SpinnakerCameraAdcBitDepth.ADC8BIT, description="ADC bit depth. If None will be left as default."
    )
    pixel_format: Optional[SpinnakerCameraPixelFormat] = Field(
        default=SpinnakerCameraPixelFormat.MONO8, description="Pixel format. If None will be left as default."
    )
    region_of_interest: Rect = Field(default=Rect(), description="Region of interest", validate_default=True)
    video_writer: Optional[VideoWriter] = Field(
        default=None, description="Video writer. If not provided, no video will be saved."
    )

    @field_validator("region_of_interest")
    @classmethod
    def validate_roi(cls, v: Rect) -> Rect:
        if v.width == 0 or v.height == 0:
            if any([x != 0 for x in [v.width, v.height, v.x, v.y]]):
                raise ValueError("If width or height is 0, all other values must be 0")
        return v


CameraTypes = Union[WebCamera, SpinnakerCamera]
TCamera = TypeVar("TCamera", bound=CameraTypes)


class CameraController(Device, Generic[TCamera]):
    device_type: Literal["CameraController"] = "CameraController"
    cameras: Dict[str, TCamera] = Field(..., description="Cameras to be instantiated")
    frame_rate: Optional[int] = Field(default=30, ge=0, description="Frame rate of the trigger to all cameras")
