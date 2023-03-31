import shutil

import arrow
import json5 as json
import polib

from jinx.common.constants import PoFileModeEnum
from jinx.common.path import check_exist
from jinx.common.prompt import Prompt
from jinx.common.token import Token

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
        # 初始化时读取po文件内现有所有msg
        self.po_content_list: list[polib.POEntry] = [entry for entry in self.po if not entry.obsolete]
        self.po_content_dict: dict[str, str] = {entry.msgid: entry.msgstr for entry in self.po if not entry.obsolete}

    def _get_write_method(self, mode: str):
        """获取写入方法"""
        method_name = "{mode}_write".format(mode=mode.lower())
        return getattr(self, method_name)

    def read_dict(self, po: polib.POEntry = None, with_obsolete: bool = False) -> dict[str, str]:
        """
        读取po文件, 返回msgid和msgstr的字典
        :param with_obsolete: 是否包含已废弃的msgid
        """
        if not po:
            po = self.po
        if with_obsolete:
            return {entry.msgid: entry.msgstr for entry in po}
        else:
            return {entry.msgid: entry.msgstr for entry in po if not entry.obsolete}

    def read_list(self, po: polib.POEntry = None, with_obsolete: bool = False) -> list[polib.POEntry]:
        """
        读取po文件, 返回POEntry的列表
        :param with_obsolete: 是否包含已废弃的msgid
        """
        if not po:
            po = self.po
        if with_obsolete:
            return [entry for entry in po]
        else:
            return [entry for entry in po if not entry.obsolete]

    def copy_po_without_entry(self, with_obsolete: bool = False, new_po_file_path: str = None) -> polib.POFile:
        """
        复制po文件, 但不包含entry
        :param with_obsolete: 是否包含已废弃的msgid
        :param new_po_file_path: 新po文件路径, 默认为None, 则使用原po文件路径
        """
        if new_po_file_path:
            pofile = new_po_file_path
        else:
            pofile = self.po_file_path
        po = polib.POFile(
            wrapwidth=self.po.wrapwidth,
            encoding=self.po.encoding,
            check_for_duplicates=self.po.check_for_duplicates,
        )
        po.metadata = self.po.metadata
        po.metadata_is_fuzzy = self.po.metadata_is_fuzzy
        po.check_for_duplicates = self.po.check_for_duplicates
        po.header = self.po.header
        po.extend(self.read_list(with_obsolete=with_obsolete))
        po.save(pofile)
        return po

    def _backup(self):
        """
        备份po文件, 备份文件名为: {po_file_path}_bak_{current}
        """
        current = arrow.now().format("YYYY-MM-DDTHH-mm-ss")
        backup_file = f"{self.po_file_path}_bak_{current}"
        shutil.copyfile(self.po_file_path, backup_file)

    @property
    def msgid_list(self) -> list[str]:
        """获取po文件所有msgid, 即需要翻译的所有内容"""
        return [entry.msgid for entry in self.po]

    def append_write(self, tokens: list[Token], with_obsolete: bool = False, new_po_file_path: str = None):
        """追加写入po文件"""
        po = self.copy_po_without_entry(with_obsolete=with_obsolete, new_po_file_path=new_po_file_path)
        no_obsolete_entry_msgid_list = [entry.msgid for entry in self.read_list(po=po, with_obsolete=False)]
        for token in tokens:
            if token.msgid not in no_obsolete_entry_msgid_list:
                po.append(token.to_poentry())
        po.save()

    def overwrite_write(self, tokens: list[Token], with_obsolete: bool = False, new_po_file_path: str = None):
        """覆盖写入po文件"""
        po = self.copy_po_without_entry(with_obsolete=with_obsolete, new_po_file_path=new_po_file_path)
        for token in tokens:
            po.append(token.to_poentry())
        po.save()

    def update_write(self, tokens: list[Token], with_obsolete: bool = False, new_po_file_path: str = None):
        """更新写入po文件"""
        po = self.copy_po_without_entry(with_obsolete=with_obsolete, new_po_file_path=new_po_file_path)
        token_entry_dict = {token.msgid: token.to_poentry() for token in tokens}
        for entry in po:
            # 如果msgid在token_entry_dict中, 并且msgstr为空, 则更新msgstr
            if entry.msgid in token_entry_dict and not entry.msgstr:
                entry.msgstr = token_entry_dict[entry.msgid].msgstr
                continue
        no_obsolete_entry_msgid_list = [entry.msgid for entry in self.read_list(po=po, with_obsolete=False)]
        for token in tokens:
            if token.msgid not in no_obsolete_entry_msgid_list:
                po.append(token.to_poentry())
        po.save()

    def write(self, data: dict[str, str], mode=PoFileModeEnum.UPDATE):
        """写入po文件"""
        # 写入前先备份
        self._backup()
        if mode == PoFileModeEnum.OVERWRITE:
            # 如果是OVERWRITE, 更新所有msgid匹配的数据
            for entry in self.po:
                if entry.msgid not in data:
                    continue
                entry.msgstr = data[entry.msgid]
            self.po.save()
            return
        elif mode == PoFileModeEnum.APPEND:
            # APPEND模式用在提取项目国际化词条, 写入po, 以便翻译
            # 如果是APPEND, 更新所有msgid匹配的数据, 并新增msgid不存在的数据
            new_data = {}
            for key, value in data.items():
                if key.startswith("u"):
                    key = key.lstrip("u")
                if key.startswith('"'):
                    key = key.lstrip('"')
                if key.endswith('"'):
                    key = key.rstrip('"')
                new_data[key] = value
            data = new_data
            for entry in self.po:
                if entry.msgid not in data or not data[entry.msgid]:
                    continue
                entry.msgstr = data[entry.msgid]
            for msgid, msgstr in data.items():
                if msgid not in self.msgid_list:
                    self.po.append(polib.POEntry(msgid=msgid, msgstr=msgstr))
            self.po.save()
            return
        else:
            # 如果是UPDATE, 更新现有msgstr为空的数据
            for entry in self.po:
                if entry.msgid not in data or entry.msgstr:
                    continue
                entry.msgstr = data[entry.msgid]
                self.po.save()

    def export(self, export_path: str):
        try:
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(self.po_content_dict, f, ensure_ascii=False, indent=4)
                f.close()
            Prompt.info("Exported to {export_path}", export_path=export_path)
        except Exception as e:
            Prompt.panic("Failed to export: {e}", e=e)


__all__ = ["PoUtil"]
