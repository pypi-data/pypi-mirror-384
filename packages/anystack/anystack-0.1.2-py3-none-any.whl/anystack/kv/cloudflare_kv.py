import json
from collections.abc import AsyncIterable
from dataclasses import dataclass, field
from typing import Any, override, TypeVar

import httpx

from .base import BaseKV

T = TypeVar("T", bound=dict[str, Any])


@dataclass
class Config:
    """Cloudflare KV配置"""

    account_id: str
    namespace_id: str
    api_token: str
    # 可选的自定义HTTP客户端
    client: httpx.AsyncClient | None = field(default=None)
    # API请求超时时间
    timeout: float = field(default=30.0)
    # 是否使用预览模式（用于测试）
    preview: bool = field(default=False)


class CloudflareKV(BaseKV[T]):
    """Cloudflare KV存储实现

    使用Cloudflare Workers KV作为后端存储。
    适用于全球分布式应用，具有低延迟和高可用性。

    注意：
    - Cloudflare KV具有最终一致性
    - 写入操作可能需要一些时间才能在全球传播
    - 适合读多写少的场景
    """

    def __init__(self, config: Config):
        """初始化Cloudflare KV存储

        Args:
            config: Cloudflare KV配置对象

        Raises:
            ImportError: 如果没有安装httpx包
            ValueError: 如果必需的配置参数缺失
        """

        if not all([config.account_id, config.namespace_id, config.api_token]):
            raise ValueError("account_id, namespace_id, and api_token are required.")

        self._config: Config = config
        self._base_url: str = (
            f"https://api.cloudflare.com/client/v4/accounts/{config.account_id}"
            f"/storage/kv/namespaces/{config.namespace_id}"
        )

        # 如果是预览模式，使用预览API端点
        if config.preview:
            self._base_url += "/preview"

        self._headers: dict[str, str] = {
            "Authorization": f"Bearer {config.api_token}",
            "Content-Type": "application/json",
        }

        self._client: httpx.AsyncClient | None = (
            config.client
        )  # httpx.AsyncClient | None
        self._own_client: bool = config.client is None

    async def _ensure_client(self):
        """确保HTTP客户端已初始化"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._config.timeout)

    async def _close_client(self):
        """关闭HTTP客户端"""
        if self._own_client and self._client:
            await self._client.aclose()
            self._client = None

    @override
    async def get(self, key: str) -> T | None:
        """获取指定键的值

        Args:
            key: 键名

        Returns:
            键对应的值，如果键不存在则返回None
        """
        await self._ensure_client()

        try:
            response = await self._client.get(
                f"{self._base_url}/values/{key}", headers=self._headers
            )

            if response.status_code == 404:
                return None

            response.raise_for_status()

            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    @override
    async def set(self, key: str, value: T) -> None:
        """设置键值对

        Args:
            key: 键名
            value: 值，必须是JSON序列化兼容的类型
        """
        await self._ensure_client()

        # 将值序列化为JSON
        try:
            serialized_value = json.dumps(value)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Value must be JSON serializable: {e}")

        response = await self._client.put(
            f"{self._base_url}/values/{key}",
            headers={**self._headers, "Content-Type": "application/json"},
            content=serialized_value,
        )
        response.raise_for_status()

    @override
    async def delete(self, key: str) -> None:
        """删除指定键

        Args:
            key: 要删除的键名
        """
        await self._ensure_client()

        try:
            response = await self._client.delete(
                f"{self._base_url}/values/{key}", headers=self._headers
            )
            # 404表示键不存在，这是正常的
            if response.status_code != 404:
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code != 404:
                raise

    @override
    async def exists(self, key: str) -> bool:
        """检查键是否存在

        Args:
            key: 键名

        Returns:
            如果键存在返回True，否则返回False
        """
        await self._ensure_client()

        try:
            response = await self._client.get(
                f"{self._base_url}/values/{key}", headers=self._headers
            )
            return response.status_code == 200
        except httpx.HTTPStatusError:
            return False

    @override
    async def list(self) -> AsyncIterable[str]:
        """列出所有键

        Yields:
            存储中的所有键名

        Note:
            Cloudflare KV的list操作可能会分页返回结果
        """

        async def _list():
            await self._ensure_client()

            cursor = None

            while True:
                params = {"limit": 1000}  # Cloudflare KV的最大限制
                if cursor:
                    params["cursor"] = cursor

                response = await self._client.get(
                    f"{self._base_url}/keys", headers=self._headers, params=params
                )
                response.raise_for_status()

                data = response.json()
                result = data.get("result", {})

                # 返回当前页的键
                for key_info in result.get("keys", []):
                    yield key_info["name"]

                # 检查是否有更多页
                cursor = result.get("cursor")
                if not cursor:
                    break

        return _list()

    @override
    async def close(self) -> None:
        """关闭连接，清理资源"""
        await self._close_client()

    async def set_with_metadata(
        self, key: str, value: Any, metadata: dict[str, Any]
    ) -> None:
        """设置键值对和元数据

        Args:
            key: 键名
            value: 值
            metadata: 元数据字典
        """
        await self._ensure_client()

        try:
            serialized_value = json.dumps(value)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Value must be JSON serializable: {e}")

        payload = {"value": serialized_value, "metadata": metadata}

        response = await self._client.put(
            f"{self._base_url}/values/{key}", headers=self._headers, json=payload
        )
        response.raise_for_status()

    async def get_with_metadata(self, key: str) -> tuple[Any, dict[str, Any] | None]:
        """获取键值对和元数据

        Args:
            key: 键名

        Returns:
            (value, metadata) 元组，如果键不存在则返回 (None, None)
        """
        await self._ensure_client()

        try:
            response = await self._client.get(
                f"{self._base_url}/metadata/{key}", headers=self._headers
            )

            if response.status_code == 404:
                return None, None

            response.raise_for_status()
            data = response.json()

            # 获取值
            value_response = await self._client.get(
                f"{self._base_url}/values/{key}", headers=self._headers
            )

            if value_response.status_code == 404:
                return None, None

            value_response.raise_for_status()

            try:
                value = value_response.json()
            except (json.JSONDecodeError, ValueError):
                value = value_response.text

            metadata = data.get("result", {}).get("metadata")
            return value, metadata

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None, None
            raise
