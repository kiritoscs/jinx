"""Export PO entries to JSON for human review."""

from __future__ import annotations

from jinx.common.path import resolve_po_path
from jinx.common.po import PoUtil


class ExportTool:
    def __init__(self, locale_path: str | None = None, export_path: str = "contents.json") -> None:
        self.locale_path = locale_path or ""
        self.export_path = export_path
        self.po_file = PoUtil(resolve_po_path(self.locale_path))

    def handle(self) -> None:
        self.po_file.export(self.export_path)
