from __future__ import annotations

from typing import Any

from bdsca_analysis_config_file.endpoint_mocks import EndpointRegistry, MockResponse, MockSession


def test_mocksession_appends_params_to_url() -> None:
    registry = EndpointRegistry()
    session = MockSession(registry)

    def handler(url: str, body: dict[Any, Any] | None, headers: dict[Any, Any] | None) -> MockResponse:
        assert url == "http://svc/items?limit=10&offset=20"
        return MockResponse(200, {"ok": True})

    registry.register("GET", "http://svc/items?limit=10&offset=20", handler)

    resp = session.get("http://svc/items", params={"limit": 10, "offset": 20})
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_missing_route_returns_404() -> None:
    registry = EndpointRegistry()
    session = MockSession(registry)

    resp = session.get("http://no-route")
    assert resp.status_code == 404
    assert "No mock for GET http://no-route" in resp.text


def test_register_override_last_handler_wins() -> None:
    registry = EndpointRegistry()
    session = MockSession(registry)

    registry.register("GET", "http://svc/ping", lambda u, b, h: MockResponse(200, {"v": 1}))
    registry.register("GET", "http://svc/ping", lambda u, b, h: MockResponse(200, {"v": 2}))

    resp = session.get("http://svc/ping")
    assert resp.status_code == 200
    assert resp.json()["v"] == 2
