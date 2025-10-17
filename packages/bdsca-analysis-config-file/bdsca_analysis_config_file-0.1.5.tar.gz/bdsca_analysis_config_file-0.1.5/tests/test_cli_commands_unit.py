from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from bdsca_analysis_config_file import cli


def write_yaml(p: Path, data: dict[str, Any]) -> None:
    import yaml  # local import for tests

    p.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def minimal_target() -> dict[str, Any]:
    return {"changeTarget": [{"project": {"name": "p", "version": "1"}}]}


def config_with_component_additions() -> dict[str, Any]:
    return {
        "specVersion": "1",
        **minimal_target(),
        "componentAdditions": [
            {"component": {"purl": "pkg:pypi/sample@1.0.0"}},
        ],
    }


def config_with_overrides() -> dict[str, Any]:
    return {
        "specVersion": "1",
        **minimal_target(),
        "overrides": [
            {
                "component": {
                    "name": "compA",
                    "vendor": "VendorX",
                    "codetype": "python",
                    "version": "1.0.0",
                },
                "newVersion": "2.0.0",
            }
        ],
    }


def config_with_vulnerability_triages() -> dict[str, Any]:
    return {
        "specVersion": "1",
        **minimal_target(),
        "vulnerabilityTriages": [
            {
                "component": {
                    "name": "compA",
                    "vendor": "VendorX",
                    "codetype": "python",
                    "version": "1.0.0",
                },
                "triages": [{"cve": "CVE-123", "resolution": "IGNORED", "comment": "ok"}],
            }
        ],
    }


def test_cmd_add_components_requires_credentials(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    cfg = tmp_path / "cfg.yaml"
    write_yaml(cfg, config_with_component_additions())

    rc = cli.cmd_add_components(cfg, None, None, insecure=False, verbosity="info")
    assert rc == 7
    err = capsys.readouterr().err.lower()
    assert "requires credentials" in err


def test_cmd_add_components_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    class FakeRemediator:
        last_error: str | None = None

        def __init__(self, *a: Any, **kw: Any) -> None:  # accept ctor args
            pass

        def add_missing_components_from_config(self, project: str, version: str, component_additions: list[dict[str, Any]], *, dryrun: bool = False) -> list[dict[str, Any]]:  # noqa: D401
            # Pretend everything is added
            return [{"component": (component_additions[0]["component"]), "added": True, "result": {"status": 201}}]

    monkeypatch.setattr(cli, "BlackDuckRemediator", FakeRemediator)

    cfg = tmp_path / "cfg.yaml"
    write_yaml(cfg, config_with_component_additions())

    rc = cli.cmd_add_components(cfg, base_url="http://x", api_token="t", insecure=True, verbosity="debug")
    assert rc == 0
    out = capsys.readouterr().out
    assert "Added component to BOM" in out
    assert "All components added successfully" in out


def test_cmd_overwrite_dryrun_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    class FakeRemediator:
        last_error: str | None = None

        def __init__(self, *a: Any, **kw: Any) -> None:
            pass

        def overwrite_component_version(self, project: str, version: str, component: dict[str, Any], new_version: str | None, changed_by: str, dryrun: bool) -> bool:
            # Return success to simulate overwrite handled
            return True

    monkeypatch.setattr(cli, "BlackDuckRemediator", FakeRemediator)

    cfg = tmp_path / "cfg.yaml"
    write_yaml(cfg, config_with_overrides())

    rc = cli.cmd_overwrite(cfg, base_url="http://x", api_token="t", insecure=False, verbosity="info", dryrun=True)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Dry-run completed" in out


def test_cmd_remediate_dryrun_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    class FakeRemediator:
        last_error: str | None = None

        def __init__(self, *a: Any, **kw: Any) -> None:
            pass

        def remediate_component_vulnerabilities(self, project: str, version: str, component: dict[str, Any], triages: list[dict[str, Any]], changed_by: str, dryrun: bool) -> bool:
            return True

    monkeypatch.setattr(cli, "BlackDuckRemediator", FakeRemediator)

    cfg = tmp_path / "cfg.yaml"
    write_yaml(cfg, config_with_vulnerability_triages())

    rc = cli.cmd_remediate(cfg, base_url="http://x", api_token="t", insecure=False, verbosity="info", dryrun=True)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Dry-run completed" in out


def test_cmd_overwrite_requires_credentials(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    cfg = tmp_path / "cfg.yaml"
    write_yaml(cfg, config_with_overrides())

    rc = cli.cmd_overwrite(cfg, base_url=None, api_token=None, insecure=False, verbosity="info", dryrun=False)
    assert rc == 7
    err = capsys.readouterr().err.lower()
    assert "requires credentials" in err


def test_cmd_add_components_schema_violation_returns_5(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Missing required specVersion and empty/invalid changeTarget should trigger schema failure
    cfg = tmp_path / "bad_add.yaml"
    write_yaml(cfg, {"changeTarget": []})

    rc = cli.cmd_add_components(cfg, base_url="http://x", api_token="t", insecure=False, verbosity="info")
    assert rc == 5
    err = capsys.readouterr().err
    assert "Schema validation failed" in err


def test_cmd_remediate_schema_violation_returns_5(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    cfg = tmp_path / "bad_remediate.yaml"
    write_yaml(cfg, {"changeTarget": []})

    rc = cli.cmd_remediate(cfg, base_url="http://x", api_token="t", insecure=False, verbosity="info", dryrun=False)
    assert rc == 5
    err = capsys.readouterr().err
    assert "Schema validation failed" in err


def test_cmd_overwrite_schema_violation_returns_5(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    cfg = tmp_path / "bad_overwrite.yaml"
    write_yaml(cfg, {"changeTarget": []})

    rc = cli.cmd_overwrite(cfg, base_url="http://x", api_token="t", insecure=False, verbosity="info", dryrun=False)
    assert rc == 5
    err = capsys.readouterr().err
    assert "Schema validation failed" in err
