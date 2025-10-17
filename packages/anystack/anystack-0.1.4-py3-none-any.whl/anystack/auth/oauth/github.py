from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from authlib.integrations.httpx_client import AsyncOAuth2Client

from ..base import BaseUser, UserIdentity
from .base import BaseOAuthProvider, OAuthConfig


@dataclass(slots=True)
class GitHubOAuthConfig(OAuthConfig):
    """Configuration specific to GitHub OAuth."""

    authorize_url: str = "https://github.com/login/oauth/authorize"
    token_url: str = "https://github.com/login/oauth/access_token"
    scope: Sequence[str] = field(
        default_factory=lambda: ("read:user", "user:email")
    )
    allow_signup: bool = True
    api_base_url: str = "https://api.github.com"
    user_agent: str = "anystack-oauth-client"


class GitHubOAuthProvider(BaseOAuthProvider):
    """OAuth provider implementation for GitHub."""

    config: GitHubOAuthConfig

    def __init__(self, config: GitHubOAuthConfig) -> None:
        super().__init__(config)

    async def _fetch_profile(self, client: AsyncOAuth2Client) -> Mapping[str, Any]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": self.config.user_agent,
        }
        query_params = {
            "allow_signup": str(self.config.allow_signup).lower(),
        }
        user_resp = await client.get(
            f"{self.config.api_base_url}/user",
            headers=headers,
            params=query_params,
        )
        user_resp.raise_for_status()
        profile: dict[str, Any] = user_resp.json()

        # GitHub can return null email; fetch verified addresses if needed.
        if not profile.get("email"):
            emails_resp = await client.get(
                f"{self.config.api_base_url}/user/emails",
                headers=headers,
            )
            emails_resp.raise_for_status()
            emails: list[dict[str, Any]] = emails_resp.json()
            primary = next(
                (
                    email_entry.get("email")
                    for email_entry in emails
                    if email_entry.get("primary") and email_entry.get("verified")
                ),
                None,
            )
            profile["email"] = primary or profile.get("email")

        return profile

    def parse_user(self, profile: Mapping[str, Any]) -> BaseUser:
        provider = "github"
        github_id = profile.get("id")
        if github_id is None:
            raise ValueError("GitHub profile does not contain an id")

        email = profile.get("email")
        extra = {
            "login": profile.get("login"),
            "name": profile.get("name"),
            "avatar_url": profile.get("avatar_url"),
            "profile_url": profile.get("html_url"),
        }

        subject = str(github_id)
        identity = UserIdentity(
            provider=provider,
            subject=subject,
            email=email,
            username=profile.get("login"),
            claims=dict(profile),
            primary=True,
        )

        # Use provider-qualified id to avoid cross-provider collision where no user store exists
        return BaseUser(id=f"{provider}:{subject}", email=email, identities=[identity], extra=extra)
