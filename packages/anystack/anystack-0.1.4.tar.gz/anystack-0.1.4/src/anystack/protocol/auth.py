from typing import Any, Protocol, TypedDict

from dataclasses import dataclass, field


class User(TypedDict):
    """Represents a user in the system."""

    id: str
    email: str | None
    extra: dict[str, Any]


class AuthToken(TypedDict):
    """Represents the authentication token(s)."""

    access_token: str
    refresh_token: str | None
    token_type: str
    expires_in: int | None  # in seconds


class UserValidator(Protocol):
    """User validation protocol - implemented by external systems"""

    async def validate_credentials(
        self, email: str, password: str
    ) -> dict[str, Any] | None: ...

    async def create_user(self, details: dict[str, Any]) -> dict[str, Any]: ...


class AuthProtocol(Protocol):
    """
    An abstract protocol for a generic authentication system.
    """

    async def register(self, details: dict[str, Any]) -> User: ...

    async def login(self, credentials: dict[str, Any]) -> AuthToken: ...

    async def logout(self, token: str) -> None: ...

    async def get_user(self, token: str) -> User | None: ...

    async def refresh_token(self, refresh_token: str) -> AuthToken: ...
