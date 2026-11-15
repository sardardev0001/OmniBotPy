"""Safe async HTTP transport for Telegram-like JSON envelope APIs.

Never log token-bearing URLs. Retry only read-only getUpdates/getMe calls, not sends.
"""
from __future__ import annotations
import asyncio
import json
import mimetypes
import re
from pathlib import Path
from typing import Any
import httpx
from .errors import APIError, RateLimitError, TransportError

_METHOD_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")

class HTTPTransport:
    def __init__(self, token: str, base_url: str, *, timeout: float = 35.0,
                 client: httpx.AsyncClient | None = None, retries: int = 2):
        if not token or any(ch in token for ch in "/?#\r\n"):
            raise ValueError("Invalid token format")
        if not (base_url.startswith("https://") or base_url.startswith("http://127.0.0.1")
                or base_url.startswith("http://localhost")):
            raise ValueError("API base URL must use HTTPS (localhost exception)")
        if retries < 0:
            raise ValueError("retries must be non-negative")
        self._token = token
        self._base_url = base_url.rstrip("/")
        self._client = client or httpx.AsyncClient(timeout=timeout)
        self._owned = client is None
        self._timeout = timeout
        self._retries = retries

    async def close(self) -> None:
        if self._owned:
            await self._client.aclose()

    async def __aenter__(self) -> HTTPTransport:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    @staticmethod
    def _clean(value: Any) -> Any:
        if hasattr(value, "model_dump"):
            return HTTPTransport._clean(value.model_dump(exclude_none=True))
        if hasattr(value, "to_dict"):
            return HTTPTransport._clean(value.to_dict())
        if isinstance(value, dict):
            return {k: HTTPTransport._clean(v) for k, v in value.items() if v is not None}
        if isinstance(value, (tuple, list)):
            return [HTTPTransport._clean(v) for v in value]
        return value

    async def request(self, method: str, payload: dict[str, Any] | None = None, *,
                      files: dict[str, tuple[str, bytes, str]] | None = None) -> Any:
        if not _METHOD_RE.fullmatch(method):
            raise ValueError("Invalid API method name")
        url = f"{self._base_url}{self._token}/{method}"
        data = self._clean(payload or {})
        safe_to_retry = method in {"getUpdates", "getMe", "getWebhookInfo", "getFile", "getChat"} and not files
        attempts = 1 + (self._retries if safe_to_retry else 0)
        for attempt in range(attempts):
            try:
                if files:
                    form = {k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)
                            for k, v in data.items()}
                    response = await self._client.post(url, data=form, files=files,
                                                       timeout=self._timeout)
                else:
                    response = await self._client.post(
                        url, json=data, timeout=max(self._timeout, float(data.get("timeout", 0)) + 10))
                try:
                    result = response.json()
                except (ValueError, UnicodeDecodeError):
                    raise TransportError(f"Invalid JSON response for {method}") from None
            except httpx.HTTPError:
                if attempt + 1 < attempts:
                    await asyncio.sleep(min(2 ** attempt, 5))
                    continue
                raise TransportError(f"HTTP transport failure calling {method}") from None
            if not isinstance(result, dict):
                raise TransportError(f"Non-object response calling {method}")
            if result.get("ok") is False:
                params = result.get("parameters") or {}
                after = params.get("retry_after") if isinstance(params, dict) else None
                code = result.get("error_code") or response.status_code
                # Server-controlled error messages can contain the token; redact it.
                desc = str(result.get("description", "Unknown API error")).replace(self._token, "[REDACTED]")
                error_cls = RateLimitError if code == 429 else APIError
                raise error_cls(method, code, desc, after)
            if response.status_code >= 400:
                raise TransportError(f"HTTP {response.status_code} calling {method}")
            if "result" not in result:
                raise TransportError(f"Missing API result for {method}")
            return result["result"]
        raise TransportError(f"Request failed for {method}")
