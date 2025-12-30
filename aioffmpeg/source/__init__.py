from yarl import URL

from . import rtsp


__all__ = (
    "Source",
    "build_url",
    "rtsp"
)


type Source = rtsp.Source


def build_url(source: Source) -> URL:
    match source:
        case rtsp.Source():
            return rtsp.build_url(source)
        case _:
            raise NotImplementedError
