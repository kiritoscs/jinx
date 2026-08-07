"""Extract marked strings into a PO file."""

from __future__ import annotations

from jinx.common import PoUtil, Prompt
from jinx.common.constants import PoFileModeEnum
from jinx.common.path import resolve_po_path
from jinx.marker import MarkerTool
from jinx.marker.utils.token import Token


class ExtractTool:
    """
    Extract i18n string candidates into a PO file.

    Useful for multi-service layouts where ``makemessages`` is awkward.
    """

    def __init__(self, target_path: str | None = None, locale_path: str | None = None) -> None:
        self.target_path = target_path or ""
        self.locale_path = locale_path or ""
        self.tokens: list[Token] = MarkerTool(target_path).tokens
        self.po_file = PoUtil(resolve_po_path(self.locale_path))

    def handle(self) -> None:
        data = {token.token: "" for token in self.tokens}
        try:
            self.po_file.write(data=data, mode=PoFileModeEnum.APPEND.value)
            Prompt.info("Extract tokens to {po_file} successfully", po_file=self.po_file.po_file_path)
        except Exception as e:  # noqa: BLE001
            Prompt.error(
                "Failed to extract tokens to {po_file}: {e}",
                po_file=self.po_file.po_file_path,
                e=e,
            )
