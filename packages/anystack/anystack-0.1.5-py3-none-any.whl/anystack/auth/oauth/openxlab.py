from httpx._models import Response


from dataclasses import dataclass, field
from typing import Any, override
from collections.abc import Mapping
from datetime import datetime
import base64
import time

from httpx import AsyncClient
import rsa


from .generic import GenericOAuthProvider, GenericOAuthConfig
from .base import OAuthToken
from ..base import BaseUser, UserIdentity


@dataclass(slots=True)
class OpenXLabOAuthConfig(GenericOAuthConfig):
    public_key_url: str = field(default="")


class OpenXLabOAuthProvider(GenericOAuthProvider):
    """OpenXLab OAuth provider."""

    config: OpenXLabOAuthConfig

    def __init__(self, config: OpenXLabOAuthConfig):
        super().__init__(config)
        self.http_client = AsyncClient()

    @override
    async def get_authorize_url(
        self, *, state: str | None = None, **extra_params: Any
    ) -> tuple[str, str]:
        """返回授权URL和状态，支持自定义重定向URI参数名称."""
        client = self._create_client()

        try:
            url = f"{self.config.authorize_url}?redirect={self.config.redirect_uri}?clientId={self.config.client_id}"

            return url, ""
        finally:
            await client.aclose()

    async def get_public_key(self) -> rsa.PublicKey:
        resp = await self.http_client.post(
            self.config.public_key_url,
            json={
                "clientId": self.config.client_id,
                "type": "auth",
                "from": "platform",
            },
        )
        resp.raise_for_status()
        pub_key = resp.json()["data"]["pubKey"]
        public_key = (
            f"-----BEGIN PUBLIC KEY-----\n{pub_key}\n-----END PUBLIC KEY-----".encode()
        )
        return rsa.PublicKey.load_pkcs1_openssl_pem(public_key)

    async def get_decrypted(self) -> str:
        public_key = await self.get_public_key()
        return base64.b64encode(
            rsa.encrypt(
                f"{self.config.client_id}||{self.config.client_secret}||{int(time.time())}".encode(),
                public_key,
            )
        ).decode()

    async def get_user_info(self, jwt: str) -> dict[str, Any]:
        resp = await self.http_client.post(
            f"{self.config.userinfo_url}",
            json={
                "token": jwt,
                "clientId": self.config.client_id,
                "d": await self.get_decrypted(),
            },
        )
        if resp.json()["msgCode"] != "10000":
            raise ValueError(resp)
        resp.raise_for_status()
        return resp.json()["data"]

    @override
    async def fetch_token(
        self, *, code: str, state: str | None = None, **extra_params: Any
    ) -> OAuthToken:
        """获取访问令牌，支持自定义重定向URI参数名称."""
        token_set: Response = await self.http_client.post(
            self.config.token_url,
            json={
                "clientId": self.config.client_id,
                "code": code,
                "state": state,
                "d": await self.get_decrypted(),
            },
        )

        token_set.raise_for_status()
        resp = token_set.json()
        if resp["msgCode"] != "10000":
            raise ValueError(resp)

        return OAuthToken(
            access_token=resp["data"]["jwt"],
            token_type="bearer",
            expires_at=float(
                datetime.strptime(
                    resp["data"]["expiration"], "%Y-%m-%d %H:%M:%S"
                ).timestamp()
            )
            if resp["data"]["expiration"] is not None
            else None,
            raw=resp["data"],
        )

    @override
    async def fetch_profile(self, token: OAuthToken) -> Mapping[str, Any]:
        return await self.get_user_info(token.access_token)

    @override
    def parse_user(self, profile: Mapping[str, Any]) -> BaseUser:
        provider = "openxlab"
        subject = str(profile["ssoUid"])  # provider user id
        email = profile.get("email")
        identity = UserIdentity(
            provider=provider,
            subject=subject,
            email=email,
            username=profile.get("username"),
            claims=dict(profile),
            primary=True,
        )
        return BaseUser(
            id=f"{provider}:{subject}",
            email=email,
            identities=[identity],
            extra=dict(profile),
        )
