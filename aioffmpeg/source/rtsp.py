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
    path: str
    query: dict[str, str]
    authentication: Optional[Authentication]
    transport: Transport

    def __init__(
        self: Self,
        *,
        host: str,
        port: Optional[int] = None,
        path: Optional[str] = None,
        query: Optional[dict[str, str]] = None,
        authentication: Optional[Authentication] = None,
        transport: Optional[Transport] = None
    ) -> None:
        self.host = host
        self.port = port if port is not None else 554
        self.path = path if path is not None else "/"
        self.query = query if query is not None else {}
        self.authentication = authentication
        self.transport = transport if transport is not None else Transport.TCP


def build_url(source: Source) -> URL:
    return URL.build(
        scheme="rtsp",
        host=source.host,
        port=source.port,
        path=source.path,
        query=source.query,
        user=source.authentication.user if \
            source.authentication else None,
        password=source.authentication.password if \
            source.authentication else None
    )
