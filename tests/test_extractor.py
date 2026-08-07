"""ExtractTool tests."""

from __future__ import annotations

from pathlib import Path

import polib

from jinx.extractor.extractor import ExtractTool
from tests.conftest import write_po


def test_extract_appends_chinese_strings(clean_config, tmp_path: Path) -> None:
    src_dir = tmp_path / "app"
    src_dir.mkdir()
    (src_dir / "views.py").write_text('title = "欢迎使用"\nother = "hello"\n', encoding="utf-8")
    po_path = write_po(tmp_path / "django.po", [("已有", "")])

    ExtractTool(target_path=str(src_dir), locale_path=str(po_path)).handle()

    reloaded = polib.pofile(str(po_path))
    msgids = {e.msgid for e in reloaded}
    assert "欢迎使用" in msgids
    assert "已有" in msgids
    # English-only string should not be extracted under zh-CN language regex
    assert "hello" not in msgids


def test_extract_to_locale_dir(clean_config, tmp_path: Path) -> None:
    src_dir = tmp_path / "pkg"
    src_dir.mkdir()
    (src_dir / "a.py").write_text('msg = "测试词条"\n', encoding="utf-8")
    po_path = write_po(tmp_path / "en" / "LC_MESSAGES" / "django.po", [])

    ExtractTool(target_path=str(src_dir), locale_path=str(tmp_path)).handle()
    reloaded = polib.pofile(str(po_path))
    assert any(e.msgid == "测试词条" for e in reloaded)


def test_extract_after_mark_collects_wrapped_strings(clean_config, tmp_path: Path) -> None:
    """Regression: extractor must find msgids already wrapped by marker."""
    src_dir = tmp_path / "app"
    src_dir.mkdir()
    src = src_dir / "views.py"
    src.write_text('title = "欢迎光临"\n', encoding="utf-8")
    po_path = write_po(tmp_path / "django.po", [])

    from jinx.marker.marker import FileMarker
    FileMarker(str(src)).handle()
    assert "_(" in src.read_text(encoding="utf-8")

    ExtractTool(target_path=str(src_dir), locale_path=str(po_path)).handle()
    reloaded = polib.pofile(str(po_path))
    assert any(e.msgid == "欢迎光临" for e in reloaded)
