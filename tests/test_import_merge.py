"""Import merge tests."""

from __future__ import annotations

from pathlib import Path

from jinx.marker.import_merge import ensure_translation_import
from jinx.marker.marker import FileMarker
from jinx.marker.utils.translation_func import DjangoTranslationFunc


def test_merge_into_existing_import() -> None:
    src = "from django.utils.translation import gettext\n\nx = 1\n"
    default = DjangoTranslationFunc.from_config()
    out = ensure_translation_import(src, default)
    assert out is not None
    assert "gettext" in out
    assert "gettext_lazy as _" in out or "as _" in out
    assert out.count("from django.utils.translation import") == 1


def test_no_change_when_alias_present() -> None:
    src = "from django.utils.translation import gettext_lazy as _\n\nx = 1\n"
    default = DjangoTranslationFunc.from_config()
    assert ensure_translation_import(src, default) is None


def test_file_marker_merges_import(clean_config, tmp_path: Path) -> None:
    src = tmp_path / "a.py"
    src.write_text(
        'from django.utils.translation import gettext\n\nmsg = "你好世界"\n',
        encoding="utf-8",
    )
    FileMarker(str(src)).handle()
    text = src.read_text(encoding="utf-8")
    assert text.count("from django.utils.translation import") == 1
    assert "as _" in text
    assert "_(" in text
