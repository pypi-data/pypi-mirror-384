import httpx
import time
import json
import threading
from typing import Any, Dict, Optional
from datetime import datetime, timezone

try:
    import certifi

    _VERIFY = certifi.where()
except Exception:
    _VERIFY = True


class TokenManager:
    def __init__(
        self,
        baseURL: str,
        apiKey: str,
        audience: str = "maniac-gateway",
        token_path: str = "/functions/v1/verify-api-key-and-mint-jwt",
        skew_seconds: int = 90,
        timeout: float = 20.0,
        extra_headers: Optional[Dict[str, str]] = None,
    ):
        self.baseURL = baseURL.rstrip("/")
        self.apiKey = apiKey
        self.audience = audience
        self.token_path = token_path
        self.skew = skew_seconds
        self._token: Optional[str] = None
        self._exp = 0
        self._lock = threading.RLock()
        self._client = httpx.Client(timeout=timeout, http2=True, verify=_VERIFY)
        self._extra_headers = extra_headers or {}

    def close(self) -> None:
        self._client.close()

    def with_auth(self, init: Dict[str, Any]) -> Dict[str, Any]:
        self._ensure_fresh_token()
        headers = {
            **(init.get("headers") or {}),
            "Authorization": f"Bearer {self._token}",
        }
        if self._extra_headers:
            headers.update(self._extra_headers)
        return {**init, "headers": headers}

    def handle_unauthorized_once(self) -> None:
        with self._lock:
            self._token = None
            self._exp = 0

    def _ensure_fresh_token(self) -> None:
        now = int(time.time())
        if self._token and now < (self._exp - self.skew):
            return
        with self._lock:
            now = int(time.time())
            if self._token and now < (self._exp - self.skew):
                return
            minted = self._mint_with_retries()
            self._token = minted["token"]
            self._exp = self._parse_exp(minted)

    def _mint_with_retries(
        self, attempts: int = 3, base_delay: float = 0.25
    ) -> Dict[str, Any]:
        last_err = None
        for i in range(attempts):
            try:
                r = self._client.post(
                    f"{self.baseURL}{self.token_path}",
                    headers={
                        "Authorization": f"Bearer {self.apiKey}",
                        "maniac-apikey": self.apiKey,
                        "Content-Type": "application/json",
                    },
                    json={"audience": self.audience},
                )
                r.raise_for_status()
                return r.json()
            except httpx.HTTPError as e:
                last_err = e
                time.sleep(base_delay * (2**i))
        raise last_err

    @staticmethod
    def _parse_exp(minted: Dict[str, Any]) -> int:
        if "expires_at" in minted:
            try:
                return int(minted["expires_at"])
            except Exception:
                pass
        if "expires_in" in minted:
            try:
                return int(time.time()) + int(minted["expires_in"])
            except Exception:
                pass
        if "expires_at" in minted and isinstance(minted["expires_at"], str):
            try:
                dt = datetime.fromisoformat(minted["expires_at"].replace("Z", "+00:00"))
                return int(dt.replace(tzinfo=timezone.utc).timestamp())
            except Exception:
                pass
        return int(time.time()) + 30
