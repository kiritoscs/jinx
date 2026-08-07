"""PoUtil write-mode tests."""

from __future__ import annotations

from pathlib import Path

import polib
import pytest

from jinx.common.constants import PoFileModeEnum
from jinx.common.po import PoUtil
from jinx.common.utils import strip_string_literal
from tests.conftest import write_po


def test_strip_string_literal() -> None:
    assert strip_string_literal('"hello"') == "hello"
    assert strip_string_literal("u'你好'") == "你好"
    assert strip_string_literal("hello") == "hello"


def test_update_only_fills_empty(tmp_path: Path) -> None:
    po_path = write_po(tmp_path / "django.po", [("a", ""), ("b", "keep")])
    util = PoUtil(str(po_path))
    util.write({"a": "A", "b": "B"}, mode=PoFileModeEnum.UPDATE.value)
    reloaded = polib.pofile(str(po_path))
    mapping = {e.msgid: e.msgstr for e in reloaded}
    assert mapping["a"] == "A"
    assert mapping["b"] == "keep"


def test_overwrite_replaces(tmp_path: Path) -> None:
    po_path = write_po(tmp_path / "django.po", [("a", "old")])
    util = PoUtil(str(po_path))
    util.write({"a": "new"}, mode=PoFileModeEnum.OVERWRITE.value)
    reloaded = polib.pofile(str(po_path))
    assert reloaded[0].msgstr == "new"


def test_append_adds_and_normalizes(tmp_path: Path) -> None:
    po_path = write_po(tmp_path / "django.po", [("existing", "")])
    util = PoUtil(str(po_path))
    util.write({'"new"': "", "existing": "x"}, mode=PoFileModeEnum.APPEND.value)
    reloaded = polib.pofile(str(po_path))
    mapping = {e.msgid: e.msgstr for e in reloaded}
    assert "new" in mapping
    assert mapping["existing"] == "x"


def test_po_properties(tmp_path: Path) -> None:
    po_path = write_po(tmp_path / "django.po", [("a", "A"), ("b", "")])
    util = PoUtil(str(po_path))
    assert "a" in util.msgid_list
    assert util.content_dict["a"] == "A"
    assert util.po is not None


def test_export_writes_json(tmp_path: Path) -> None:
    po_path = write_po(tmp_path / "django.po", [("a", "A")])
    out = tmp_path / "out.json"
    PoUtil(str(po_path)).export(str(out))
    assert '"a"' in out.read_text(encoding="utf-8")


def test_missing_po_panics(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        PoUtil(str(tmp_path / "missing.po"))


def test_backup_created_on_write(tmp_path: Path) -> None:
    po_path = write_po(tmp_path / "django.po", [("a", "")])
    PoUtil(str(po_path)).write({"a": "A"}, mode=PoFileModeEnum.UPDATE.value)
    backups = list(tmp_path.glob("django.po_bak_*"))
    assert backups
