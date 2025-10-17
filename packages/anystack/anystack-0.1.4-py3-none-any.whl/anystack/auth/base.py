from typing import Any, Iterable

from dataclasses import dataclass, field
from abc import ABC, abstractmethod


@dataclass(slots=True)
class UserIdentity:
    """Represents an external identity bound to a user.

    - provider: logical name of the identity provider (e.g. 'github', 'logto').
    - subject: stable user identifier issued by the provider (e.g. OIDC 'sub').
    - email/username/tenant are optional conveniences for routing and display.
    - claims can store raw profile fields for later enrichment.
    - primary marks the identity used as the main login/merge reference.
    """

    provider: str
    subject: str
    email: str | None = None
    username: str | None = None
    tenant: str | None = None
    claims: dict[str, Any] = field(default_factory=dict)
    primary: bool = False


@dataclass(slots=True)
class BaseUser:
    id: str  # canonical internal id (can be provider:subject if no user store)
    email: str | None
    # Optional RBAC primitives
    roles: set[str] = field(default_factory=set)
    permissions: set[str] = field(default_factory=set)
    # External identities bound to this user
    identities: list[UserIdentity] = field(default_factory=list)
    # Extra profile or app-specific fields
    extra: dict[str, Any] = field(default_factory=dict)

    def primary_identity(self) -> UserIdentity | None:
        """Return the primary identity if available, else the first one."""
        for ident in self.identities:
            if ident.primary:
                return ident
        return self.identities[0] if self.identities else None

    def set_identities(self, identities: Iterable[UserIdentity]) -> None:
        self.identities = list(identities)

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def has_permission(self, perm: str) -> bool:
        return perm in self.permissions


@dataclass(slots=True)
class BaseAuthToken:
    access_token: str
    refresh_token: str | None = field(default=None)
    token_type: str = field(default="bearer")
    expires_in: int | None = field(default=None)  # in seconds


class BaseUserValidator(ABC):
    @abstractmethod
    async def validate_credentials(
        self, email: str, password: str
    ) -> dict[str, Any] | None: ...
    @abstractmethod
    async def create_user(self, details: dict[str, Any]) -> dict[str, Any]: ...


class BaseAuthProtocol(ABC):
    @abstractmethod
    async def register(self, details: dict[str, Any]) -> BaseUser: ...
    @abstractmethod
    async def login(self, credentials: dict[str, Any]) -> BaseAuthToken: ...
    @abstractmethod
    async def logout(self, token: str) -> None: ...
    @abstractmethod
    async def get_user(self, token: str) -> BaseUser | None: ...
    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> BaseAuthToken: ...
