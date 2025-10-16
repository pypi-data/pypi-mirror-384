# token_manager.py  (replace the second/active class with this)

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import aiohttp
import ssl

try:
    import certifi

    _CERT_PATH = certifi.where()
except Exception:
    _CERT_PATH = None


@dataclass
class TokenManagerOptions:
    baseURL: str
    apiKey: str
    audience: Optional[str] = None
    scopes: Optional[List[str]] = None
    minimumDollars: Optional[float] = None
    skewSeconds: int = 30
    session: Optional[aiohttp.ClientSession] = None  # << already present


class TokenManager:
    def __init__(self, opts: TokenManagerOptions) -> None:
        self.audience = opts.audience
        self.scopes = opts.scopes
        self.minimumDollars = opts.minimumDollars
        self.baseURL = opts.baseURL.rstrip("/")
        self.apiKey = opts.apiKey
        self.skewSeconds = opts.skewSeconds

        self._session: Optional[aiohttp.ClientSession] = opts.session
        self._owns_session: bool = opts.session is None

        self._token: Optional[str] = None
        self._exp: Optional[int] = None
        self._inflight: Optional[asyncio.Task[None]] = None

        # optional: protect concurrent first-use races
        self._sess_lock = asyncio.Lock()

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            async with self._sess_lock:
                if self._session is None or self._session.closed:
                    ctx = (
                        ssl.create_default_context(cafile=_CERT_PATH)
                        if _CERT_PATH
                        else ssl.create_default_context()
                    )
                    self._session = aiohttp.ClientSession(
                        connector=aiohttp.TCPConnector(ssl=ctx)
                    )
                    self._owns_session = True
        return self._session

    def set_session(self, session: aiohttp.ClientSession) -> None:
        if self._owns_session and self._session and not self._session.closed:
            pass
        self._session = session
        self._owns_session = False

    async def aclose(self) -> None:
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()

    async def get_token(self) -> str:
        if self._is_fresh():
            return self._token or ""
        if self._inflight is None:
            self._inflight = asyncio.create_task(self._refresh())
        try:
            await self._inflight
        finally:
            self._inflight = None
        if not self._token:
            raise RuntimeError("Failed to mint JWT")
        return self._token

    async def with_auth(self, init: Dict[str, Any] | None = None) -> Dict[str, Any]:
        init = init or {}
        headers: Dict[str, str] = {**(init.get("headers") or {})}
        token = await self.get_token()
        headers["Authorization"] = f"Bearer {token}"
        return {**init, "headers": headers}

    async def handle_unauthorized_once(self) -> None:
        await self._refresh(force=True)

    def _is_fresh(self) -> bool:
        return bool(
            self._token
            and self._exp
            and (int(time.time()) + self.skewSeconds < self._exp)
        )

    async def _refresh(self, force: bool = False) -> None:
        if not force and self._is_fresh():
            return

        body: Dict[str, Any] = {
            "audience": self.audience,
            "scopes": self.scopes,
            "minimumDollars": self.minimumDollars,
        }

        session = await self._ensure_session()
        async with session.post(
            f"{self.baseURL}/functions/v1/verify-api-key-and-mint-jwt",
            json=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.apiKey}",
            },
        ) as res:
            try:
                data: Dict[str, Any] = await res.json()
            except Exception:
                data = {}

            if not data or not data.get("ok"):
                self._token = None
                self._exp = None
                reason = (
                    f"HTTP {res.status}"
                    if not data
                    else f"{data.get('code')} ({data.get('status')}): {data.get('message')}"
                )
                raise RuntimeError(f"Mint failed: {reason}")

            self._token = data.get("token")
            self._exp = data.get("expires_at")
