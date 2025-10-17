from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


class MockResponse:
    """Minimal requests.Response-like object for tests.

    - status_code: HTTP status code
    - headers: optional headers
    - text: body as string
    - json(): parses body as JSON, raises ValueError if invalid
    - ok: True if status_code in 200..299
    """

    def __init__(
        self,
        status_code: int = 200,
        body: Any | None = None,
        headers: dict[str, str] | None = None,
    ):
        self.status_code = status_code
        self.headers = headers or {}
        if body is None:
            self.text = ""
        elif isinstance(body, (dict, list)):
            self.text = json.dumps(body)
        else:
            self.text = str(body)

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self) -> Any:
        if not self.text:
            return None
        return json.loads(self.text)


Handler = Callable[[str, Optional[dict[Any, Any]], Optional[dict[Any, Any]]], MockResponse]


@dataclass
class _Route:
    method: str
    url: str
    handler: Handler


class EndpointRegistry:
    """Registry of mock endpoints keyed by (method, url)."""

    def __init__(self) -> None:
        self._routes: dict[tuple[str, str], Handler] = {}

    def register(self, method: str, url: str, handler: Handler) -> None:
        key = (method.upper(), url)
        self._routes[key] = handler

    def clear(self) -> None:
        self._routes.clear()

    def dispatch(
        self,
        method: str,
        url: str,
        json_body: dict[Any, Any] | None = None,
        headers: dict[Any, Any] | None = None,
    ) -> MockResponse:
        key = (method.upper(), url)
        handler = self._routes.get(key)
        if handler is None:
            return MockResponse(404, {"error": f"No mock for {method} {url}"})
        try:
            return handler(url, json_body, headers)
        except Exception as ex:  # pragma: no cover - allow tests to assert failures
            return MockResponse(500, {"error": str(ex)})


class MockSession:
    """A lightweight session mimicking requests.Session.

    Supports get/post/put/delete with JSON bodies and returns MockResponse.
    """

    def __init__(self, registry: EndpointRegistry | None = None):
        self.registry = registry or EndpointRegistry()
        self.headers: dict[str, str] = {}

    def request(
        self,
        method: str,
        url: str,
        json: dict | None = None,
        headers: dict | None = None,
        **kwargs: Any,
    ) -> MockResponse:
        merged_headers = {**self.headers, **(headers or {})}
        # Emulate requests 'params' behavior by appending to URL
        params = kwargs.get("params")
        if params:
            try:
                parsed = urlparse(url)
                existing = dict(parse_qsl(parsed.query))
                existing.update(params)
                new_query = urlencode(existing)
                url = urlunparse(parsed._replace(query=new_query))
            except Exception:
                # If parsing fails, fall back to naive concatenation
                sep = "&" if "?" in url else "?"
                url = f"{url}{sep}{urlencode(params)}"
        return self.registry.dispatch(method, url, json, merged_headers)

    def get(self, url: str, headers: dict | None = None, **kwargs: Any) -> MockResponse:
        return self.request("GET", url, headers=headers, **kwargs)

    def post(
        self,
        url: str,
        json: dict | None = None,
        headers: dict | None = None,
        **kwargs: Any,
    ) -> MockResponse:  # noqa: A002 - shadow built-in for signature parity
        return self.request("POST", url, json=json, headers=headers, **kwargs)

    def put(
        self,
        url: str,
        json: dict | None = None,
        headers: dict | None = None,
        **kwargs: Any,
    ) -> MockResponse:
        return self.request("PUT", url, json=json, headers=headers, **kwargs)

    def delete(self, url: str, headers: dict | None = None, **kwargs: Any) -> MockResponse:
        return self.request("DELETE", url, headers=headers, **kwargs)


__all__ = [
    "MockResponse",
    "EndpointRegistry",
    "MockSession",
]
