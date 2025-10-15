from __future__ import annotations

from re import Pattern
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from starlette.routing import compile_path

from ..protocol.gateway import (
    Endpoint,
    LifespanHandler,
    Middleware,
    Request,
    Route,
    Router,
    WebSocketState,
)


class PathRoute:
    """
    一个基于路径和 HTTP 方法进行匹配的具体路由实现
    """

    path: str
    _endpoint: Endpoint
    methods: list[str] | None
    _middlewares: list[Middleware]
    _path_regex: Pattern[str]

    def __init__(
        self,
        path: str,
        endpoint: Endpoint,
        *,
        methods: list[str] | None = None,
        middlewares: list[Middleware] | None = None,
    ):
        self.path = path
        self._endpoint = endpoint
        self.methods = methods
        self._middlewares = middlewares or []
        self._path_regex, _, _ = compile_path(path)

    @property
    def endpoint(self) -> Endpoint:
        return self._endpoint

    @property
    def middlewares(self) -> list[Middleware]:
        return self._middlewares

    def match(self, request: Request) -> bool:
        if self.methods and request.method not in self.methods:
            return False
        return self._path_regex.match(request.path) is not None


class ListRouter:
    """
    一个简单的路由器实现，它按顺序遍历一个路由列表
    """

    _routes: list[Route]

    def __init__(self, routes: list[Route]):
        self._routes = routes

    def find_route(self, request: Request) -> Route | None:
        for route in self._routes:
            if route.match(request):
                return route
        return None

    def add_route(self, route: Route) -> None:
        self._routes.append(route)

    def add_websocket_route(self, route: Route) -> None:
        self._routes.append(route)


class BaseRequest(ABC):
    @property
    @abstractmethod
    def method(self) -> str: ...

    @property
    @abstractmethod
    def path(self) -> str: ...

    @property
    @abstractmethod
    def headers(self) -> dict[str, str]: ...

    @abstractmethod
    async def body(self) -> bytes: ...

    @abstractmethod
    def stream(self) -> AsyncIterator[bytes]: ...


class BaseResponse(ABC):
    status_code: int
    headers: dict[str, str]

    @abstractmethod
    async def body(self) -> bytes: ...


class BaseWebSocket(ABC):
    @property
    @abstractmethod
    def state(self) -> WebSocketState: ...

    @abstractmethod
    async def accept(
        self, subprotocol: str | None = None, headers: dict[str, str] | None = None
    ) -> None: ...

    @abstractmethod
    async def receive_text(self) -> str: ...

    @abstractmethod
    async def send_text(self, data: str) -> None: ...

    @abstractmethod
    async def receive_bytes(self) -> bytes: ...

    @abstractmethod
    async def send_bytes(self, data: bytes) -> None: ...

    @abstractmethod
    async def receive_json(self) -> Any: ...

    @abstractmethod
    async def send_json(self, data: Any) -> None: ...

    @abstractmethod
    async def close(self, code: int = 1000, reason: str | None = None) -> None: ...


class BaseGateway(ABC):
    router: Router
    global_middlewares: list[Middleware]

    def __init__(self) -> None:
        self.global_middlewares = []
        self._startup_handlers: list[LifespanHandler] = []
        self._shutdown_handlers: list[LifespanHandler] = []
        self._lifespan_started = False

    @abstractmethod
    def add_middleware(self, middleware: Middleware) -> None: ...

    @abstractmethod
    def add_route(self, route: Route) -> None: ...

    @abstractmethod
    def add_websocket_route(self, route: Route) -> None: ...

    def on_startup(self, handler: LifespanHandler) -> None:
        self._startup_handlers.append(handler)

    def on_shutdown(self, handler: LifespanHandler) -> None:
        self._shutdown_handlers.append(handler)

    async def startup(self) -> None:
        if self._lifespan_started:
            return
        for handler in self._startup_handlers:
            await handler()
        self._lifespan_started = True

    async def shutdown(self) -> None:
        if not self._lifespan_started:
            return
        for handler in reversed(self._shutdown_handlers):
            await handler()
        self._lifespan_started = False
