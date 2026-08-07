"""PO file utilities."""

from __future__ import annotations

import json
import shutil
from typing import Any

import arrow
import polib

from jinx.common.constants import PoFileModeEnum
from jinx.common.path import check_exist
from jinx.common.prompt import Prompt
from jinx.common.utils import strip_string_literal


class PoUtil:
    """Read / write gettext PO files with backup."""

    def __init__(self, po_file_path: str) -> None:
        check_exist(po_file_path)
        self.po_file_path = po_file_path
        try:
            self._po = polib.pofile(po_file_path)
        except Exception as e:  # noqa: BLE001 — surface as panic
            Prompt.panic("Failed to load {po_file_path}: {e}", po_file_path=po_file_path, e=e)
        self.po_content_list: list[polib.POEntry] = list(self._po)
        self.po_content_dict: dict[str, str] = {entry.msgid: entry.msgstr for entry in self._po}

    @property
    def po(self) -> polib.POFile:
        return self._po

    def _backup(self) -> None:
        current = arrow.now().format("YYYY-MM-DDTHH-mm-ss")
        backup_file = f"{self.po_file_path}_bak_{current}"
        shutil.copyfile(self.po_file_path, backup_file)

    @property
    def msgid_list(self) -> list[str]:
        return [entry.msgid for entry in self._po]

    @property
    def content_dict(self) -> dict[str, str]:
        return self.po_content_dict

    @staticmethod
    def _normalize_msgid_map(data: dict[str, str]) -> dict[str, str]:
        normalized: dict[str, str] = {}
        for key, value in data.items():
            normalized[strip_string_literal(key)] = value
        return normalized

    def write(self, data: dict[str, str], mode: str = PoFileModeEnum.UPDATE.value) -> None:
        """Write translation entries into the PO file."""
        self._backup()
        if mode == PoFileModeEnum.OVERWRITE.value:
            for entry in self._po:
                if entry.msgid in data:
                    entry.msgstr = data[entry.msgid]
            self._po.save()
            return

        if mode == PoFileModeEnum.APPEND.value:
            data = self._normalize_msgid_map(data)
            existing = set(self.msgid_list)
            for entry in self._po:
                if entry.msgid in data and data[entry.msgid]:
                    entry.msgstr = data[entry.msgid]
            for msgid, msgstr in data.items():
                if msgid not in existing:
                    self._po.append(polib.POEntry(msgid=msgid, msgstr=msgstr))
            self._po.save()
            return

        # UPDATE: only fill empty msgstr
        for entry in self._po:
            if entry.msgid in data and not entry.msgstr:
                entry.msgstr = data[entry.msgid]
        self._po.save()

    def export(self, export_path: str) -> None:
        try:
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(self.po_content_dict, f, ensure_ascii=False, indent=4)
            Prompt.info("Exported to {export_path}", export_path=export_path)
        except Exception as e:  # noqa: BLE001
            Prompt.panic("Failed to export: {e}", e=e)


__all__ = ["PoUtil"]
