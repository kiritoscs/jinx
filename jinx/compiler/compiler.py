"""Compile PO files to MO."""

from __future__ import annotations

from pathlib import Path

from jinx.common import PoUtil, Prompt
from jinx.common.path import resolve_po_path


class CompileTool:
    def __init__(self, locale_path: str | None = None) -> None:
        self.locale_path = locale_path or ""
        self.po_file = PoUtil(resolve_po_path(self.locale_path))

    def handle(self) -> None:
        mo_file_path = str(Path(self.po_file.po_file_path).with_suffix(".mo"))
        try:
            self.po_file.po.save_as_mofile(mo_file_path)
            Prompt.info(
                "Successfully compiled {po_file} to {mo_file}",
                po_file=self.po_file.po_file_path,
                mo_file=mo_file_path,
            )
        except Exception as e:  # noqa: BLE001
            Prompt.error(
                "Failed to compile {po_file} to {mo_file}, {e}",
                po_file=self.po_file.po_file_path,
                mo_file=mo_file_path,
                e=e,
            )
