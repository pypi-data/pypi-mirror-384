from __future__ import annotations

from typing import Any

from bdsca_analysis_config_file import BlackDuckRemediator
from bdsca_analysis_config_file.endpoint_mocks import EndpointRegistry, MockResponse, MockSession


class _FakeHub:
    def __init__(self) -> None:
        # Provide baseurl so RemediatorBase can build absolute URLs
        self.config = {"insecure": False, "baseurl": "http://bd"}

    def get_headers(self) -> dict[str, str]:
        return {}

    def get_projects(self, limit: int, parameters: dict[str, Any]) -> dict[str, Any]:
        # Always resolve to project id 1
        return {"items": [{"_meta": {"href": "http://bd/api/projects/1"}}]}

    def _get_parameter_string(self, parameters: dict[str, Any]) -> str:  # pragma: no cover - compatibility
        from urllib.parse import urlencode

        return "?" + urlencode(parameters)


def test_add_components_posts_correct_payload_and_headers() -> None:
    registry = EndpointRegistry()
    session = MockSession(registry)

    # Compose remediator and stub versions lookup to return a version id
    remediator = BlackDuckRemediator(hub=_FakeHub(), session=session)
    remediator._call_project_versions = lambda project, version_name: {"items": [{"_meta": {"href": "http://bd/api/projects/1/versions/2"}}]}  # type: ignore[assignment]

    bom_url = "http://bd/api/projects/1/versions/2/components"

    # First, BOM does not contain the component -> should POST add
    def bom_get_handler(url: str, body: dict[str, Any] | None, headers: dict[str, Any] | None) -> MockResponse:
        # Verify Accept header used by check_component_exists_in_bom
        assert headers is not None
        assert headers.get("Accept") == "application/vnd.blackducksoftware.bill-of-materials-6+json"
        return MockResponse(200, {"items": []})

    registry.register("GET", bom_url, bom_get_handler)

    posted = {"count": 0}

    def bom_post_handler(url: str, body: dict[str, Any] | None, headers: dict[str, Any] | None) -> MockResponse:
        posted["count"] += 1
        assert headers is not None
        # Verify Content-Type header used by add_component_to_bom
        assert headers.get("Content-Type") == "application/vnd.blackducksoftware.bill-of-materials-6+json"
        assert isinstance(body, dict)
        # Verify minimal payload shape
        assert body.get("componentModification") == "add"
        assert isinstance(body.get("component"), str)
        return MockResponse(201, {"status": "OK"})

    registry.register("POST", bom_url, bom_post_handler)
    # Also mock the components-in-use lookup the implementation performs
    from urllib.parse import urlencode

    comps_q = urlencode({"limit": 30, "q": "compX"})
    comps_url = "http://bd/api/search/components-in-use?" + comps_q

    def comps_handler(url: str, body: dict[str, Any] | None, headers: dict[str, Any] | None) -> MockResponse:
        return MockResponse(
            200,
            {
                "items": [
                    {
                        "componentVersion": "1.0.0",
                        "_meta": {"href": "http://bd/api/components/90/versions/100"},
                    }
                ]
            },
        )

    registry.register("GET", comps_url, comps_handler)

    # Run add now that lookup is registered
    res = remediator.add_missing_components_from_config(
        project_name="p",
        project_version_name="1",
        component_additions=[{"component": {"name": "compX", "version": "1.0.0"}}],
    )
    assert len(res) == 1
    assert res[0]["added"] is True
    assert posted["count"] == 1


def test_add_components_skips_when_exists_in_bom() -> None:
    registry = EndpointRegistry()
    session = MockSession(registry)

    remediator = BlackDuckRemediator(hub=_FakeHub(), session=session)
    remediator._call_project_versions = lambda project, version_name: {"items": [{"_meta": {"href": "http://bd/api/projects/1/versions/2"}}]}  # type: ignore[assignment]

    bom_url = "http://bd/api/projects/1/versions/2/components"

    # Simulate component existing in BOM
    registry.register(
        "GET",
        bom_url,
        lambda url, body, headers: MockResponse(
            200,
            {"items": [{"componentName": "compX", "componentVersion": "1.0.0"}]},
        ),
    )

    # If a POST happens, fail the test (should be skipped)
    def unexpected_post(url: str, body: dict[str, Any] | None, headers: dict[str, Any] | None) -> MockResponse:  # pragma: no cover - negative path
        raise AssertionError("POST should not be called when component exists in BOM")

    registry.register("POST", bom_url, unexpected_post)

    res = remediator.add_missing_components_from_config(
        project_name="p",
        project_version_name="1",
        component_additions=[{"component": {"name": "compX", "version": "1.0.0"}}],
    )
    assert len(res) == 1
    assert res[0]["added"] is False


def test_add_components_uses_purl_version_url_in_payload(monkeypatch: Any) -> None:
    registry = EndpointRegistry()
    session = MockSession(registry)

    remediator = BlackDuckRemediator(hub=_FakeHub(), session=session)
    remediator._call_project_versions = lambda project, version_name: {"items": [{"_meta": {"href": "http://bd/api/projects/1/versions/2"}}]}  # type: ignore[assignment]

    # Mock get_component_by_purl to return a payload that includes a version URL
    def fake_get_component_by_purl(purl: str) -> dict[str, Any] | None:
        assert purl == "pkg:pypi/compY@2.0.0"
        return {
            "items": [
                {
                    "componentName": "compY",
                    "versionName": "2.0.0",
                    "version": "http://bd/api/components/42/versions/99",  # URL expected to be used in payload
                }
            ]
        }

    monkeypatch.setattr(remediator, "get_component_by_purl", fake_get_component_by_purl)

    bom_url = "http://bd/api/projects/1/versions/2/components"

    # BOM is empty -> add should POST
    registry.register("GET", bom_url, lambda url, body, headers: MockResponse(200, {"items": []}))

    captured: dict[str, Any] = {"payload": None}

    def post_handler(url: str, body: dict[str, Any] | None, headers: dict[str, Any] | None) -> MockResponse:
        captured["payload"] = body
        return MockResponse(201, {"status": "OK"})

    registry.register("POST", bom_url, post_handler)

    # Register components-in-use lookup (current implementation performs this even when PURL is provided)
    from urllib.parse import urlencode

    comps_q = urlencode({"limit": 30, "q": "compY"})
    comps_url = "http://bd/api/search/components-in-use?" + comps_q

    def comps_handler(url: str, body: dict[str, Any] | None, headers: dict[str, Any] | None) -> MockResponse:
        return MockResponse(
            200,
            {
                "items": [
                    {
                        "componentVersion": "2.0.0",
                        # Return the same href as the PURL version URL to satisfy payload assertion
                        "_meta": {"href": "http://bd/api/components/42/versions/99"},
                    }
                ]
            },
        )

    registry.register("GET", comps_url, comps_handler)

    res = remediator.add_missing_components_from_config(
        project_name="p",
        project_version_name="1",
        component_additions=[{"component": {"purl": "pkg:pypi/compY@2.0.0"}}],
    )
    assert len(res) == 1
    assert res[0]["added"] is True
    assert isinstance(captured["payload"], dict)
    # Ensure the component field is set to the version URL from the purl lookup
    assert captured["payload"]["component"] == "http://bd/api/components/42/versions/99"

    # (lookup already registered above)


def test_add_components_purl_lookup_missing_falls_back_to_version(monkeypatch: Any) -> None:
    registry = EndpointRegistry()
    session = MockSession(registry)

    remediator = BlackDuckRemediator(hub=_FakeHub(), session=session)
    remediator._call_project_versions = lambda project, version_name: {"items": [{"_meta": {"href": "http://bd/api/projects/1/versions/2"}}]}  # type: ignore[assignment]

    # Mock PURL lookup to return None (not found)
    monkeypatch.setattr(remediator, "get_component_by_purl", lambda p: None)

    bom_url = "http://bd/api/projects/1/versions/2/components"

    # BOM is empty -> add should POST
    registry.register("GET", bom_url, lambda url, body, headers: MockResponse(200, {"items": []}))

    captured: dict[str, dict[str, Any] | None] = {"payload": None}

    def post_handler(url: str, body: dict[str, Any] | None, headers: dict[str, Any] | None) -> MockResponse:
        captured["payload"] = body
        return MockResponse(201, {"status": "OK"})

    registry.register("POST", bom_url, post_handler)

    # Register components-in-use to provide an href and assert it's used
    from urllib.parse import urlencode

    comps_q = urlencode({"limit": 30, "q": "compZ"})
    comps_url = "http://bd/api/search/components-in-use?" + comps_q

    def comps_handler(url: str, body: dict[str, Any] | None, headers: dict[str, Any] | None) -> MockResponse:
        return MockResponse(
            200,
            {
                "items": [
                    {
                        "componentVersion": "3.0.0",
                        "_meta": {"href": "http://bd/api/components/88/versions/200"},
                    }
                ]
            },
        )

    registry.register("GET", comps_url, comps_handler)

    # Provide both purl and name/version to exercise resolution via components-in-use
    res = remediator.add_missing_components_from_config(
        project_name="p",
        project_version_name="1",
        component_additions=[{"component": {"purl": "pkg:pypi/compZ@3.0.0", "name": "compZ", "version": "3.0.0"}}],
    )
    assert len(res) == 1
    assert res[0]["added"] is True
    assert isinstance(captured["payload"], dict)

    # Perform another add using same inputs to capture href-based payload
    captured = {"payload": None}

    def post_handler2(url: str, body: dict[str, Any] | None, headers: dict[str, Any] | None) -> MockResponse:
        captured["payload"] = body
        return MockResponse(201, {"status": "OK"})

    registry.register("POST", bom_url, post_handler2)

    res = remediator.add_missing_components_from_config(
        project_name="p",
        project_version_name="1",
        component_additions=[{"component": {"purl": "pkg:pypi/compZ@3.0.0", "name": "compZ", "version": "3.0.0"}}],
    )
    assert len(res) == 1
    assert res[0]["added"] is True
    assert isinstance(captured["payload"], dict)
    assert captured["payload"]["component"] == "http://bd/api/components/88/versions/200"


def test_add_components_with_empty_version_posts_empty_string() -> None:
    registry = EndpointRegistry()
    session = MockSession(registry)

    remediator = BlackDuckRemediator(hub=_FakeHub(), session=session)
    remediator._call_project_versions = lambda project, version_name: {"items": [{"_meta": {"href": "http://bd/api/projects/1/versions/2"}}]}  # type: ignore[assignment]

    bom_url = "http://bd/api/projects/1/versions/2/components"
    registry.register("GET", bom_url, lambda url, body, headers: MockResponse(200, {"items": []}))

    captured: dict[str, dict[str, Any] | None] = {"payload": None}

    def post_handler(url: str, body: dict[str, Any] | None, headers: dict[str, Any] | None) -> MockResponse:
        captured["payload"] = body
        return MockResponse(201, {"status": "OK"})

    registry.register("POST", bom_url, post_handler)

    # Register lookup with empty version to drive href resolution
    from urllib.parse import urlencode

    comps_q = urlencode({"limit": 30, "q": "compE"})
    comps_url = "http://bd/api/search/components-in-use?" + comps_q

    def comps_handler(url: str, body: dict[str, Any] | None, headers: dict[str, Any] | None) -> MockResponse:
        return MockResponse(
            200,
            {
                "items": [
                    {
                        "componentVersion": "",
                        "_meta": {"href": "http://bd/api/components/66/versions/1"},
                    }
                ]
            },
        )

    registry.register("GET", comps_url, comps_handler)

    res = remediator.add_missing_components_from_config(
        project_name="p",
        project_version_name="1",
        component_additions=[{"component": {"name": "compE", "version": ""}}],
    )
    assert len(res) == 1
    assert res[0]["added"] is True
    assert isinstance(captured["payload"], dict)
    # Expect href resolved via components-in-use for empty version
    assert captured["payload"]["component"] == "http://bd/api/components/66/versions/1"


def test_add_components_resolves_version_url_via_components_search(monkeypatch: Any) -> None:
    registry = EndpointRegistry()
    session = MockSession(registry)

    remediator = BlackDuckRemediator(hub=_FakeHub(), session=session)
    remediator._call_project_versions = lambda project, version_name: {"items": [{"_meta": {"href": "http://bd/api/projects/1/versions/2"}}]}  # type: ignore[assignment]

    # Ensure PURL path isn't used
    monkeypatch.setattr(remediator, "get_component_by_purl", lambda p: None)

    bom_url = "http://bd/api/projects/1/versions/2/components"

    registry.register("GET", bom_url, lambda url, body, headers: MockResponse(200, {"items": []}))

    # Intercept the current implementation's search endpoint and verify headers
    from urllib.parse import urlencode

    expected_q = urlencode({"limit": 30, "q": "compS"})
    comps_url = "http://bd/api/search/components-in-use?" + expected_q

    def comps_handler(url: str, body: dict[str, Any] | None, headers: dict[str, Any] | None) -> MockResponse:
        assert headers is not None
        # Current implementation uses internal accept with fallback json
        assert headers.get("Accept") == "application/vnd.blackducksoftware.internal-1+json, application/json"
        # Return a payload containing a componentVersion that matches and a meta href to use
        return MockResponse(
            200,
            {
                "items": [
                    {
                        "componentVersion": "5.0.0",
                        "_meta": {"href": "http://bd/api/components/77/versions/123"},
                    }
                ]
            },
        )

    registry.register("GET", comps_url, comps_handler)

    captured: dict[str, dict[str, Any] | None] = {"payload": None}

    def post_handler(url: str, body: dict[str, Any] | None, headers: dict[str, Any] | None) -> MockResponse:
        captured["payload"] = body
        return MockResponse(201, {"status": "OK"})

    registry.register("POST", bom_url, post_handler)

    res = remediator.add_missing_components_from_config(
        project_name="p",
        project_version_name="1",
        component_additions=[{"component": {"name": "compS", "version": "5.0.0"}}],
    )
    assert len(res) == 1
    assert res[0]["added"] is True
    assert isinstance(captured["payload"], dict)
    assert captured["payload"]["component"] == "http://bd/api/components/77/versions/123"
