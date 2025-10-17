from typing import Protocol, TypeVar, Callable, Literal, Any, ParamSpec
from collections.abc import AsyncIterator, Awaitable

from starlette.middleware import Middleware, _MiddlewareFactory
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Router
from starlette.websockets import WebSocket



P = ParamSpec("P")
T = TypeVar("T")


class App(Protocol):

    def add_middleware(self, middleware: _MiddlewareFactory[P], *args: P.args, **kwargs: P.kwargs) -> None:
        ...
    

    def add_route(
        self,
        path: str,
        route: Callable[[Request], Awaitable[Response] | Response],
        methods: list[str] | None = None,
        name: str | None = None,
        include_in_schema: bool = True,
    ) -> None:  # pragma: no cover
        ...

    def add_websocket_route(
        self,
        path: str,
        route: Callable[[WebSocket], Awaitable[None]],
        name: str | None = None,
    ) -> None:  # pragma: no cover
        ...
