from typing import Optional, Self


__all__ = (
    "Authentication",
)


class Authentication:
    user: str
    password: Optional[str]

    def __init__(
        self: Self,
        *,
        user: str,
        password: Optional[str] = None
    ) -> None:
        self.user = user
        self.password = password
