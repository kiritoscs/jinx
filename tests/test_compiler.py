"""CompileTool tests."""

from __future__ import annotations

from pathlib import Path

import polib

from jinx.compiler.compiler import CompileTool
from tests.conftest import write_po


def test_compile_po_to_mo(clean_config, tmp_path: Path) -> None:
    po_path = write_po(tmp_path / "django.po", [("你好", "Hello")])
    CompileTool(locale_path=str(po_path)).handle()
    mo_path = tmp_path / "django.mo"
    assert mo_path.is_file()
    mo = polib.mofile(str(mo_path))
    assert mo[0].msgid == "你好"
    assert mo[0].msgstr == "Hello"


def test_compile_locale_dir(clean_config, tmp_path: Path) -> None:
    po_path = write_po(tmp_path / "en" / "LC_MESSAGES" / "django.po", [("x", "y")])
    CompileTool(locale_path=str(tmp_path)).handle()
    assert po_path.with_suffix(".mo").is_file()
