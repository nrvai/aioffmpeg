from enum import Enum, auto
from typing import Optional, Self

from yarl import URL

from .common import Authentication


__all__ = (
    "Source",
    "Transport",
    "build_url"
)


class Transport(Enum):
    TCP = auto()
    UDP = auto()


class Source:
    host: str
    port: int
    path: Optional[str]
    authentication: Optional[Authentication]
    transport: Transport

    def __init__(
        self: Self,
        *,
        host: str,
        port: int,
        path: Optional[str] = None,
        authentication: Optional[Authentication] = None,
        transport: Transport = Transport.TCP
    ) -> None:
        self.host = host
        self.port = port
        self.path = path
        self.authentication = authentication
        self.transport = transport


def build_url(source: Source) -> URL:
    return URL.build(
        scheme="rtsp",
        host=source.host,
        port=source.port,
        path=source.path or "/",
        user=source.authentication.user if \
            source.authentication else None,
        password=source.authentication.password if \
            source.authentication else None
    )
