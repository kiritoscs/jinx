"""CLI smoke and integration tests."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import polib
from click.testing import CliRunner

from jinx.cli import cli, main
from tests.conftest import write_po


def test_cli_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "marker" in result.output
    assert "translator" in result.output
    assert "extractor" in result.output
    assert "exporter" in result.output
    assert "compiler" in result.output


def test_cli_subcommand_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["marker", "--help"])
    assert result.exit_code == 0
    assert "target-path" in result.output or "target_path" in result.output


def test_cli_marker_command(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "app.py"
    src.write_text('msg = "你好世界"\n', encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(cli, ["marker", "-t", str(tmp_path)])
    assert result.exit_code == 0, result.output
    text = src.read_text(encoding="utf-8")
    assert "_(" in text
    assert "django.utils.translation" in text


def test_cli_exporter_command(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    po = write_po(tmp_path / "django.po", [("你好", "Hello")])
    out = tmp_path / "e.json"
    runner = CliRunner()
    result = runner.invoke(cli, ["exporter", "-l", str(po), "-e", str(out)])
    assert result.exit_code == 0, result.output
    assert json.loads(out.read_text(encoding="utf-8"))["你好"] == "Hello"


def test_cli_compiler_command(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    po = write_po(tmp_path / "django.po", [("a", "b")])
    runner = CliRunner()
    result = runner.invoke(cli, ["compiler", "-l", str(po)])
    assert result.exit_code == 0, result.output
    assert po.with_suffix(".mo").is_file()


def test_cli_extractor_command(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "m.py").write_text('x = "抽取测试"\n', encoding="utf-8")
    po = write_po(tmp_path / "django.po", [])
    runner = CliRunner()
    result = runner.invoke(cli, ["extractor", "-t", str(tmp_path), "-l", str(po)])
    assert result.exit_code == 0, result.output
    assert any(e.msgid == "抽取测试" for e in polib.pofile(str(po)))


def test_cli_translator_full_match(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    po = write_po(tmp_path / "django.po", [("你好", "")])
    d = tmp_path / "dict.json"
    d.write_text(json.dumps({"你好": "Hello"}, ensure_ascii=False), encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["translator", "-p", str(po), "-o", str(d), "-m", "full_match"],
    )
    assert result.exit_code == 0, result.output
    assert polib.pofile(str(po))[0].msgstr == "Hello"


def test_cli_translator_update_mocked(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    po = write_po(tmp_path / "django.po", [("你好", "")])
    mock_client = type("C", (), {"result": {"你好": "Hi"}, "translate": lambda self: None})()
    with patch("jinx.translator.translator.Provider.get_instance", return_value=mock_client):
        runner = CliRunner()
        result = runner.invoke(cli, ["translator", "-p", str(po), "-m", "update"])
    assert result.exit_code == 0, result.output
    assert polib.pofile(str(po))[0].msgstr == "Hi"


def test_main_invokes_cli() -> None:
    with patch("jinx.cli.cli") as mock_cli:
        main()
        mock_cli.assert_called_once()
