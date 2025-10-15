from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence, Any
from collections.abc import Mapping

from .generic import GenericOAuthConfig, GenericOAuthProvider
from ..base import BaseUser, UserIdentity


_DEFAULT_SCOPE: tuple[str, ...] = ("openid", "profile", "email")


def _default_extra_fields() -> dict[str, str]:
    return {
        "name": "name",
        "username": "username",
        "picture": "picture",
        "family_name": "family_name",
        "given_name": "given_name",
        "locale": "locale",
        "phone_number": "phone_number",
        "email_verified": "email_verified",
        "roles": "roleNames",
        "custom_data": "customData",
    }


@dataclass(slots=True)
class LogtoOAuthConfig(GenericOAuthConfig):
    """Configuration helper for Logto OAuth/OIDC providers."""

    endpoint: str = ""
    authorize_url: str = ""
    token_url: str = ""
    userinfo_url: str = ""
    scope: Sequence[str] = field(default_factory=lambda: _DEFAULT_SCOPE)
    extra_fields: dict[str, str] = field(default_factory=_default_extra_fields)

    def __post_init__(self) -> None:
        if not self.endpoint:
            raise ValueError("Logto endpoint must be provided")

        base_endpoint = self.endpoint.rstrip("/")

        if not self.authorize_url:
            self.authorize_url = f"{base_endpoint}/oidc/auth"

        if not self.token_url:
            self.token_url = f"{base_endpoint}/oidc/token"

        if not self.userinfo_url:
            self.userinfo_url = f"{base_endpoint}/oidc/me"


class LogtoOAuthProvider(GenericOAuthProvider):
    """OAuth provider implementation backed by Logto."""

    config: LogtoOAuthConfig

    def __init__(self, config: LogtoOAuthConfig) -> None:
        super().__init__(config)

    def parse_user(self, profile: Mapping[str, Any]) -> BaseUser:
        provider = "logto"
        # Logto /oidc/me response follows OIDC; prefer 'sub' for subject
        sub = profile.get("sub")
        if not sub:
            # Fallback to 'id' if a custom pipeline mapped it
            sub = profile.get("id")
        if not sub:
            raise ValueError("Logto profile does not contain 'sub' or 'id'")

        email = profile.get("email")
        identity = UserIdentity(
            provider=provider,
            subject=str(sub),
            email=email,
            username=profile.get("username"),
            claims=dict(profile),
            primary=True,
        )
        return BaseUser(
            id=f"{provider}:{identity.subject}",
            email=email,
            identities=[identity],
            extra={k: v for k, v in profile.items() if k not in {"sub", "email"}},
        )
