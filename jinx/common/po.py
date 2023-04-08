import copy
import os

import json5 as json
import polib

from jinx.common.constants import PoFileModeEnum
from jinx.common.path import check_exist
from jinx.common.prompt import Prompt
from jinx.common.token import Token
from jinx.common.utils import copy_file

"""
POFile对象
    encoding: str
    warpwidth: int
    check_for_duplicates: bool
    header: str
    metadata: dict[str, str]
    metadata_is_fuzzy: list
"""


class PoUtil:
    """PO文件工具"""

    def __init__(self, po_file_path: str):
        check_exist(po_file_path)
        self.po_file_path = po_file_path
        self.po: polib.POFile
        try:
            self.po = polib.pofile(po_file_path)
        except Exception as e:
            Prompt.panic("Failed to load {po_file_path}: {e}", po_file=po_file_path, e=e)

    def _get_write_method(self, mode: str):
        """获取写入方法"""
        PoFileModeEnum.check_member(mode)
        method_name = "{mode}_write".format(mode=mode.lower())
        return getattr(self, method_name)

    def read_dict(self, po: polib.POFile = None, with_obsolete: bool = False) -> dict[str, str]:
        """
        读取po文件, 返回msgid和msgstr的字典
        :param po: po对象, 默认为None, 则使用self.po
        :param with_obsolete: 是否包含已废弃的msgid
        """
        if not po:
            po = self.po
        if with_obsolete:
            return {entry.msgid: entry.msgstr for entry in po}
        else:
            return {entry.msgid: entry.msgstr for entry in po if not entry.obsolete}

    def read_list(self, po: polib.POFile = None, with_obsolete: bool = False) -> list[polib.POEntry]:
        """
        读取po文件, 返回POEntry的列表
        :param po: po对象, 默认为None, 则使用self.po
        :param with_obsolete: 是否包含已废弃的msgid, 默认为False, 则不包含
        """
        if not po:
            po = self.po
        if with_obsolete:
            return [entry for entry in po]
        else:
            return [entry for entry in po if not entry.obsolete]

    @staticmethod
    def copy_entry(entry: polib.POEntry) -> polib.POEntry:
        return copy.deepcopy(entry)

    def copy_po(
        self, new_po_file_path: str = None, with_entry: bool = False, with_obsolete: bool = False
    ) -> polib.POFile:
        """
        复制POFile, 但可以不包含entry
        :param with_obsolete: 是否包含已废弃的msgid
        :param new_po_file_path: 新po文件路径, 默认为None, 则使用原po文件路径
        :param with_entry: 是否包含entry
        :return polib.POFile
        """
        if new_po_file_path:
            pofile = new_po_file_path
        else:
            pofile = self.po_file_path
        po: polib.POFile = polib.POFile(
            wrapwidth=self.po.wrapwidth,
            encoding=self.po.encoding,
            check_for_duplicates=self.po.check_for_duplicates,
        )
        po.metadata = self.po.metadata
        po.metadata_is_fuzzy = self.po.metadata_is_fuzzy
        po.check_for_duplicates = self.po.check_for_duplicates
        po.header = self.po.header
        if with_entry:
            po.extend(self.read_list(with_obsolete=with_obsolete))
        po.save(pofile)
        return po

    def _backup(self):
        """
        备份po文件, 备份文件名为: {po_file_path}_bak_{current}
        """
        if bool(os.environ.get("TESTING", "False")):
            return
        copy_file(self.po_file_path)

    @property
    def msgid_list(self) -> list[str]:
        """获取po文件所有msgid, 即需要翻译的所有内容"""
        return [entry.msgid for entry in self.po]

    def append_write(self, tokens: list[Token], with_obsolete: bool = False, new_po_file_path: str = None):
        """
        追加写入po文件
        :param tokens: Token对象列表
        :param with_obsolete: 是否包含已废弃的msgid
        :param new_po_file_path: 新po文件路径, 默认为None, 则使用原po文件路径
        """
        po = self.copy_po(with_obsolete=with_obsolete, new_po_file_path=new_po_file_path, with_entry=True)
        no_obsolete_entry_msgid_list = [entry.msgid for entry in self.read_list(po=po, with_obsolete=False)]
        for token in tokens:
            if token.msgid not in no_obsolete_entry_msgid_list:
                po.append(token.to_po_entry())
        po.save()

    def overwrite_write(self, tokens: list[Token], with_obsolete: bool = False, new_po_file_path: str = None):
        """
        覆盖写入po文件
        按照原文件entry顺序先遍历覆盖, 再追加
        :param tokens: Token对象列表
        :param with_obsolete: 是否包含已废弃的msgid
        :param new_po_file_path: 新po文件路径, 默认为None, 则使用原po文件路径
        """
        token_info = {token.msgid: token for token in tokens}
        entry_list = self.read_list(with_obsolete=with_obsolete)
        po = self.copy_po(with_obsolete=with_obsolete, new_po_file_path=new_po_file_path, with_entry=False)
        for entry in entry_list:
            if entry.msgid not in token_info:
                po.append(entry)
                continue
            new_entry = self.copy_entry(entry)
            new_entry.msgstr = token_info[entry.msgid].msgstr
            po.append(new_entry)
        po.save()

    def update_write(self, tokens: list[Token], with_obsolete: bool = False, new_po_file_path: str = None):
        """
        更新写入po文件
        :param tokens: Token对象列表
        :param with_obsolete: 是否包含已废弃的msgid
        :param new_po_file_path: 新po文件路径, 默认为None, 则使用原po文件路径
        """
        token_info = {token.msgid: token for token in tokens}
        po = self.copy_po(with_obsolete=with_obsolete, new_po_file_path=new_po_file_path, with_entry=True)
        for entry in po:
            if entry.msgstr:
                continue
            if entry.msgid in token_info:
                entry.msgstr = token_info[entry.msgid].msgstr
        po.save()

    def write(self, mode: str, tokens: list[Token], with_obsolete: bool = False, new_po_file_path: str = None):
        """写入po文件"""
        # 写入前先备份
        self._backup()
        self._get_write_method(mode)(tokens=tokens, with_obsolete=with_obsolete, new_po_file_path=new_po_file_path)

    def export(self, export_path: str):
        try:
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(self.read_dict(), f, ensure_ascii=False, indent=4)
                f.close()
            Prompt.info("Exported to {export_path}", export_path=export_path)
        except Exception as e:
            Prompt.panic("Failed to export: {e}", e=e)


__all__ = ["PoUtil"]
