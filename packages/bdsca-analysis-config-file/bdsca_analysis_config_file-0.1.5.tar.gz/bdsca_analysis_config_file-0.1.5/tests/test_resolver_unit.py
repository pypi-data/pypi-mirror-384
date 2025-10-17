from __future__ import annotations

from typing import Any, NoReturn

from bdsca_analysis_config_file.remediator_base import RemediatorBase


class _FakeHub:
    def __init__(self) -> None:
        self.config = {"insecure": False}

    def get_headers(self) -> dict[str, str]:
        return {}


class _DummySession:
    """Minimal requests-like session to prevent real HTTP in unit tests."""

    def get(self, url: str, headers: dict[str, str] | None = None, verify: bool | None = None) -> NoReturn:  # pragma: no cover - negative path
        raise AssertionError("Network call not expected in unit test: GET " + url)


class _TestBase(RemediatorBase):
    def __init__(self) -> None:
        # Provide a dummy session so RemediatorBase doesn't import 'requests' in CI
        super().__init__(hub=_FakeHub(), session=_DummySession())
        self.calls: int = 0
        self.payload_to_return: dict[str, Any] | None = None

    def get_component_by_purl(self, purl: str) -> dict[str, Any] | None:
        self.calls += 1
        return self.payload_to_return


def _purl_payload(name: str, version_name: str, origin_id: str, version_url: str = "") -> dict[str, Any]:
    return {
        "items": [
            {
                # Keys expected by _extract_component_from_purl_payload
                "componentName": name,
                "versionName": version_name,
                # Current implementation extracts 'version' as a URL if present
                # and 'originId' for the origin identifier
                **({"version": version_url} if version_url else {}),
                "originId": origin_id,
            }
        ]
    }


def test_resolve_component_identity_purl_uses_cache() -> None:
    base = _TestBase()
    base.payload_to_return = _purl_payload("A", "1.2.3", "orig-1")

    # First resolve will call get_component_by_purl
    name, version_url, version_name, origin_url, origin_id = base.resolve_component_identity({"purl": "pkg:pypi/A@1.2.3"})
    assert (name, version_url, version_name, origin_url, origin_id) == ("A", "", "1.2.3", "", "orig-1")
    assert base.calls == 1

    # Second resolve should use the _purl_component_cache and not call again
    name2, version_url2, version_name2, origin_url2, origin_id2 = base.resolve_component_identity({"purl": "pkg:pypi/A@1.2.3"})
    assert (name2, version_url2, version_name2, origin_url2, origin_id2) == ("A", "", "1.2.3", "", "orig-1")
    assert base.calls == 1  # unchanged, no extra lookup


def test_resolve_component_identity_nv_cache_path() -> None:
    base = _TestBase()
    # No purl path; ensure NV cache key is set and values returned unchanged
    name, version_url, version_name, origin_url, origin_id = base.resolve_component_identity({"name": "B", "version": "2.0.0", "origin": "orig-2"})
    # Current implementation does not carry through the provided 'origin' in NV path; origin fields come out empty
    assert (name, version_url, version_name, origin_url, origin_id) == ("B", "", "2.0.0", "", "")

    # Call again; behavior should be identical
    name2, version_url2, version_name2, origin_url2, origin_id2 = base.resolve_component_identity({"name": "B", "version": "2.0.0", "origin": "orig-2"})
    assert (name2, version_url2, version_name2, origin_url2, origin_id2) == ("B", "", "2.0.0", "", "")
    # get_component_by_purl should never be called for NV path
    assert base.calls == 0
