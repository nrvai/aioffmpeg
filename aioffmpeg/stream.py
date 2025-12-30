import asyncio

from typing import Any, AsyncGenerator, Optional, Self

import numpy as np
import numpy.typing as npt

from .source import Source, build_url, rtsp


__all__ = (
    "Stream",
    "VideoFormat"
)


class VideoFormat:
    width: int
    height: int
    fps: int
    pixel_format: str

    def __init__(
        self: Self,
        *,
        width: int,
        height: int,
        fps: int,
        pixel_format: str
    ) -> None:
        self.width = width
        self.height = height
        self.fps = fps
        self.pixel_format = pixel_format


def _get_pixel_channels(pixel_format: str) -> int:
    match pixel_format:
        case "rgba":
            return 4
        case "rgb24" | "bgr24":
            return 3
        case "gray":
            return 1
        case _:
            raise NotImplementedError


def _calculate_frame_size(video_format: VideoFormat) -> int:
    pixel_channels = _get_pixel_channels(video_format.pixel_format)

    return video_format.width * video_format.height * pixel_channels


def _build_command(source: Source, video_format: VideoFormat) -> list[str]:
    url = str(build_url(source))

    match source:
        case rtsp.Source():
            return [
                "ffmpeg",
                "-rtsp_transport",
                source.transport.name.lower(),
                "-i",
                url,
                "-f",
                "rawvideo",
                "-pix_fmt",
                video_format.pixel_format,
                "-r",
                str(video_format.fps),
                "-an",
                "-sn",
                "pipe:1"
            ]
        case _:
            raise NotImplementedError


class Stream:
    source: Source
    video_format: VideoFormat

    _process: Optional[asyncio.subprocess.Process]
    _lock: asyncio.Lock

    def __init__(
        self: Self,
        *,
        source: Source,
        video_format: VideoFormat
    ) -> None:
        self.source = source
        self.video_format = video_format

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

            command = _build_command(self.source, self.video_format)
            self._process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE
            )

    async def close(self: Self) -> None:
        async with self._lock:
            assert self._process

            if self._process.returncode is not None:
                self._process.terminate()
                await self._process.wait()

            self._process = None

    async def frames(self: Self) -> AsyncGenerator[npt.NDArray[np.uint8]]:
        assert self._process

        channels = _get_pixel_channels(self.video_format.pixel_format)
        size = _calculate_frame_size(self.video_format)

        while True:
            if not self._process:
                return

            data = await self._process.stdout.readexactly(size) # pyright: ignore[reportOptionalMemberAccess]
            frame = np \
                .frombuffer(data, dtype=np.uint8) \
                .reshape((
                    self.video_format.height,
                    self.video_format.width,
                    channels
                ))

            yield frame
