"""High-level translation tool over PO files."""

from __future__ import annotations

from jinx.common import Prompt
from jinx.common.config import config_util, language
from jinx.common.constants import TranslatorModeEnum, TranslatorProviderEnum
from jinx.common.path import resolve_po_path
from jinx.common.po import PoUtil
from jinx.common.utils import read_file
from jinx.translator.provider import Provider


class TranslatorTool:
    def __init__(
        self,
        locale_path: str | None = None,
        official_dict_path: str | None = None,
        mode: str = TranslatorModeEnum.UPDATE.value,
    ) -> None:
        self.locale_path = locale_path or ""
        self.official_dict_path = official_dict_path
        self.mode = mode
        self.official_dict: dict[str, str] = {}
        self.po_file = PoUtil(resolve_po_path(self.locale_path))
        self._client = None
        self._init_official_dict()
        self._init_client()

    def _init_official_dict(self) -> None:
        if not self.official_dict_path:
            self.official_dict = {}
            return
        try:
            self.official_dict = read_file(fp=self.official_dict_path, is_json=True)
        except Exception as e:  # noqa: BLE001
            Prompt.panic(
                "Official dict {official_dict_path} is invalid: {e}",
                official_dict_path=self.official_dict_path,
                e=e,
            )

    def _init_client(self) -> None:
        if self.mode == TranslatorModeEnum.FULL_MATCH.value:
            return
        if self.mode == TranslatorModeEnum.UPDATE.value:
            contents = [entry.msgid for entry in self.po_file.po if entry.msgstr == ""]
        else:
            contents = self.po_file.msgid_list
        provider = config_util.get("translator.provider", TranslatorProviderEnum.GoogleAPI.value)
        self._client = Provider.get_instance(
            source_lang=language.current,
            dest_lang=language.dest,
            official_dict=self.official_dict,
            provider=provider,
            contents=contents,
        )

    def handle(self) -> None:
        if self.mode == TranslatorModeEnum.FULL_MATCH.value:
            self._full_match()
            return
        assert self._client is not None
        self._client.translate()
        self.po_file.write(data=self._client.result, mode=self.mode)

    def _full_match(self) -> None:
        Prompt.info("Syncing entries from official dict")
        for entry in self.po_file.po:
            if entry.msgid not in self.official_dict:
                continue
            entry.msgstr = self.official_dict[entry.msgid]
        self.po_file.po.save(self.po_file.po_file_path)
        Prompt.info("Finished syncing entries")
