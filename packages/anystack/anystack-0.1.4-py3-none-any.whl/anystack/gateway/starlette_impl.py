from __future__ import annotations

import inspect
from typing import Any, cast, override
from collections.abc import AsyncIterator, Sequence

from starlette.requests import Request as StarletteRawRequest
from starlette.responses import Response as StarletteRawResponse
from starlette.responses import PlainTextResponse
from starlette.websockets import (
    WebSocket as StarletteRawWebSocket,
    WebSocketState as StarletteWSState,
)
from starlette.types import ASGIApp, Scope, Receive, Send, Message

from ..protocol.gateway import (
    Endpoint,
    Gateway,
    HTTPHandler,
    Middleware,
    Request,
    Response,
    Router,
    Route,
    WebSocket,
    WebSocketHandler,
    WebSocketState,
)

from .base import BaseGateway, BaseRequest, BaseResponse, BaseWebSocket


class _MockRequest(BaseRequest):
    """A mock request used for WebSocket routing."""

    _scope: Scope

    def __init__(self, scope: Scope):
        self._scope = scope

    @property
    @override
    def method(self) -> str:
        return "GET"

    @property
    @override
    def path(self) -> str:
        return self._scope["path"]

    @property
    @override
    def headers(self) -> dict[str, str]:
        return {k.decode("utf-8"): v.decode("utf-8") for k, v in self._scope["headers"]}

    @override
    async def body(self) -> bytes:
        return b""

    @override
    def stream(self) -> AsyncIterator[bytes]:
        async def _empty_stream():
            yield b""

        return _empty_stream()


class StarletteRequest(BaseRequest):
    """包装 Starlette Request 以符合 Request 协议"""

    _request: StarletteRawRequest

    def __init__(self, request: StarletteRawRequest):
        self._request = request

    @property
    @override
    def method(self) -> str:
        return self._request.method

    @property
    @override
    def path(self) -> str:
        return self._request.url.path

    @property
    @override
    def headers(self) -> dict[str, str]:
        return dict(self._request.headers)

    @override
    async def body(self) -> bytes:
        return await self._request.body()

    @override
    def stream(self) -> AsyncIterator[bytes]:
        return self._request.stream()


class StarletteResponse(BaseResponse):
    """包装 Starlette Response 以符合 Response 协议"""

    _response: StarletteRawResponse
    status_code: int
    headers: dict[str, str]
    scope: Scope | None

    def __init__(self, response: StarletteRawResponse, scope: Scope | None = None):
        self._response = response
        self.status_code = response.status_code
        self.headers = dict(response.headers)
        self.scope = scope

    @override
    async def body(self) -> bytes:
        if hasattr(self._response, "body"):
            return cast(bytes, self._response.body)

        async def _receive() -> Message:
            return {"type": "http.response.body", "body": b""}

        body_chunks: list[bytes] = []

        async def _send(message: Message) -> None:
            if message["type"] == "http.response.body":
                body_chunks.append(message.get("body", b""))

        # The scope is needed for rendering some response types.
        scope = self.scope or {}
        await self._response(scope, _receive, _send)
        return b"".join(body_chunks)


class StarletteWebSocket(BaseWebSocket):
    """包装 Starlette WebSocket 以符合 WebSocket 协议"""

    _websocket: StarletteRawWebSocket

    def __init__(self, websocket: StarletteRawWebSocket):
        self._websocket = websocket

    @property
    @override
    def state(self) -> WebSocketState:
        starlette_state = self._websocket.client_state
        if starlette_state == StarletteWSState.CONNECTING:
            return "connecting"
        if starlette_state == StarletteWSState.CONNECTED:
            return "connected"
        # DISCONNECTED state
        return "disconnected"

    @override
    async def accept(
        self, subprotocol: str | None = None, headers: dict[str, str] | None = None
    ) -> None:
        raw_headers = (
            [(k.encode(), v.encode()) for k, v in headers.items()] if headers else None
        )
        await self._websocket.accept(subprotocol=subprotocol, headers=raw_headers)

    @override
    async def receive_text(self) -> str:
        return await self._websocket.receive_text()

    @override
    async def send_text(self, data: str) -> None:
        if self.state == "connected":
            await self._websocket.send_text(data)

    @override
    async def receive_bytes(self) -> bytes:
        return await self._websocket.receive_bytes()

    @override
    async def send_bytes(self, data: bytes) -> None:
        if self.state == "connected":
            await self._websocket.send_bytes(data)

    @override
    async def receive_json(self) -> Any:
        return await self._websocket.receive_json()

    @override
    async def send_json(self, data: Any) -> None:
        if self.state == "connected":
            await self._websocket.send_json(data)

    @override
    async def close(self, code: int = 1000, reason: str | None = None) -> None:
        await self._websocket.close(code=code, reason=reason)




class StarletteGateway(BaseGateway):
    router: Router
    global_middlewares: list[Middleware]

    def __init__(
        self,
        *,
        router: Router,
        global_middlewares: list[Middleware] | None = None,
    ):
        super().__init__()
        self.router = router
        self.global_middlewares = list(global_middlewares or [])

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            raw_request = StarletteRawRequest(scope, receive)
            response = await self.handle_http(StarletteRequest(raw_request))
            content = await response.body()
            # Re-create a raw response because the body of the protocol response might have been
            # consumed or generated from a stream.
            raw_response = StarletteRawResponse(
                content=content,
                status_code=response.status_code,
                headers=response.headers,
            )
            await raw_response(scope, receive, send)
        elif scope["type"] == "websocket":
            raw_websocket = StarletteRawWebSocket(scope, receive, send)
            await self.handle_ws(StarletteWebSocket(raw_websocket))
        elif scope["type"] == "lifespan":
            await self.handle_lifespan(receive, send)

    def is_http_handler(self, endpoint: Endpoint) -> bool:
        sig = inspect.signature(endpoint)
        if not sig.parameters:
            return False
        first_param = next(iter(sig.parameters.values()))
        return "Request" in str(first_param.annotation)

    def is_ws_handler(self, endpoint: Endpoint) -> bool:
        sig = inspect.signature(endpoint)
        if not sig.parameters:
            return False
        first_param = next(iter(sig.parameters.values()))
        return "WebSocket" in str(first_param.annotation)

    async def handle_http(self, request: Request) -> Response:
        scope = getattr(getattr(request, "_request", None), "scope", None)
        route = self.router.find_route(request)
        if not route:
            return StarletteResponse(
                PlainTextResponse("Not Found", status_code=404), scope=scope
            )

        endpoint = route.endpoint
        if not self.is_http_handler(endpoint):
            return StarletteResponse(
                PlainTextResponse("Method Not Allowed", status_code=405), scope=scope
            )

        http_handler = cast(HTTPHandler, endpoint)

        all_middlewares = self.global_middlewares + route.middlewares
        handler_stack = http_handler
        for mw in reversed(all_middlewares):

            def create_next_handler(
                next_handler: HTTPHandler, current_mw: Middleware
            ) -> HTTPHandler:
                async def chained_handler(req: Request) -> Response:
                    return await current_mw(req, next_handler)

                return chained_handler

            handler_stack = create_next_handler(handler_stack, mw)

        return await handler_stack(request)

    async def handle_ws(self, websocket: WebSocket) -> None:
        if not isinstance(websocket, StarletteWebSocket):
            await websocket.close(code=1011, reason="Internal Server Error")
            return

        scope = websocket._websocket.scope  # type: ignore[protected-access]
        mock_request = _MockRequest(scope)

        route = self.router.find_route(mock_request)
        if not route:
            await websocket.close(code=1011, reason="Not Found")
            return

        endpoint = route.endpoint
        if not self.is_ws_handler(endpoint):
            await websocket.close(code=1011, reason="Method Not Allowed")
            return

        ws_handler = cast(WebSocketHandler, endpoint)
        await ws_handler(websocket)

    @override
    def add_middleware(self, middleware: Middleware) -> None:
        self.global_middlewares.append(middleware)

    @override
    def add_route(self, route: Route) -> None:
        self.router.add_route(route)

    @override
    def add_websocket_route(self, route: Route) -> None:
        self.router.add_websocket_route(route)

    async def handle_lifespan(self, receive: Receive, send: Send) -> None:
        while True:
            message = await receive()
            message_type = message["type"]

            if message_type == "lifespan.startup":
                try:
                    await self.startup()
                except Exception as exc:  # noqa: BLE001
                    await send(
                        {
                            "type": "lifespan.startup.failed",
                            "message": str(exc),
                        }
                    )
                    raise
                else:
                    await send({"type": "lifespan.startup.complete"})

            elif message_type == "lifespan.shutdown":
                try:
                    await self.shutdown()
                except Exception as exc:  # noqa: BLE001
                    await send(
                        {
                            "type": "lifespan.shutdown.failed",
                            "message": str(exc),
                        }
                    )
                    raise
                else:
                    await send({"type": "lifespan.shutdown.complete"})
                    return
