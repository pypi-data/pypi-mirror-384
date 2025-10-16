from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from typing import (
    Any,
    AsyncGenerator,
    AsyncIterable,
    Awaitable,
    Callable,
    Dict,
    Optional,
)

import aiohttp

from .token_manager_async import TokenManager, TokenManagerOptions
from .types import (
    ChatCompletion,
    ChatCompletionCreateParams,
    ChatCompletionChunk,
    Container,
    ContainerCreateParams,
    ContainerGetParams,
    ManiacOptions,
    ModelsList,
    RegisterCompletionsParams,
    RegisterCompletionsSuccess,
)
from urllib.parse import urlencode
from .utils_training import validate_and_convert_dataset

import ssl
import certifi


def _normalize_params(
    params: Optional[Dict[str, Any]] | None = None, **kwargs: Any
) -> Dict[str, Any]:
    """Merge a dict-like params object with kwargs, with kwargs taking precedence."""
    base: Dict[str, Any] = {}
    if params is not None:
        if isinstance(params, dict):
            base.update(params)
        else:
            raise TypeError("params must be a dict when used with kwargs")
    if kwargs:
        base.update(kwargs)
    return base


async def _raise_json_error(res: aiohttp.ClientResponse):
    try:
        detail = await res.json()
    except Exception:
        try:
            detail = {"message": await res.text()}
        except Exception:
            detail = None
    msg = (detail or {}).get("message") if isinstance(detail, dict) else None
    raise RuntimeError(f"HTTP {res.status} {res.reason}: {msg or detail or ''}")


class AsyncManiac:
    def __init__(self, opts: ManiacOptions | None = None, **kwargs: Any) -> None:
        opts = {**(opts or {}), **kwargs}
        env_api_key = os.environ.get("MANIAC_API_KEY")
        self.apiKey: Optional[str] = opts.get("apiKey") or env_api_key
        self.baseURL: str = (opts.get("baseURL") or "https://api.maniac.ai/").rstrip(
            "/"
        )
        self.baseURLIsCustom: bool = opts.get("baseURL") is not None

        self._session: Optional[aiohttp.ClientSession] = None
        self.tokenManager = TokenManager(
            TokenManagerOptions(
                baseURL=self.baseURL,
                apiKey=self.apiKey or "",
                audience="maniac-gateway",
                session=None,
            )
        )

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            ssl_ctx = ssl.create_default_context(cafile=certifi.where())
            connector = aiohttp.TCPConnector(ssl=ssl_ctx)
            self._session = aiohttp.ClientSession(connector=connector)
            if hasattr(self.tokenManager, "set_session"):
                self.tokenManager.set_session(self._session)
            elif hasattr(self.tokenManager, "session"):
                self.tokenManager.session = self._session
        return self._session

    async def aclose(self) -> None:
        # finish any inflight token refresh
        if getattr(self, "tokenManager", None):
            try:
                await self.tokenManager.aclose()
            except Exception:
                pass
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):  # ergonomic
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.aclose()

    def _headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {
            "content-type": "application/json",
            "maniac-apikey": self.apiKey or "",
        }
        if self.apiKey:
            headers["authorization"] = f"Bearer {self.apiKey}"
        if extra:
            headers.update(extra)
        return headers

    async def _request_json(
        self, path: str, init: Dict[str, Any], subdomain: str = "api"
    ) -> Any:
        session = await self._ensure_session()

        url = f"{self.baseURL.replace('api', subdomain)}{path}"
        async with session.request(
            method=init.get("method") or "GET",
            url=url,
            headers=init.get("headers"),
            data=init.get("body"),
        ) as res:
            if res.status < 200 or res.status >= 300:
                try:
                    text = await res.text()
                except Exception:
                    text = ""
                raise RuntimeError(f"HTTP {res.status} {res.reason}: {text}")
            return await res.json()

    async def _fetch_with_jwt(
        self, url: str, payload: Any, subdomain: str = "api"
    ) -> Any:
        session = await self._ensure_session()

        init = await self.tokenManager.with_auth(
            {
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(payload),
            }
        )
        url_with_sub = f"{self.baseURL.replace('api', subdomain)}{url}"
        async with session.post(
            url_with_sub, headers=init["headers"], data=init["body"]
        ) as res:
            if res.status == 401:
                await self.tokenManager.handle_unauthorized_once()
                fresh = await self.tokenManager.with_auth(
                    {
                        "method": "POST",
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps(payload),
                    }
                )
                async with session.post(
                    url_with_sub, headers=fresh["headers"], data=fresh["body"]
                ) as res2:
                    if not (200 <= res2.status < 300):
                        return await _raise_json_error(res2)
                    return await res2.json()
            if not (200 <= res.status < 300):
                return await _raise_json_error(res)
            return await res.json()

    async def _fetch_sse_with_jwt(
        self,
        url: str,
        payload: Any,
        subdomain: str = "api",
        signal: Optional[asyncio.Event] = None,
    ) -> aiohttp.ClientResponse:
        session = await self._ensure_session()

        init = await self.tokenManager.with_auth(
            {
                "method": "POST",
                "headers": {
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream",
                },
                "body": json.dumps(payload),
            }
        )
        url_with_sub = f"{self.baseURL.replace('api', subdomain)}{url}"
        res = await session.post(
            url_with_sub, headers=init["headers"], data=init["body"]
        )
        if res.status == 401:
            await self.tokenManager.handle_unauthorized_once()
            init = await self.tokenManager.with_auth(init)
            res = await session.post(
                url_with_sub, headers=init["headers"], data=init.get("body")
            )
        if res.status < 200 or res.status >= 300:
            detail: Any = None
            try:
                detail = await res.json()
            except Exception:
                pass
            msg = detail.get("message") if isinstance(detail, dict) else res.reason
            raise RuntimeError(f"Streaming request failed: {res.status} {msg}")
        return res

    async def _read_sse_stream(
        self, resp: aiohttp.ClientResponse, signal: Optional[asyncio.Event] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        buffer = ""
        try:
            async for raw, _ in resp.content.iter_chunks():
                if signal and signal.is_set():
                    break
                if not raw:
                    continue
                buffer += raw.decode("utf-8", errors="ignore")
                while True:
                    sep = "\n\n"
                    idx = buffer.find(sep)
                    if idx == -1:
                        break
                    raw_event = buffer[:idx]
                    buffer = buffer[idx + len(sep) :]
                    for line in raw_event.splitlines():  # handles \r\n too
                        if not line.startswith("data:"):
                            continue
                        data = line.split(":", 1)[1].strip()
                        if not data or data == "[DONE]":
                            if data == "[DONE]":
                                return
                            continue
                        try:
                            yield json.loads(data)
                        except Exception:
                            pass
            remaining = buffer.strip()
            if remaining.startswith("data:"):
                data = remaining[5:].strip()
                if data and data != "[DONE]":
                    try:
                        yield json.loads(data)
                    except Exception:
                        pass
        finally:
            resp.release()

    class _Containers:
        def __init__(self, outer: "AsyncManiac") -> None:
            self._outer = outer

        async def create(
            self, params: ContainerCreateParams | None = None, **kwargs: Any
        ) -> Container:
            params = _normalize_params(params, **kwargs)
            res = await self._outer._request_json(
                "/functions/v1/containers-create-client",
                {
                    "method": "POST",
                    "headers": self._outer._headers(),
                    "body": json.dumps(params),
                },
            )
            return res.get("data")

        async def get(
            self, params: ContainerGetParams | str | None = None, **kwargs: Any
        ) -> Container:
            if isinstance(params, str):
                params = {"label": params}
            params = _normalize_params(params, **kwargs)
            res = await self._outer._request_json(
                "/functions/v1/containers-create-client",
                {
                    "method": "POST",
                    "headers": self._outer._headers(),
                    "body": json.dumps(params),
                },
            )
            return res.get("data")

    class _Completions:
        def __init__(self, outer: "AsyncManiac") -> None:
            self._outer = outer

        async def register(
            self, input: RegisterCompletionsParams | None = None, **kwargs: Any
        ) -> RegisterCompletionsSuccess[Any]:
            input = _normalize_params(input, **kwargs)
            container = input.get("container")
            dataset = input.get("dataset")
            if not container:
                raise RuntimeError("container is required")
            if not isinstance(dataset, list) or len(dataset) == 0:
                raise RuntimeError("dataset must be a non-empty array")

            converted, inferred_system_prompt = validate_and_convert_dataset(dataset)
            task: Dict[str, Any] = {
                "system_prompt": inferred_system_prompt,
                "label": container.get("label"),
            }
            payload = {"task": task, "data": converted}
            raw = await self._outer._request_json(
                "/functions/v1/direct-insert",
                {
                    "method": "POST",
                    "headers": self._outer._headers(),
                    "body": json.dumps(payload),
                },
                "api" if self._outer.baseURLIsCustom else "inference",
            )
            return {
                "status": "ok",
                "label": container.get("label"),
                "dataCount": len(converted),
                "raw": raw,
            }

        async def create(
            self, params: ChatCompletionCreateParams | None = None, **kwargs: Any
        ) -> ChatCompletion:
            body: Dict[str, Any]
            params = _normalize_params(params, **kwargs)
            container = params.get("container")
            messages = params.get("messages") or []
            rest = {
                k: v for k, v in params.items() if k not in ("container", "messages")
            }

            if not container:
                body = {**rest, "model": rest.get("model") or "openai/gpt-4o-mini"}
                body["messages"] = messages
            else:
                container_body = container.get("inference_body", {})
                system_prompt = container_body.get("system_prompt")
                rest_of_container = {
                    k: v for k, v in container_body.items() if k != "system_prompt"
                }
                messages_with_system = messages
                if system_prompt:
                    messages_with_system = [
                        {"role": "system", "content": system_prompt}
                    ] + messages
                body = {**rest, **rest_of_container, "messages": messages_with_system}

            res = await self._outer._fetch_with_jwt(
                "/v1/chat/completions",
                body,
                "api" if self._outer.baseURLIsCustom else "inference",
            )
            res = {
                **res,
                "output_text": (res.get("choices") or [{}])[0]
                .get("message", {})
                .get("content", ""),
            }
            return res

        async def create_with_stream(
            self,
            params: ChatCompletionCreateParams | None = None,
            signal: Optional[asyncio.Event] = None,
            **kwargs: Any,
        ) -> AsyncIterable[ChatCompletionChunk]:
            params = _normalize_params(params, **kwargs)
            container = params.get("container")
            messages = params.get("messages") or []
            rest = {
                k: v for k, v in params.items() if k not in ("container", "messages")
            }

            if not container:
                body = {
                    **rest,
                    "model": rest.get("model") or "openai/gpt-4o-mini",
                    "stream": True,
                    "messages": messages,
                }
            else:
                container_body = container.get("inference_body", {})
                system_prompt = container_body.get("system_prompt")
                rest_of_container = {
                    k: v for k, v in container_body.items() if k != "system_prompt"
                }
                messages_with_system = [
                    {"role": "system", "content": system_prompt}
                ] + messages
                body = {
                    **rest,
                    **rest_of_container,
                    "stream": True,
                    "messages": messages_with_system,
                }

            sub = "api" if self._outer.baseURLIsCustom else "inference"
            res = await self._outer._fetch_sse_with_jwt(
                "/v1/chat/completions", body, sub, signal
            )
            async for evt in self._outer._read_sse_stream(res, signal):
                yield evt

        async def stream(
            self,
            params: ChatCompletionCreateParams | None = None,
            callback: Optional[Callable[[ChatCompletionChunk], Awaitable[None]]] = None,
            **kwargs: Any,
        ) -> AsyncIterable[ChatCompletionChunk] | None:
            if callback is None:
                return self.create_with_stream(params, **kwargs)
            async for chunk in self.create_with_stream(params, **kwargs):
                await callback(chunk)
            return None

    class _Models:
        def __init__(self, outer: "AsyncManiac") -> None:
            self._outer = outer

        async def list(self) -> ModelsList:
            return await self._outer._request_json(
                "/functions/v1/models",
                {"method": "GET", "headers": self._outer._headers()},
            )

        async def retrieve(self, id: str):
            qs = urlencode({"id": id})
            return await self._outer._request_json(
                f"/functions/v1/models?{qs}",
                {"method": "GET", "headers": self._outer._headers()},
            )

    @property
    def containers(self) -> "AsyncManiac._Containers":
        return AsyncManiac._Containers(self)

    @property
    def chat(self) -> Any:
        class _Chat:
            def __init__(self, outer: "AsyncManiac") -> None:
                self.completions = AsyncManiac._Completions(outer)

        return _Chat(self)

    @property
    def completions(self) -> Any:
        class _Comps:
            def __init__(self, outer: "AsyncManiac") -> None:
                self.register = AsyncManiac._Completions(outer).register

        return _Comps(self)

    @property
    def models(self) -> Any:
        class _Models:
            def __init__(self, outer: "AsyncManiac") -> None:
                self.list = AsyncManiac._Models(outer).list
                self.retrieve = AsyncManiac._Models(outer).retrieve

        return _Models(self)
