from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "bdsca_analysis_config_file", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_version_flag() -> None:
    cp = run_cli("--version")
    assert cp.returncode == 0
    assert "bdsca-analysis-config-file" in cp.stdout


def test_validate_example_yaml(tmp_path: Path) -> None:
    # Use a valid minimal config to avoid depending on the example file content.
    cfg = tmp_path / "cfg.yaml"
    data = {
        "specVersion": "1",
        "changeTarget": [{"project": {"name": "x", "version": "2"}}],
        "overrides": [
            {
                "component": {
                    "name": "example-component",
                    "codetype": "python",
                    "vendor": "ExampleVendor",
                    "version": "1.0.0",
                },
                "newVersion": "1.0.1",
            }
        ],
    }
    write_yaml(cfg, data)
    cp = run_cli("validate", str(cfg))
    assert cp.returncode == 0
    assert "Valid YAML (schema v1)" in cp.stdout


def test_validate_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.yaml"
    cp = run_cli("validate", str(missing))
    assert cp.returncode != 0
    assert "file not found" in cp.stderr.lower()


def test_schema_violation(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    # Missing required specVersion
    bad.write_text("overrides: []\n", encoding="utf-8")
    cp = run_cli("validate", str(bad))
    assert cp.returncode == 5
    assert "Schema validation failed" in cp.stderr


def valid_config_dict() -> dict:
    return {
        "specVersion": "1",
        "changeTarget": [{"project": {"name": "x", "version": "2"}}],
        "overrides": [
            {
                "component": {
                    "name": "x",
                    "codetype": "python",
                    "vendor": "v",
                    "version": "1",
                },
                "newVersion": "2",
            }
        ],
        # include a minimal triage to populate remediation metadata
        "vulnerabilityTriages": [
            {
                "component": {
                    "name": "x",
                    "codetype": "python",
                    "vendor": "v",
                    "version": "1",
                },
                "triages": [{"cve": "CVE-0000-0000", "resolution": "IGNORED", "comment": "n/a"}],
            }
        ],
    }


def write_yaml(p: Path, data: dict) -> None:
    import yaml  # local import for test

    p.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def test_output_summary(tmp_path: Path) -> None:
    cfg = tmp_path / "ok.yaml"
    write_yaml(cfg, valid_config_dict())
    cp = run_cli("validate", str(cfg), "--output", "summary")
    assert cp.returncode == 0
    assert "specVersion: 1" in cp.stdout
    assert "overrides: 1" in cp.stdout


def test_output_yaml(tmp_path: Path) -> None:
    cfg = tmp_path / "ok.yaml"
    data = valid_config_dict()
    write_yaml(cfg, data)
    cp = run_cli("validate", str(cfg), "--output", "yaml")
    assert cp.returncode == 0
    # YAML output should reflect keys
    assert "specVersion: '1'" in cp.stdout or 'specVersion: "1"' in cp.stdout


def test_output_json(tmp_path: Path) -> None:
    cfg = tmp_path / "ok.yaml"
    data = valid_config_dict()
    write_yaml(cfg, data)
    cp = run_cli("validate", str(cfg), "--output", "json")
    assert cp.returncode == 0
    assert '{\n  "specVersion": "1"' in cp.stdout


def test_change_target_requires_project(tmp_path: Path) -> None:
    cfg = tmp_path / "bad.yaml"
    data = valid_config_dict()
    data["changeTarget"] = {}
    write_yaml(cfg, data)
    cp = run_cli("validate", str(cfg))
    assert cp.returncode == 5
    assert "changeTarget" in cp.stderr


def test_change_target_project_requires_name_version(tmp_path: Path) -> None:
    cfg = tmp_path / "bad2.yaml"
    data = valid_config_dict()
    data["changeTarget"] = [{"project": {"name": "p"}}]
    write_yaml(cfg, data)
    cp = run_cli("validate", str(cfg))
    assert cp.returncode == 5
    # Expect error to reference the project object and a missing version
    assert "changeTarget[0].project" in cp.stderr or "changeTarget.project" in cp.stderr or "project" in cp.stderr
    assert "version is missing" in cp.stderr or "'version' is missing" in cp.stderr or "'version' is a required property" in cp.stderr or "Must include one of" in cp.stderr


def test_target_flag_outputs_effective_target(tmp_path: Path) -> None:
    cfg = tmp_path / "ok.yaml"
    data = valid_config_dict()
    write_yaml(cfg, data)
    cp = run_cli("validate", str(cfg), "--target")
    assert cp.returncode == 0
    assert "Target: Project 'x' version '2'" in cp.stdout


def test_summary_includes_target_when_requested(tmp_path: Path) -> None:
    cfg = tmp_path / "ok.yaml"
    data = valid_config_dict()
    write_yaml(cfg, data)
    cp = run_cli("validate", str(cfg), "--output", "summary", "--target")
    assert cp.returncode == 0
    assert "target:" in cp.stdout


def test_remediate_requires_credentials(tmp_path: Path) -> None:
    cfg = tmp_path / "ok.yaml"
    write_yaml(cfg, valid_config_dict())
    cp = run_cli("remediate", str(cfg))
    assert cp.returncode == 7
    assert "requires credentials" in cp.stderr.lower()
