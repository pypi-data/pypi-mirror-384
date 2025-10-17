from __future__ import annotations

from typing import Any

from bdsca_analysis_config_file import BlackDuckRemediator
from bdsca_analysis_config_file.endpoint_mocks import (
    EndpointRegistry,
    MockResponse,
    MockSession,
)


class FakeHub:
    def __init__(self) -> None:
        self.config = {"insecure": False}

    def get_headers(self) -> dict[str, str]:
        return {}

    def get_projects(self, limit: int, parameters: dict[str, Any]) -> dict[str, Any]:
        return {"items": [{"_meta": {"href": "http://bd/api/projects/1"}}]}

    def _get_parameter_string(self, parameters: dict[str, Any]) -> str:  # pragma: no cover - not used here
        from urllib.parse import urlencode

        return "?" + urlencode(parameters)


def test_vulnerability_remediation_flow() -> None:
    registry = EndpointRegistry()
    session = MockSession(registry)

    base_version_href = "http://bd/api/versions/1"

    # URL constructed by remediator for vulnerable BOM components (with encoded params)
    from urllib.parse import urlencode

    list_url = base_version_href + "/vulnerable-bom-components?" + urlencode({"q": "componentName:compA,vulnerabilityName:CVE-123"})
    item_href = "http://bd/api/vuln-bom/item-1"

    registry.register(
        "GET",
        list_url,
        lambda url, body, headers: MockResponse(
            200,
            {
                "totalCount": 1,
                "items": [
                    {
                        "componentName": "compA",
                        "componentVersionName": "1.0.0",
                        "componentVersionOriginId": "origin-xyz",
                        "_meta": {"href": item_href},
                    }
                ],
            },
        ),
    )

    # Fetch item details
    registry.register(
        "GET",
        item_href,
        lambda url, body, headers: MockResponse(200, {"_meta": {"href": item_href}}),
    )

    # Update remediation status
    registry.register(
        "PUT",
        item_href,
        lambda url, body, headers: MockResponse(202, {"updated": True}),
    )

    remediator = BlackDuckRemediator(hub=FakeHub(), session=session)
    # Avoid extra endpoints by stubbing versions
    remediator._call_project_versions = lambda project, version_name: {"items": [{"_meta": {"href": base_version_href}}]}  # type: ignore[assignment]

    # Call the new remediation entry point
    ok = remediator.remediate_component_vulnerabilities(
        project_name="MyProj",
        project_version="1.0.0",
        component={
            "name": "compA",
            "version": "1.0.0",
            "origin": "origin-xyz",
        },
        triages=[
            {
                "cve": "CVE-123",
                "resolution": "Ignored",
                "comment": "reviewed",
            }
        ],
        changed_by="tester",
    )
    assert ok is True
