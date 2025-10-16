# maniac/transports/httpx_sync.py
import httpx, json, ssl, certifi
from typing import Any, Dict, Iterable


class HttpxTransport:
    def __init__(self, base_url: str, token_manager):
        self.base_url = base_url.rstrip("/")
        self.base_is_custom = "api." not in self.base_url  # or pass a flag in
        self.tm = token_manager
        self.client = httpx.Client(verify=certifi.where(), http2=True, timeout=60)

    def _sub(self, sub: str) -> str:
        return self.base_url.replace("api", sub)

    def request_json(
        self, path: str, init: Dict[str, Any], subdomain: str = "api"
    ) -> Any:
        url = f"{self._sub(subdomain)}{path}"
        r = self.client.request(
            init.get("method", "GET"),
            url,
            headers=init.get("headers"),
            content=init.get("body"),
        )
        r.raise_for_status()
        return r.json()

    def post_json_with_jwt(self, url: str, payload: Any, subdomain: str = "api") -> Any:
        url = f"{self._sub(subdomain)}{url}"
        init = self.tm.with_auth(
            {
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(payload),
            }
        )
        r = self.client.post(url, headers=init["headers"], content=init["body"])
        if r.status_code == 401:
            self.tm.handle_unauthorized_once()
            init = self.tm.with_auth(init)
            r = self.client.post(url, headers=init["headers"], content=init["body"])
        r.raise_for_status()
        return r.json()

    def sse_events(self, url: str, payload: Any, subdomain: str = "api"):
        url = f"{self._sub(subdomain)}{url}"
        init = self.tm.with_auth(
            {
                "method": "POST",
                "headers": {
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream",
                },
                "body": json.dumps(payload),
            }
        )
        with self.client.stream(
            "POST", url, headers=init["headers"], content=init["body"]
        ) as r:
            r.raise_for_status()
            # Basic SSE line parser
            buf = ""
            for chunk in r.iter_text():
                if not chunk:
                    continue
                buf += chunk
                while "\n\n" in buf:
                    raw, buf = buf.split("\n\n", 1)
                    for line in raw.splitlines():
                        if not line.startswith("data:"):
                            continue
                        data = line[5:].strip()
                        if not data or data == "[DONE]":
                            if data == "[DONE]":
                                return
                            continue
                        try:
                            yield json.loads(data)
                        except Exception:
                            continue
