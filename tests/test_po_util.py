"""PoUtil write-mode tests."""

from pathlib import Path

import polib

from jinx.common.constants import PoFileModeEnum
from jinx.common.po import PoUtil
from jinx.common.utils import strip_string_literal


def _write_po(path: Path, entries: list[tuple[str, str]]) -> None:
    po = polib.POFile()
    po.metadata = {"Content-Type": "text/plain; charset=UTF-8"}
    for msgid, msgstr in entries:
        po.append(polib.POEntry(msgid=msgid, msgstr=msgstr))
    po.save(str(path))


def test_strip_string_literal() -> None:
    assert strip_string_literal('"hello"') == "hello"
    assert strip_string_literal("u'你好'") == "你好"
    assert strip_string_literal("hello") == "hello"


def test_update_only_fills_empty(tmp_path: Path) -> None:
    po_path = tmp_path / "django.po"
    _write_po(po_path, [("a", ""), ("b", "keep")])
    util = PoUtil(str(po_path))
    util.write({"a": "A", "b": "B"}, mode=PoFileModeEnum.UPDATE.value)
    reloaded = polib.pofile(str(po_path))
    mapping = {e.msgid: e.msgstr for e in reloaded}
    assert mapping["a"] == "A"
    assert mapping["b"] == "keep"


def test_overwrite_replaces(tmp_path: Path) -> None:
    po_path = tmp_path / "django.po"
    _write_po(po_path, [("a", "old")])
    util = PoUtil(str(po_path))
    util.write({"a": "new"}, mode=PoFileModeEnum.OVERWRITE.value)
    reloaded = polib.pofile(str(po_path))
    assert reloaded[0].msgstr == "new"


def test_append_adds_and_normalizes(tmp_path: Path) -> None:
    po_path = tmp_path / "django.po"
    _write_po(po_path, [("existing", "")])
    util = PoUtil(str(po_path))
    util.write({'"new"': "", "existing": "x"}, mode=PoFileModeEnum.APPEND.value)
    reloaded = polib.pofile(str(po_path))
    mapping = {e.msgid: e.msgstr for e in reloaded}
    assert "new" in mapping
    assert mapping["existing"] == "x"
