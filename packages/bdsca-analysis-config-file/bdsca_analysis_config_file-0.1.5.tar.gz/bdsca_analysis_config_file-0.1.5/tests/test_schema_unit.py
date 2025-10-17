from bdsca_analysis_config_file.schema import validate_config


def test_validate_config_valid() -> None:
    config = {
        "specVersion": "1",
        "changeTarget": [{"project": {"name": "foo", "version": "bar"}}],
        "componentAdditions": [
            {"component": {"purl": "pkg:pypi/sample@1.0.0"}},
        ],
    }
    errors = validate_config(config)
    assert errors == []


def test_validate_config_missing_spec() -> None:
    config = {
        "changeTarget": [{"project": {"name": "foo", "version": "bar"}}],
        "componentAdditions": [
            {"component": {"purl": "pkg:pypi/sample@1.0.0"}},
        ],
    }
    errors = validate_config(config)
    assert any("specVersion" in e for e in errors)


def test_validate_config_missing_project() -> None:
    config = {
        "specVersion": "1",
        "changeTarget": [{}],
        "componentAdditions": [
            {"component": {"purl": "pkg:pypi/sample@1.0.0"}},
        ],
    }
    errors = validate_config(config)
    assert any("project" in e for e in errors)


def test_validate_config_component_additions_only_purl() -> None:
    config = {
        "specVersion": "1",
        "changeTarget": [{"project": {"name": "foo", "version": "bar"}}],
        "componentAdditions": [
            {"component": {"purl": "pkg:pypi/sample@1.0.0"}},
        ],
    }
    errors = validate_config(config)
    assert errors == []
