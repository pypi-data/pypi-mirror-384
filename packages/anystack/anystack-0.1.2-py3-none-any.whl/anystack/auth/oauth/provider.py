from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
from collections.abc import Mapping

from ..base import BaseAuthProtocol, BaseAuthToken, BaseUser
from .base import BaseOAuthProvider, OAuthResult, OAuthToken


@dataclass(slots=True)
class OAuthLoginParams:
    """Parameters required to complete an OAuth login exchange."""

    code: str
    state: str | None = None
    extra: Mapping[str, Any] = field(default_factory=dict)


class OAuthAuthProvider(BaseAuthProtocol):
    """Auth protocol adapter that reuses third-party OAuth tokens directly."""

    def __init__(self, provider: BaseOAuthProvider, *, default_token_type: str = "bearer") -> None:
        self._provider = provider
        self._default_token_type = default_token_type

    async def register(self, details: dict[str, Any]) -> BaseUser:
        raise NotImplementedError("OAuth providers do not support user registration")

    async def login(self, credentials: dict[str, Any]) -> BaseAuthToken:
        params = self._parse_login_credentials(credentials)
        result = await self._provider.authenticate(
            code=params.code,
            state=params.state,
            **params.extra,
        )
        return self._to_auth_token(result.token)

    async def logout(self, token: str) -> None:
        # OAuth access tokens are managed by the upstream provider; nothing to do here.
        return None

    async def get_user(self, token: str) -> BaseUser | None:
        oauth_token = self._token_from_str(token)
        try:
            profile = await self._provider.fetch_profile(oauth_token)
        except Exception:
            return None
        return self._provider.parse_user(profile)

    async def refresh_token(self, refresh_token: str) -> BaseAuthToken:
        raise NotImplementedError("Refresh token flow is not implemented for OAuth providers")

    def to_auth_token(self, result: OAuthResult) -> BaseAuthToken:
        """Convert an OAuthResult into BaseAuthToken without re-exchange."""
        return self._to_auth_token(result.token)

    def _parse_login_credentials(self, credentials: Mapping[str, Any]) -> OAuthLoginParams:
        code = credentials.get("code")
        if not isinstance(code, str) or not code:
            raise ValueError("OAuth login requires a non-empty 'code'")

        state = credentials.get("state")
        if state is not None and not isinstance(state, str):
            raise ValueError("state must be a string if provided")

        extra = {
            k: v
            for k, v in credentials.items()
            if k not in {"code", "state"}
        }
        return OAuthLoginParams(code=code, state=state, extra=extra)

    def _to_auth_token(self, token: OAuthToken) -> BaseAuthToken:
        expires_in = None
        if token.expires_in is not None:
            expires_in = int(token.expires_in)
        elif token.expires_at is not None:
            remaining = int(token.expires_at - time.time())
            expires_in = remaining if remaining > 0 else 0

        return BaseAuthToken(
            access_token=token.access_token,
            refresh_token=token.refresh_token,
            token_type=token.token_type or self._default_token_type,
            expires_in=expires_in,
        )

    def _token_from_str(self, token: str) -> OAuthToken:
        return OAuthToken(
            access_token=token,
            token_type=self._default_token_type,
            raw={"access_token": token, "token_type": self._default_token_type},
        )
