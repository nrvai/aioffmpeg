import asyncio

from typing import Any, AsyncGenerator, Optional, Self

from . import ffmpeg
from .source import Source, rtsp


__all__ = (
    "VideoFormat",
    "VideoStream",

    "calculate_frame_size",
    "get_color_channels"
)


class VideoFormat:
    width: int
    height: int
    pixel_format: str

    def __init__(
        self: Self,
        *,
        width: int,
        height: int,
        pixel_format: str
    ) -> None:
        self.width = width
        self.height = height
        self.pixel_format = pixel_format


def _build_ffmpeg_arguments(
    source: Source,
    video_format: VideoFormat,
    filters: Optional[str]
) -> list[str]:
    url = str(source.url())
    arguments = []

    match source:
        case rtsp.Source():
            arguments.extend([
                "-rtsp_transport",
                source.transport.name.lower()
            ])
        case _:
            raise NotImplementedError

    arguments.extend([
        "-i",
        url,
        "-f",
        "rawvideo",
        "-pix_fmt",
        video_format.pixel_format
    ])

    if filters:
        arguments.extend([
            "-vf",
            f"\"{filters}\""
        ])

    arguments.extend([
        "-an",
        "-sn",
        "pipe:1"
    ])

    return arguments


def get_color_channels(pixel_format: str) -> int:
    match pixel_format:
        case "rgba":
            return 4
        case "rgb24" | "bgr24":
            return 3
        case "gray":
            return 1
        case _:
            raise NotImplementedError


def calculate_frame_size(video_format: VideoFormat) -> int:
    channels = get_color_channels(video_format.pixel_format)

    return video_format.width * video_format.height * channels


class VideoStream:
    source: Source
    video_format: VideoFormat
    filters: Optional[str]

    _process: Optional[asyncio.subprocess.Process]
    _lock: asyncio.Lock

    def __init__(
        self: Self,
        *,
        source: Source,
        video_format: VideoFormat,
        filters: Optional[str] = None
    ) -> None:
        self.source = source
        self.video_format = video_format
        self.filters = filters

        self._process = None
        self._lock = asyncio.Lock()

    async def __aenter__(self: Self) -> Self:
        await self.open()

        return self

    async def __aexit__(self: Self, *args: Any) -> None:
        await self.close()

    async def open(self: Self) -> None:
        async with self._lock:
            assert self._process is None

            arguments = _build_ffmpeg_arguments(
                self.source,
                self.video_format,
                self.filters
            )

            self._process = await ffmpeg.open(arguments)

    async def close(self: Self) -> None:
        async with self._lock:
            assert self._process

            if self._process.returncode is not None:
                await ffmpeg.close(self._process)

            self._process = None

    async def frames(self: Self) -> AsyncGenerator[bytes]:
        assert self._process
        assert self._process.stdout is not None

        size = calculate_frame_size(self.video_format)

        while True:
            if not self._process:
                return

            data = await self._process.stdout.readexactly(size)

            yield data
