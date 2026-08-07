"""AST marker tests (format-preserving span edits)."""

from __future__ import annotations

from pathlib import Path

from jinx.common.config import init_config
from jinx.marker.marker import FileMarker, MarkerTool, get_marker_config


def test_marks_chinese_string(clean_config, tmp_path: Path) -> None:
    src = tmp_path / "sample.py"
    src.write_text('msg = "你好世界"\n', encoding="utf-8")

    FileMarker(str(src)).handle()
    content = src.read_text(encoding="utf-8")
    assert '_("你好世界")' in content or "_('你好世界')" in content
    assert "django.utils.translation" in content


def test_preserves_comments_and_spacing(clean_config, tmp_path: Path) -> None:
    src = tmp_path / "sample.py"
    src.write_text(
        "# header comment\n"
        "msg = \"你好\"  # trailing\n"
        "\n"
        "value = 1\n",
        encoding="utf-8",
    )
    FileMarker(str(src)).handle()
    content = src.read_text(encoding="utf-8")
    assert "# header comment" in content
    assert "# trailing" in content
    assert "value = 1" in content
    assert '_("你好")' in content or "_('你好')" in content


def test_skips_already_marked(clean_config, tmp_path: Path) -> None:
    src = tmp_path / "sample.py"
    src.write_text(
        'from django.utils.translation import gettext_lazy as _\n\nmsg = _("你好")\n',
        encoding="utf-8",
    )
    FileMarker(str(src)).handle()
    assert '_(_("你好"))' not in src.read_text(encoding="utf-8")
    assert src.read_text(encoding="utf-8").count("django.utils.translation") == 1


def test_skips_docstring(clean_config, tmp_path: Path) -> None:
    src = tmp_path / "sample.py"
    src.write_text('"""模块说明你好"""\n\nx = 1\n', encoding="utf-8")
    FileMarker(str(src)).handle()
    content = src.read_text(encoding="utf-8")
    assert "模块说明你好" in content
    assert "_(" not in content


def test_skips_function_docstring(clean_config, tmp_path: Path) -> None:
    src = tmp_path / "sample.py"
    src.write_text('def f():\n    """函数说明你好"""\n    return 1\n', encoding="utf-8")
    FileMarker(str(src)).handle()
    assert "_(" not in src.read_text(encoding="utf-8")


def test_fstring_converted_to_format(clean_config, tmp_path: Path) -> None:
    src = tmp_path / "sample.py"
    src.write_text('name = "a"\nmsg = f"你好{name}"\n', encoding="utf-8")
    handler = FileMarker(str(src))
    handler.handle()
    assert not handler.illegal_tokens
    content = src.read_text(encoding="utf-8")
    assert "format" in content
    assert "你好{}" in content or "你好" in content
    assert "f\"" not in content or "f'" not in content or "msg =" in content
    assert "f\"你好" not in content


def test_fstring_with_format_spec(clean_config, tmp_path: Path) -> None:
    src = tmp_path / "sample.py"
    src.write_text("n = 3\nmsg = f\"共{n:02d}件商品\"\n", encoding="utf-8")
    FileMarker(str(src)).handle()
    content = src.read_text(encoding="utf-8")
    assert "02d" in content
    assert ".format(n)" in content or ".format(" in content


def test_unsupported_fstring_left_unchanged(clean_config, tmp_path: Path) -> None:
    src = tmp_path / "sample.py"
    # dynamic format spec cannot be converted safely
    src.write_text('w = "02d"\nmsg = f"数量{1:{w}}"\n', encoding="utf-8")
    handler = FileMarker(str(src))
    handler.handle()
    assert handler.illegal_tokens
    assert "f\"数量" in src.read_text(encoding="utf-8") or "f'数量" in src.read_text(encoding="utf-8")


def test_strict_mode_skips_when_unsupported_fstring(clean_config, tmp_path: Path) -> None:
    cfg = tmp_path / "jinx.toml"
    cfg.write_text(
        "[marker]\nstrict_mode = true\nconvert_fstring = true\n",
        encoding="utf-8",
    )
    init_config(cfg)
    src = tmp_path / "sample.py"
    original = 'w = "x"\nx = "你好"\ny = f"数{1:{w}}"\n'
    src.write_text(original, encoding="utf-8")
    FileMarker(str(src)).handle()
    assert src.read_text(encoding="utf-8") == original


def test_only_extract_tokens_does_not_write(clean_config, tmp_path: Path) -> None:
    src = tmp_path / "sample.py"
    original = 'msg = "你好世界"\n'
    src.write_text(original, encoding="utf-8")
    handler = FileMarker(str(src))
    handler.handle(only_extract_tokens=True)
    assert handler.tokens
    assert src.read_text(encoding="utf-8") == original


def test_marker_tool_lists_files(clean_config, tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text('x = "你好"\n', encoding="utf-8")
    (tmp_path / "b.txt").write_text("nope", encoding="utf-8")
    tool = MarkerTool(str(tmp_path))
    files = tool.files
    assert any(f.endswith("a.py") for f in files)
    assert not any(f.endswith("b.txt") for f in files)


def test_marker_tool_tokens_property(clean_config, tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text('x = "你好啊"\n', encoding="utf-8")
    tool = MarkerTool(str(tmp_path))
    tokens = tool.tokens
    assert any(t.token == "你好啊" for t in tokens)


def test_marker_tool_handle_marks_all(clean_config, tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text('x = "标记一"\n', encoding="utf-8")
    (tmp_path / "b.py").write_text('y = "标记二"\n', encoding="utf-8")
    MarkerTool(str(tmp_path)).handle()
    assert "_(" in (tmp_path / "a.py").read_text(encoding="utf-8")
    assert "_(" in (tmp_path / "b.py").read_text(encoding="utf-8")


def test_syntax_error_file_does_not_crash(clean_config, tmp_path: Path) -> None:
    src = tmp_path / "bad.py"
    src.write_text("def (\n", encoding="utf-8")
    FileMarker(str(src)).handle()


def test_english_string_not_marked_under_zh(clean_config, tmp_path: Path) -> None:
    src = tmp_path / "sample.py"
    src.write_text('msg = "hello world"\n', encoding="utf-8")
    FileMarker(str(src)).handle()
    assert src.read_text(encoding="utf-8") == 'msg = "hello world"\n'


def test_get_marker_config_default(clean_config) -> None:
    assert get_marker_config().strict_mode is False
    assert get_marker_config().convert_fstring is True
