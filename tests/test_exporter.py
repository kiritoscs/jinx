"""ExportTool tests."""

from __future__ import annotations

import json
from pathlib import Path

from jinx.exporter.exporter import ExportTool
from tests.conftest import write_po


def test_export_json(clean_config, tmp_path: Path) -> None:
    po_path = write_po(tmp_path / "django.po", [("你好", "Hello"), ("世界", "")])
    out = tmp_path / "out.json"
    ExportTool(locale_path=str(po_path), export_path=str(out)).handle()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["你好"] == "Hello"
    assert data["世界"] == ""


def test_export_from_locale_dir(clean_config, tmp_path: Path) -> None:
    write_po(tmp_path / "en" / "LC_MESSAGES" / "django.po", [("a", "A")])
    out = tmp_path / "contents.json"
    ExportTool(locale_path=str(tmp_path), export_path=str(out)).handle()
    assert json.loads(out.read_text(encoding="utf-8"))["a"] == "A"
