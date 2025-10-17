from bdsca_analysis_config_file import cli


def test_build_parser() -> None:
    parser = cli._build_parser()
    assert parser is not None
    assert parser.prog == "bdsca-config"


def test_load_and_validate_config_valid(tmp_path: cli.Path) -> None:
    cfg = tmp_path / "ok.yaml"
    cfg.write_text("specVersion: '1'\nchangeTarget:\n  - project:\n      name: foo\n      version: bar\n", encoding="utf-8")
    data, errors = cli._load_and_validate_config(cfg)
    assert isinstance(data, dict)
    assert errors == []


def test_load_and_validate_config_missing_file(tmp_path: cli.Path) -> None:
    missing = tmp_path / "missing.yaml"
    data, errors = cli._load_and_validate_config(missing)
    assert data == {}
    assert errors and "Error reading file" in errors[0]


def test_cmd_validate_valid(tmp_path: cli.Path) -> None:
    cfg = tmp_path / "ok.yaml"
    cfg.write_text("specVersion: '1'\nchangeTarget:\n  - project:\n      name: foo\n      version: bar\n", encoding="utf-8")
    rc = cli.cmd_validate(cfg)
    assert rc == 0


def test_cmd_validate_invalid(tmp_path: cli.Path) -> None:
    cfg = tmp_path / "bad.yaml"
    cfg.write_text("changeTarget: []\n", encoding="utf-8")
    rc = cli.cmd_validate(cfg)
    assert rc == 5
