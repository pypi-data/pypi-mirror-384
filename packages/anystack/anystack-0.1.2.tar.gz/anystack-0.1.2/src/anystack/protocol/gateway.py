from typing import Protocol, TypeVar, Callable, Literal, Any
from collections.abc import AsyncIterator, Awaitable

T = TypeVar("T")


class Request(Protocol):
    """代表一个传入的 HTTP 请求"""

    @property
    def method(self) -> str: ...

    @property
    def path(self) -> str: ...

    @property
    def headers(self) -> dict[str, str]: ...

    async def body(self) -> bytes: ...

    def stream(self) -> AsyncIterator[bytes]: ...


class Response(Protocol):
    """代表一个传出的 HTTP 响应"""

    status_code: int
    headers: dict[str, str]

    async def body(self) -> bytes: ...


WebSocketState = Literal["connecting", "connected", "disconnected"]


class WebSocket(Protocol):
    """代表一个独立的 WebSocket 连接"""

    @property
    def state(self) -> WebSocketState: ...

    async def accept(
        self, subprotocol: str | None = None, headers: dict[str, str] | None = None
    ) -> None:
        """接受连接请求"""
        ...

    async def receive_text(self) -> str:
        """接收文本消息"""
        ...

    async def send_text(self, data: str) -> None:
        """发送文本消息"""
        ...

    async def receive_bytes(self) -> bytes:
        """接收二进制消息"""
        ...

    async def send_bytes(self, data: bytes) -> None:
        """发送二进制消息"""
        ...

    async def receive_json(self) -> Any:
        """接收并解析 JSON 消息"""
        ...

    async def send_json(self, data: Any) -> None:
        """序列化并发送 JSON 消息"""
        ...

    async def close(self, code: int = 1000, reason: str | None = None) -> None:
        """关闭连接"""
        ...


# Handler 定义了处理请求并返回响应的函数签名
Handler = Callable[[Request], Awaitable[Response]]


LifespanHandler = Callable[[], Awaitable[None]]


class Middleware(Protocol):
    """
    中间件协议。它接收一个请求和一个“下一个”处理器，
    并返回一个响应。
    """

    async def __call__(self, request: Request, next: Handler) -> Response:
        """
        可以在调用 next(request) 之前对请求进行预处理，
        也可以在调用之后对响应进行后处理。
        """
        ...


HTTPHandler = Callable[[Request], Awaitable[Response]]

# WebSocket 处理器签名
WebSocketHandler = Callable[[WebSocket], Awaitable[None]]

Endpoint = HTTPHandler | WebSocketHandler


class Route(Protocol):
    """代表一条路由规则"""

    @property
    def endpoint(self) -> Endpoint: ...

    @property
    def middlewares(self) -> list[Middleware]: ...

    def match(self, request: Request) -> bool:
        """检查请求是否匹配此路由规则"""
        ...


class Router(Protocol):
    """路由器，负责管理和查找路由"""

    def find_route(self, request: Request) -> Route | None:
        """根据请求查找匹配的路由"""
        ...

    def add_route(self, route: Route) -> None:
        ...

    def add_websocket_route(self, route: Route) -> None:
        ...
    

class Gateway(Protocol):
    """
    网关是所有流量的入口点，负责协调路由、中间件和后端服务。
    """

    router: Router
    global_middlewares: list[Middleware]

    def add_middleware(self, middleware: Middleware) -> None:
        ...

    def add_route(self, route: Route) -> None:
        ...

    def add_websocket_route(self, route: Route) -> None:
        ...

    def on_startup(self, handler: LifespanHandler) -> None:
        ...

    def on_shutdown(self, handler: LifespanHandler) -> None:
        ...

    async def startup(self) -> None:
        ...

    async def shutdown(self) -> None:
        ...
