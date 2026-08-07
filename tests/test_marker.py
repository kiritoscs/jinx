"""AST marker tests."""

from pathlib import Path

from jinx.common.config import init_config
from jinx.marker.marker import FileMarker, MarkerTool


def test_marks_chinese_string(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_config(None)
    src = tmp_path / "sample.py"
    src.write_text('msg = "你好世界"\n', encoding="utf-8")

    FileMarker(str(src)).handle()
    content = src.read_text(encoding="utf-8")
    assert '_("你好世界")' in content or "_('你好世界')" in content
    assert "django.utils.translation" in content


def test_skips_already_marked(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_config(None)
    src = tmp_path / "sample.py"
    src.write_text(
        'from django.utils.translation import gettext_lazy as _\n\nmsg = _("你好")\n',
        encoding="utf-8",
    )
    before = src.read_text(encoding="utf-8")
    FileMarker(str(src)).handle()
    assert src.read_text(encoding="utf-8") == before or "__" not in src.read_text(encoding="utf-8")
    # should not double-wrap
    assert '_(_("你好"))' not in src.read_text(encoding="utf-8")


def test_skips_docstring(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_config(None)
    src = tmp_path / "sample.py"
    src.write_text('"""模块说明你好"""\n\nx = 1\n', encoding="utf-8")
    FileMarker(str(src)).handle()
    content = src.read_text(encoding="utf-8")
    assert '"""模块说明你好"""' in content
    assert "_(" not in content


def test_fstring_reported_not_wrapped(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_config(None)
    src = tmp_path / "sample.py"
    src.write_text('name = "a"\nmsg = f"你好{name}"\n', encoding="utf-8")
    handler = FileMarker(str(src))
    handler.handle()
    assert handler.illegal_tokens
    content = src.read_text(encoding="utf-8")
    # f-string itself should not become _()
    assert '_(f"' not in content


def test_marker_tool_lists_files(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_config(None)
    (tmp_path / "a.py").write_text('x = "你好"\n', encoding="utf-8")
    (tmp_path / "b.txt").write_text("nope", encoding="utf-8")
    tool = MarkerTool(str(tmp_path))
    files = tool.files
    assert any(f.endswith("a.py") for f in files)
    assert not any(f.endswith("b.txt") for f in files)
