"""Path helper tests."""

from pathlib import Path

from jinx.common.path import resolve_po_path


def test_resolve_po_file_direct(tmp_path: Path) -> None:
    po = tmp_path / "django.po"
    po.write_text('msgid ""\nmsgstr ""\n', encoding="utf-8")
    assert resolve_po_path(str(po)) == str(po)


def test_resolve_locale_dir(tmp_path: Path) -> None:
    po = tmp_path / "en" / "LC_MESSAGES" / "django.po"
    po.parent.mkdir(parents=True)
    po.write_text('msgid ""\nmsgstr ""\n', encoding="utf-8")
    assert resolve_po_path(str(tmp_path), dest_lang="en") == str(po)
