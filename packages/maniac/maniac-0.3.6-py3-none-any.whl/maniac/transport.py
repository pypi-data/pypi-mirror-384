# maniac/transport.py
from typing import Any, Dict, Iterable, AsyncIterable, Optional, Protocol, Callable
import asyncio


class ManiacHTTPError(Exception):
    def __init__(self, status: int, reason: str, body: Any = None):
        super().__init__(f"HTTP {status} {reason}")
        self.status = status
        self.reason = reason
        self.body = body


class SyncTransport(Protocol):
    base_url: str

    def close(self) -> None: ...
    def __enter__(self): ...
    def __exit__(self, exc_type, exc, tb): ...

    def request_json(
        self, path: str, init: Dict[str, Any], subdomain: str = "api"
    ) -> Any: ...

    def post_json_with_jwt(
        self, url: str, payload: Any, subdomain: str = "api"
    ) -> Any: ...

    def sse_events(
        self,
        url: str,
        payload: Any,
        subdomain: str = "api",
        stop: Optional[Callable[[], bool]] = None,
    ) -> Iterable[Dict[str, Any]]: ...


class AsyncTransport(Protocol):
    base_url: str

    async def aclose(self) -> None: ...
    async def __aenter__(self): ...
    async def __aexit__(self, exc_type, exc, tb): ...

    async def request_json(
        self, path: str, init: Dict[str, Any], subdomain: str = "api"
    ) -> Any: ...

    async def post_json_with_jwt(
        self, url: str, payload: Any, subdomain: str = "api"
    ) -> Any: ...

    def sse_events(
        self,
        url: str,
        payload: Any,
        subdomain: str = "api",
        signal: Optional[asyncio.Event] = None,
    ) -> AsyncIterable[Dict[str, Any]]: ...
