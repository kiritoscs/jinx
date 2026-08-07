"""False-positive skip heuristics."""

from __future__ import annotations

import ast
from pathlib import Path

from jinx.marker.marker import FileMarker
from jinx.marker.skip import assignment_target_for_constant, should_skip_string


def test_skip_short_and_exact() -> None:
    assert should_skip_string("中")  # single char
    assert should_skip_string("utf-8")
    assert not should_skip_string("欢迎使用本系统")


def test_skip_name_assignment(clean_config, tmp_path: Path) -> None:
    src = tmp_path / "a.py"
    src.write_text('name = "张三"\nmsg = "请登录后继续"\n', encoding="utf-8")
    FileMarker(str(src)).handle()
    text = src.read_text(encoding="utf-8")
    # name-like short CJK skipped
    assert 'name = "张三"' in text or "name = '张三'" in text
    assert "_(" in text  # msg marked
    assert "请登录后继续" in text


def test_assignment_target_detection() -> None:
    tree = ast.parse('name = "张三"\n')
    assign = tree.body[0]
    assert isinstance(assign, ast.Assign)
    const = assign.value
    assert isinstance(const, ast.Constant)
    # stack simulation: Module, Assign
    stack = [tree, assign]
    assert assignment_target_for_constant(stack, const) == "name"


def test_dry_run_does_not_write(clean_config, tmp_path: Path) -> None:
    src = tmp_path / "a.py"
    original = 'msg = "你好世界"\n'
    src.write_text(original, encoding="utf-8")
    fr = FileMarker(str(src)).handle(dry_run=True)
    assert fr.would_change
    assert fr.preview is not None
    assert "_(" in fr.preview
    assert src.read_text(encoding="utf-8") == original


def test_check_mode_exit(clean_config, tmp_path: Path) -> None:
    from click.testing import CliRunner

    from jinx.cli import cli

    (tmp_path / "a.py").write_text('msg = "需要标记的文案"\n', encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(cli, ["--no-validate", "marker", "-t", str(tmp_path), "--check"])
    assert result.exit_code == 1
    # still unmarked
    assert "_(" not in (tmp_path / "a.py").read_text(encoding="utf-8")


def test_check_passes_when_clean(clean_config, tmp_path: Path) -> None:
    from click.testing import CliRunner
    from jinx.cli import cli
    src = tmp_path / "a.py"
    src.write_text(
        'from django.utils.translation import gettext_lazy as _\nmsg = _("已经标记")\n',
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["--no-validate", "marker", "-t", str(tmp_path), "--check"])
    assert result.exit_code == 0, result.output
