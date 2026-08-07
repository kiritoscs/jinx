"""TranslatorTool integration tests."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import polib
import pytest

from jinx.common.config import init_config
from jinx.common.constants import TranslatorModeEnum
from jinx.translator.translator import TranslatorTool
from tests.conftest import write_po


@pytest.fixture(autouse=True)
def _cfg(clean_config):
    return clean_config


def test_full_match_syncs_from_official_dict(tmp_path: Path) -> None:
    po_path = write_po(
        tmp_path / "django.po",
        [("你好", ""), ("世界", "old"), ("其他", "")],
    )
    dict_path = tmp_path / "dict.json"
    dict_path.write_text(json.dumps({"你好": "Hello", "世界": "World"}, ensure_ascii=False), encoding="utf-8")

    tool = TranslatorTool(
        locale_path=str(po_path),
        official_dict_path=str(dict_path),
        mode=TranslatorModeEnum.FULL_MATCH.value,
    )
    assert tool._client is None
    tool.handle()

    reloaded = polib.pofile(str(po_path))
    mapping = {e.msgid: e.msgstr for e in reloaded}
    assert mapping["你好"] == "Hello"
    assert mapping["世界"] == "World"
    assert mapping["其他"] == ""


def test_update_mode_only_empty_entries(tmp_path: Path) -> None:
    po_path = write_po(tmp_path / "django.po", [("你好", ""), ("世界", "World")])

    mock_client = MagicMock()
    mock_client.result = {"你好": "Hello", "世界": "IGNORED"}

    with patch("jinx.translator.translator.Provider.get_instance", return_value=mock_client) as factory:
        tool = TranslatorTool(locale_path=str(po_path), mode=TranslatorModeEnum.UPDATE.value)
        # factory called with only empty msgstr entries
        contents = factory.call_args.kwargs["contents"]
        assert contents == ["你好"]
        tool.handle()

    mock_client.translate.assert_called_once()
    reloaded = polib.pofile(str(po_path))
    mapping = {e.msgid: e.msgstr for e in reloaded}
    assert mapping["你好"] == "Hello"
    assert mapping["世界"] == "World"


def test_overwrite_mode_sends_all_msgids(tmp_path: Path) -> None:
    po_path = write_po(tmp_path / "django.po", [("a", ""), ("b", "B")])
    mock_client = MagicMock()
    mock_client.result = {"a": "A", "b": "BB"}

    with patch("jinx.translator.translator.Provider.get_instance", return_value=mock_client) as factory:
        tool = TranslatorTool(locale_path=str(po_path), mode=TranslatorModeEnum.OVERWRITE.value)
        assert set(factory.call_args.kwargs["contents"]) == {"a", "b"}
        tool.handle()

    reloaded = polib.pofile(str(po_path))
    mapping = {e.msgid: e.msgstr for e in reloaded}
    assert mapping["a"] == "A"
    assert mapping["b"] == "BB"


def test_invalid_official_dict_panics(tmp_path: Path) -> None:
    po_path = write_po(tmp_path / "django.po", [("a", "")])
    bad = tmp_path / "bad.json"
    bad.write_text("{not-json", encoding="utf-8")
    with pytest.raises(SystemExit):
        TranslatorTool(
            locale_path=str(po_path),
            official_dict_path=str(bad),
            mode=TranslatorModeEnum.FULL_MATCH.value,
        )


def test_resolve_locale_directory(tmp_path: Path) -> None:
    po_path = write_po(
        tmp_path / "en" / "LC_MESSAGES" / "django.po",
        [("你好", "")],
    )
    locale_root = tmp_path
    init_config(None)
    with patch("jinx.translator.translator.Provider.get_instance") as factory:
        mock_client = MagicMock()
        mock_client.result = {"你好": "Hi"}
        factory.return_value = mock_client
        tool = TranslatorTool(locale_path=str(locale_root), mode=TranslatorModeEnum.UPDATE.value)
        assert tool.po_file.po_file_path == str(po_path)
        tool.handle()
    assert polib.pofile(str(po_path))[0].msgstr == "Hi"
