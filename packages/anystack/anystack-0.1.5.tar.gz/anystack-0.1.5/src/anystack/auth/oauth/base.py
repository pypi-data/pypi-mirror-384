from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from collections.abc import Mapping, Sequence
from abc import ABC, abstractmethod

from authlib.integrations.httpx_client import AsyncOAuth2Client

from ..base import BaseUser


@dataclass(slots=True)
class OAuthConfig:
    """Common configuration for an OAuth2/OIDC provider."""

    client_id: str
    client_secret: str
    redirect_uri: str
    authorize_url: str
    token_url: str
    scope: Sequence[str] = field(default_factory=tuple)
    timeout: float | None = None


@dataclass(slots=True)
class OAuthToken:
    """Normalized OAuth access token returned by a provider."""

    access_token: str
    token_type: str
    refresh_token: str | None = None
    expires_in: float | None = None
    expires_at: float | None = None
    raw: Mapping[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class OAuthResult:
    """Result of a completed OAuth authentication flow."""

    user: BaseUser
    token: OAuthToken
    profile: Mapping[str, Any]


class BaseOAuthProvider(ABC):
    """Abstract base class for OAuth providers backed by Authlib."""

    config: OAuthConfig

    def __init__(self, config: OAuthConfig) -> None:
        self.config = config

    def _create_client(self) -> AsyncOAuth2Client:
        """Instantiate a configured OAuth2 client."""
        client = AsyncOAuth2Client(
            client_id=self.config.client_id,
            client_secret=self.config.client_secret,
            scope=self.config.scope,
            redirect_uri=self.config.redirect_uri,
        )
        if self.config.timeout is not None:
            client.timeout = self.config.timeout
        return client

    async def get_authorize_url(
        self, *, state: str | None = None, **extra_params: Any
    ) -> tuple[str, str]:
        """Return the provider authorize URL and state."""
        client = self._create_client()
        try:
            url, generated_state = client.create_authorization_url(
                self.config.authorize_url,
                state=state,
                **extra_params,
            )
            return url, generated_state
        finally:
            await client.aclose()

    async def fetch_token(
        self, *, code: str, state: str | None = None, **extra_params: Any
    ) -> OAuthToken:
        """Exchange an authorization code for an access token."""
        client = self._create_client()
        try:
            token_set = await client.fetch_token(
                url=self.config.token_url,
                code=code,
                state=state,
                include_client_id=True,
                **extra_params,
            )
        finally:
            await client.aclose()

        access_token = token_set.get("access_token")
        if not access_token:
            raise ValueError("Provider did not return an access_token")

        expires_in = token_set.get("expires_in")
        expires_at = token_set.get("expires_at")

        return OAuthToken(
            access_token=access_token,
            token_type=token_set.get("token_type", "bearer"),
            refresh_token=token_set.get("refresh_token"),
            expires_in=float(expires_in) if expires_in is not None else None,
            expires_at=float(expires_at) if expires_at is not None else None,
            raw=token_set,
        )

    async def authenticate(
        self, *, code: str, state: str | None = None, **extra_params: Any
    ) -> OAuthResult:
        """Complete the OAuth workflow: exchange code and fetch profile."""
        token = await self.fetch_token(code=code, state=state, **extra_params)
        profile = await self.fetch_profile(token)
        user = self.parse_user(profile)
        return OAuthResult(user=user, token=token, profile=profile)

    async def fetch_profile(self, token: OAuthToken) -> Mapping[str, Any]:
        """Fetch the remote user profile using the access token."""
        client = self._create_client()
        client.token = dict(token.raw)
        try:
            return await self._fetch_profile(client)
        finally:
            await client.aclose()

    @abstractmethod
    async def _fetch_profile(
        self, client: AsyncOAuth2Client
    ) -> Mapping[str, Any]:
        """Retrieve the remote user profile. Implemented by subclasses."""
        raise NotImplementedError

    @abstractmethod
    def parse_user(self, profile: Mapping[str, Any]) -> BaseUser:
        """Convert a remote profile into a BaseUser."""
        raise NotImplementedError
