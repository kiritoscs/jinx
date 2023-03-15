import json
import shutil

import arrow
import polib

from common.constants import PoFileModeEnum
from common.path import check_exist
from common.prompt import Prompt


class PoUtil:
    """PO文件工具"""

    def __init__(self, po_file_path: str):
        check_exist(po_file_path)
        self.po_file_path = po_file_path
        self._po: polib.POFile
        try:
            self._po = polib.pofile(po_file_path)
        except Exception as e:
            Prompt.panic("Failed to load {po_file_path}: {e}", po_file=po_file_path, e=e)
        # 初始化时读取po文件内现有所有msg
        self.po_content_list: list[polib.POEntry] = [entry for entry in self._po]
        self.po_content_dict: dict[str, str] = {entry.msgid: entry.msgstr for entry in self._po}

    @property
    def po(self) -> polib.POFile:
        return self._po

    def _backup(self):
        current = arrow.now().format("YYYY-MM-DDTHH-mm-ss")
        backup_file = f"{self.po_file_path}_bak_{current}"
        shutil.copyfile(self.po_file_path, backup_file)

    @property
    def msgid_list(self) -> list[str]:
        """获取po文件所有msgid, 即需要翻译的所有内容"""
        return [entry.msgid for entry in self._po]

    @property
    def content_dict(self) -> dict[str, str]:
        """获取po文件所有信息"""
        return self.po_content_dict

    def write(self, data: dict[str, str], mode=PoFileModeEnum.UPDATE):
        """写入po文件"""
        # 写入前先备份
        self._backup()
        if mode == PoFileModeEnum.OVERWRITE:
            # 如果是OVERWRITE, 更新所有msgid匹配的数据
            for entry in self._po:
                if entry.msgid not in data:
                    continue
                entry.msgstr = data[entry.msgid]
            self._po.save()
            return
        else:
            # 如果是UPDATE, 更新现有msgstr为空的数据
            for entry in self._po:
                if entry.msgid not in data or entry.msgstr:
                    continue
                entry.msgstr = data[entry.msgid]
                self._po.save()

    def export(self, export_path: str):
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(self.po_content_dict, f, ensure_ascii=False, indent=4)
            f.close()


__all__ = ["PoUtil"]
