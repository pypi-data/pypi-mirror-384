"""Stateless JWT authentication provider"""

from typing import Any, MutableMapping
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field

from authlib.jose import JsonWebToken, JWTClaims
from authlib.jose.errors import JoseError

from .base import BaseAuthProtocol, BaseUser, BaseAuthToken, BaseUserValidator, UserIdentity


@dataclass
class JWTConfig:
    """JWT 配置"""

    secret_key: str
    algorithm: str = field(default="HS256")
    access_token_expire_minutes: int = field(default=30)
    refresh_token_expire_days: int = field(default=30)
    issuer: str = field(default="anystack")


class JWTProvider(BaseAuthProtocol):
    """
    无状态 JWT 认证提供者

    特点:
    - 完全无状态，不依赖任何服务器端存储
    - 用户信息完全编码在 JWT 中
    - 用户验证委托给外部 UserValidator
    - 支持两种模式：带验证器模式和无验证器模式
    """

    def __init__(
        self, config: JWTConfig, user_validator: BaseUserValidator | None = None
    ):
        self.config = config
        self.user_validator = user_validator
        self._jwt = JsonWebToken([config.algorithm])

    def _create_token_payload(
        self, user_info: dict[str, Any], token_type: str = "access"
    ) -> dict[str, Any]:
        """创建 JWT 载荷"""
        now = datetime.now(timezone.utc)

        if token_type == "access":
            expire_delta = timedelta(minutes=self.config.access_token_expire_minutes)
        else:  # refresh token
            expire_delta = timedelta(days=self.config.refresh_token_expire_days)

        # 将用户信息直接编码到 JWT 中 - 无状态的关键
        payload = {
            # 标准 JWT 字段
            "sub": str(user_info["id"]),  # subject (user id)
            "iss": self.config.issuer,  # issuer
            "iat": int(now.timestamp()),  # issued at
            "exp": int((now + expire_delta).timestamp()),  # expiration
            "type": token_type,  # token type
            # 用户信息 - 直接存储在令牌中
            "email": user_info.get("email"),
            "user_data": {
                k: v for k, v in user_info.items() if k not in ["id", "email"]
            },
        }

        return payload

    def _create_token(
        self, user_info: dict[str, Any], token_type: str = "access"
    ) -> str:
        """创建 JWT 令牌"""
        payload = self._create_token_payload(user_info, token_type)
        header = {"alg": self.config.algorithm}
        return self._jwt.encode(header, payload, self.config.secret_key).decode()

    def _decode_token(self, token: str) -> JWTClaims | None:
        """解码并验证 JWT 令牌"""
        try:
            claims = self._jwt.decode(token, self.config.secret_key)
            claims.validate()  # 验证 exp, iat 等标准字段
            return claims
        except JoseError:
            return None

    async def register(self, details: dict[str, Any]) -> BaseUser:
        """注册新用户"""
        if not self.user_validator:
            raise NotImplementedError("需要提供 UserValidator 来处理用户注册")

        user_info = await self.user_validator.create_user(details)

        return BaseUser(
            id=str(user_info["id"]),
            email=user_info.get("email"),
            extra={k: v for k, v in user_info.items() if k not in ["id", "email"]},
        )

    async def login(self, credentials: dict[str, Any]) -> BaseAuthToken:
        """
        用户登录

        支持两种模式:
        1. 带验证器模式: 验证 email/password，从外部系统获取用户信息
        2. 无验证器模式: 直接使用 credentials 中的用户信息（适用于已验证场景）
        """
        email = credentials.get("email")
        password = credentials.get("password")

        if not email:
            raise ValueError("需要提供邮箱")

        if self.user_validator:
            # 带验证器模式: 验证凭据
            if not password:
                raise ValueError("需要提供密码")

            user_info = await self.user_validator.validate_credentials(email, password)
            if not user_info:
                raise ValueError("邮箱或密码错误")
        else:
            user_info = {
                "id": credentials.get("user_id", email),  # 默认使用邮箱作为 ID
                "email": email,
                **{
                    k: v
                    for k, v in credentials.items()
                    if k not in ["email", "password", "user_id"]
                },
            }

        # 创建令牌 - 用户信息完全编码在令牌中
        access_token = self._create_token(user_info, "access")
        refresh_token = self._create_token(user_info, "refresh")

        return BaseAuthToken(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.config.access_token_expire_minutes * 60,
        )

    async def logout(self, token: str) -> None:
        """
        用户登出

        注意: JWT 的无状态特性意味着服务器端无法真正"撤销"令牌
        实际应用中的登出策略:
        1. 客户端删除令牌 (推荐)
        2. 使用短期令牌 + 刷新令牌策略
        3. 维护令牌黑名单 (但这会破坏无状态特性)
        """
        # JWT 本身无法在服务器端撤销
        # 这里只是接口实现，实际的登出逻辑应该在客户端处理
        pass

    async def get_user(self, token: str) -> BaseUser | None:
        """从 JWT 中直接解析用户信息 - 完全无状态"""
        claims = self._decode_token(token)
        if not claims:
            return None

        # 检查令牌类型
        if claims.get("type") != "access":
            return None

        user_id = claims.get("sub")
        email = claims.get("email")
        user_data = claims.get("user_data", {})

        if not user_id:
            return None

        # Extract optional RBAC and identities from user_data if present
        roles = set(user_data.get("roles", []) or [])
        permissions = set(user_data.get("permissions", []) or [])

        identities_payload = user_data.get("identities", []) or []
        identities: list[UserIdentity] = []
        if isinstance(identities_payload, list):
            for item in identities_payload:
                try:
                    identities.append(
                        UserIdentity(
                            provider=str(item.get("provider")),
                            subject=str(item.get("subject")),
                            email=item.get("email"),
                            username=item.get("username"),
                            tenant=item.get("tenant"),
                            claims=item.get("claims", {}) or {},
                            primary=bool(item.get("primary", False)),
                        )
                    )
                except Exception:
                    # Ignore malformed identity payloads; keep token usable
                    continue

        # Remove reserved keys from extra to avoid duplication
        extra = {
            k: v
            for k, v in user_data.items()
            if k not in {"roles", "permissions", "identities"}
        }

        return BaseUser(
            id=user_id,
            email=email,
            roles=roles,
            permissions=permissions,
            identities=identities,
            extra=extra,
        )

    async def refresh_token(self, refresh_token: str) -> BaseAuthToken:
        """刷新访问令牌"""
        claims = self._decode_token(refresh_token)
        if not claims:
            raise ValueError("无效的刷新令牌")

        # 检查令牌类型
        if claims.get("type") != "refresh":
            raise ValueError("不是有效的刷新令牌")

        # 从刷新令牌中提取用户信息
        user_info = {
            "id": claims.get("sub"),
            "email": claims.get("email"),
            **claims.get("user_data", {}),
        }

        if not user_info["id"]:
            raise ValueError("刷新令牌中缺少用户信息")

        # 创建新的访问令牌
        new_access_token = self._create_token(user_info, "access")

        return BaseAuthToken(
            access_token=new_access_token,
            refresh_token=refresh_token,  # 保持原有的刷新令牌
            token_type="bearer",
            expires_in=self.config.access_token_expire_minutes * 60,
        )


class SimpleUserValidator(BaseUserValidator):
    """A lightweight in-memory user validator for demos and tests."""

    def __init__(self, users: MutableMapping[str, dict[str, Any]] | None = None) -> None:
        self._users: MutableMapping[str, dict[str, Any]] = users or {}

    async def validate_credentials(
        self, email: str, password: str
    ) -> dict[str, Any] | None:
        record = self._users.get(email.lower())
        if not record:
            return None
        if record.get("password") != password:
            return None
        return record

    async def create_user(self, details: dict[str, Any]) -> dict[str, Any]:
        email = details.get("email")
        password = details.get("password")
        if not email or not password:
            raise ValueError("email and password are required")

        key = email.lower()
        if key in self._users:
            raise ValueError("user already exists")

        record = {
            "id": details.get("id", key),
            "email": email,
            "password": password,
            **{
                k: v
                for k, v in details.items()
                if k not in {"id", "email", "password"}
            },
        }
        self._users[key] = record
        return record
