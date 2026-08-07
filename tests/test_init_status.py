"""init / status / plural-snippet CLI tests."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from jinx.cli import cli
from jinx.marker.plural_hints import collect_plural_hints, ngettext_snippet
from tests.conftest import write_po


def test_init_writes_config(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    out = tmp_path / "jinx.toml"
    result = runner.invoke(cli, ["--no-validate", "init", "-o", str(out)])
    assert result.exit_code == 0, result.output
    assert out.is_file()
    assert "marker" in out.read_text(encoding="utf-8")


def test_init_refuses_overwrite(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "jinx.toml"
    out.write_text("x=1\n", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(cli, ["--no-validate", "init", "-o", str(out)])
    assert result.exit_code != 0


def test_status_pending_exit_one(clean_config, tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text('msg = "需要处理的文案"\n', encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(cli, ["--no-validate", "status", "-t", str(tmp_path)])
    assert result.exit_code == 1


def test_status_with_po(clean_config, tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    po = write_po(tmp_path / "django.po", [("hello", ""), ("world", "World")])
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--no-validate", "status", "-t", str(tmp_path), "-l", str(po)],
    )
    # untranslated entry → exit 1
    assert result.exit_code == 1
    assert "PO" in result.output or "untranslated" in result.output.lower() or "Status" in result.output


def test_plural_hints_detect_count_fstring(tmp_path: Path) -> None:
    src = tmp_path / "a.py"
    src.write_text('n = 3\nmsg = f"共{n}个商品"\n', encoding="utf-8")
    hints = collect_plural_hints(str(tmp_path))
    assert hints
    assert any("商品" in h.snippet or "n" in h.snippet for h in hints)


def test_ngettext_snippet() -> None:
    s = ngettext_snippet("{count} item", "{count} items", "count")
    assert "ngettext_lazy" in s
    assert "{count} item" in s


def test_plural_snippet_cli() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--no-validate", "plural-snippet", "-s", "{c} item", "-p", "{c} items", "--count", "c"],
    )
    assert result.exit_code == 0
    assert "ngettext_lazy" in result.output


def test_version_option() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.3.0" in result.output
