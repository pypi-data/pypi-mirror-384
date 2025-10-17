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

    def _get_parameter_string(self, parameters: dict[str, Any]) -> str:
        from urllib.parse import urlencode

        return "?" + urlencode(parameters)


def test_dryrun_skips_put_and_prints_preview(capsys: Any) -> None:
    registry = EndpointRegistry()
    session = MockSession(registry)

    base_version_href = "http://bd/api/versions/1"

    # URL constructed by remediator for vulnerable BOM components (with encoded params)
    from urllib.parse import urlencode

    list_url = base_version_href + "/vulnerable-bom-components?" + urlencode({"q": "componentName:compA,vulnerabilityName:CVE-999"})
    item_href = "http://bd/api/vuln-bom/item-2"

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

    # Fetch item details returns current status/comment
    registry.register(
        "GET",
        item_href,
        lambda url, body, headers: MockResponse(
            200,
            {
                "remediationStatus": "OLD_STATUS",
                "comment": "old comment",
                "_meta": {"href": item_href},
            },
        ),
    )

    # Registering a PUT should not be necessary in dry-run; if mistakenly called, 500 helps detect
    registry.register(
        "PUT",
        item_href,
        lambda url, body, headers: MockResponse(500, {"error": "PUT should not be called in dry-run"}),
    )

    remediator = BlackDuckRemediator(hub=FakeHub(), session=session)
    # Avoid extra endpoints by stubbing versions
    remediator._call_project_versions = lambda project, version_name: {"items": [{"_meta": {"href": base_version_href}}]}  # type: ignore[assignment]

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
                "cve": "CVE-999",
                "resolution": "NEW",
                "comment": "reviewed",
            }
        ],
        changed_by="tester",
        dryrun=True,
    )

    # Should report success in dry-run mode
    assert ok is True

    # Inspect captured stdout for DRY-RUN message and current/new values
    out, err = capsys.readouterr()
    assert "DRY-RUN: Would update remediation" in out
    assert "OLD_STATUS" in out
    assert "reviewed" in out
