import os
import sys
import arrow
import shutil

import polib

from utils.constants import OpenFileModeEnum


class PoUtil:
    def __init__(self, _po_file: str, mode: str = OpenFileModeEnum.READ):
        if not os.path.exists(_po_file):
            print(f"po文件{_po_file}不存在")
            sys.exit(1)
        self._po: polib.POFile
        self._mode = mode
        # 非仅读模式, 先备份再读取
        if mode != OpenFileModeEnum.READ:
            self._backup(_po_file)
        try:
            self._po = polib.pofile(_po_file)
        except Exception as e:
            print(f"读取po文件{_po_file}失败: {e}")
            sys.exit(1)
        # 初始化时读取po文件内现有所有msg
        self._msg: dict[str, str] = self._read()

    @staticmethod
    def _backup(_po_file: str):
        current = arrow.now().format("YYYY-MM-DDTHH-mm-ss")
        backup_file = f"{_po_file}_bak_{current}"
        shutil.copyfile(_po_file, backup_file)

    def _read(self) -> dict[str, str]:
        """获取po文件所有信息"""
        return {
            entry.msgid: entry.msgstr
            for entry in self._po
        }

    @property
    def read(self) -> dict[str, str]:
        """获取po文件所有信息"""
        return self._msg

    def write(self, data: dict[str, str]):
        """写入po文件"""
        if self._mode == OpenFileModeEnum.READ:
            print("当前po文件打开模式为仅读，不可写入")
            return
        # 如果是覆盖模式，直接覆盖
        if self._mode == OpenFileModeEnum.OVERWRITE:
            self._po = polib.POFile()
            for msgid, msgstr in data.items():
                entry = polib.POEntry(msgid=msgid, msgstr=msgstr)
                self._po.append(entry)
            self._po.save()
            return
        # 如果是追加模式，先读取po文件内现有所有msg，然后将新数据追加到po文件
        for entry in self._po:
            if entry.msgid in data:
                entry.msgstr = data[entry.msgid]
        for msgid, msgstr in data.items():
            if msgid not in self._msg:
                entry = polib.POEntry(msgid=msgid, msgstr=msgstr)
                self._po.append(entry)
                self._msg[msgid] = msgstr
        self._po.save()
