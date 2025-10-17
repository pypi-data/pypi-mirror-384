from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, override
from collections.abc import Mapping, Sequence

from authlib.integrations.httpx_client import AsyncOAuth2Client

from ..base import BaseUser, UserIdentity
from .base import BaseOAuthProvider, OAuthConfig, OAuthToken


@dataclass(slots=True)
class GenericOAuthConfig(OAuthConfig):
    """通用OAuth配置，支持任何标准OAuth 2.0/OIDC提供者."""

    # 用户信息端点（必需字段）
    userinfo_url: str = ""

    # 提供方名称（用于生成身份标识与区分来源）
    provider_name: str = "oidc"

    # 用户字段映射配置
    user_id_field: str = "sub"  # 用户ID字段名，默认为OIDC标准的'sub'
    email_field: str = "email"  # 邮箱字段名

    # 可选的额外字段映射
    extra_fields: dict[str, str] = field(default_factory=dict)

    # 请求头配置
    userinfo_headers: dict[str, str] = field(
        default_factory=lambda: {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
    )

    # 用户解析自定义函数（可选）
    custom_user_parser: Callable[[Mapping[str, Any]], dict[str, Any]] | None = None


class GenericOAuthProvider(BaseOAuthProvider):
    """通用OAuth提供者，支持任何标准OAuth 2.0/OIDC提供者."""

    config: GenericOAuthConfig

    def __init__(self, config: GenericOAuthConfig) -> None:
        super().__init__(config)

    def _create_client(self) -> AsyncOAuth2Client:
        """创建支持自定义重定向URI参数的OAuth2客户端."""
        # 如果使用非标准的重定向URI参数名称，我们需要自定义客户端行为
        client = AsyncOAuth2Client(
            client_id=self.config.client_id,
            client_secret=self.config.client_secret,
            scope=self.config.scope,
            redirect_uri=self.config.redirect_uri,
        )
        if self.config.timeout is not None:
            client.timeout = self.config.timeout
        return client

    @override
    async def get_authorize_url(
        self, *, state: str | None = None, **extra_params: Any
    ) -> tuple[str, str]:
        """返回授权URL和状态，支持自定义重定向URI参数名称."""
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

    @override
    async def fetch_token(
        self, *, code: str, state: str | None = None, **extra_params: Any
    ) -> OAuthToken:
        """获取访问令牌，支持自定义重定向URI参数名称."""
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

    @override
    async def _fetch_profile(self, client: AsyncOAuth2Client) -> Mapping[str, Any]:
        """从OAuth提供者获取用户信息."""
        resp = await client.get(
            self.config.userinfo_url, headers=self.config.userinfo_headers
        )
        resp.raise_for_status()
        profile: dict[str, Any] = resp.json()
        return profile

    @override
    def parse_user(self, profile: Mapping[str, Any]) -> BaseUser:
        """将OAuth用户信息解析为BaseUser对象."""

        # 如果有自定义解析函数，优先使用
        if self.config.custom_user_parser:
            parsed_data = self.config.custom_user_parser(profile)
            identity = UserIdentity(
                provider=self.config.provider_name,
                subject=str(parsed_data.get("id", "")),
                email=parsed_data.get("email"),
                claims=dict(profile),
                primary=True,
            )
            return BaseUser(
                id=f"{self.config.provider_name}:{identity.subject}",
                email=identity.email,
                identities=[identity],
                extra=parsed_data.get("extra", {}),
            )

        # 获取用户ID
        user_id = profile.get(self.config.user_id_field)
        if user_id is None:
            raise ValueError(
                f"OAuth profile does not contain field '{self.config.user_id_field}'"
            )

        # 获取邮箱
        email = profile.get(self.config.email_field)

        # 构建额外字段
        extra = {}
        for local_key, remote_key in self.config.extra_fields.items():
            value = profile.get(remote_key)
            if value is not None:
                extra[local_key] = value

        subject = str(user_id)
        identity = UserIdentity(
            provider=self.config.provider_name,
            subject=subject,
            email=email,
            claims=dict(profile),
            primary=True,
        )

        return BaseUser(
            id=f"{self.config.provider_name}:{subject}",
            email=email,
            identities=[identity],
            extra=extra,
        )


def create_keycloak_config(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    server_url: str,
    realm: str,
    scope: Sequence[str] = ("openid", "profile", "email"),
    **kwargs: Any,
) -> GenericOAuthConfig:
    """创建Keycloak OAuth配置的便捷函数."""
    base_url = f"{server_url}/realms/{realm}/protocol/openid-connect"

    return GenericOAuthConfig(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        authorize_url=f"{base_url}/auth",
        token_url=f"{base_url}/token",
        userinfo_url=f"{base_url}/userinfo",
        scope=scope,
        user_id_field="sub",
        email_field="email",
        extra_fields={
            "username": "preferred_username",
            "name": "name",
            "given_name": "given_name",
            "family_name": "family_name",
            "locale": "locale",
            "email_verified": "email_verified",
        },
        **kwargs,
    )


def create_google_config(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    scope: Sequence[str] = ("openid", "profile", "email"),
    **kwargs: Any,
) -> GenericOAuthConfig:
    """创建Google OAuth配置的便捷函数."""
    return GenericOAuthConfig(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        userinfo_url="https://openidconnect.googleapis.com/v1/userinfo",
        scope=scope,
        user_id_field="sub",
        email_field="email",
        extra_fields={
            "name": "name",
            "given_name": "given_name",
            "family_name": "family_name",
            "picture": "picture",
            "locale": "locale",
            "email_verified": "email_verified",
        },
        **kwargs,
    )


def create_microsoft_config(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    tenant: str = "common",
    scope: Sequence[str] = ("openid", "profile", "email"),
    **kwargs: Any,
) -> GenericOAuthConfig:
    """创建Microsoft/Azure AD OAuth配置的便捷函数."""
    base_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0"

    return GenericOAuthConfig(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        authorize_url=f"{base_url}/authorize",
        token_url=f"{base_url}/token",
        userinfo_url="https://graph.microsoft.com/oidc/userinfo",
        scope=scope,
        user_id_field="sub",
        email_field="email",
        extra_fields={
            "name": "name",
            "given_name": "given_name",
            "family_name": "family_name",
            "preferred_username": "preferred_username",
        },
        **kwargs,
    )


def create_custom_oauth_config(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    authorize_url: str,
    token_url: str,
    userinfo_url: str,
    scope: Sequence[str] = ("openid", "profile", "email"),
    user_id_field: str = "sub",
    email_field: str = "email",
    extra_fields: dict[str, str] | None = None,
    **kwargs: Any,
) -> GenericOAuthConfig:
    """创建自定义OAuth配置的便捷函数，支持非标准的重定向URI参数名."""
    return GenericOAuthConfig(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        authorize_url=authorize_url,
        token_url=token_url,
        userinfo_url=userinfo_url,
        scope=scope,
        user_id_field=user_id_field,
        email_field=email_field,
        extra_fields=extra_fields or {},
        **kwargs,
    )
