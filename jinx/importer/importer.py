import os
import typing

from jinx.common import PoUtil, Prompt
from jinx.common.constants import PoFileModeEnum
from jinx.common.token import Token
from jinx.common.utils import read_file
from jinx.config import language


class Importer:
    def __init__(self, locale_path: str = None, final_entry_path: str = None):
        """
        翻译工具
        :param locale_path: Django locale目录, 也可以是po文件路径
        :param final_entry_path: 最终词条文件路径/目录
        """
        self.locale_path = locale_path
        self.final_entry_path = final_entry_path
        self.po_file: PoUtil
        self.entry_dict: typing.Dict[str, str] = {}
        self._init_po()
        self._init_entry()

    def _init_po(self):
        """初始化po文件"""
        if self.locale_path.endswith(".po"):
            po_file = self.locale_path
        else:
            po_file = os.path.join(self.locale_path, language.dest, "LC_MESSAGES", "django.po")
        self.po_file = PoUtil(po_file)

    def _init_entry(self):
        """初始化词条"""
        if not self.final_entry_path:
            self.entry_dict = {}
            return
        try:
            if os.path.isdir(self.final_entry_path):
                entry_file_list = []
                for file in os.listdir(self.final_entry_path):
                    if file.endswith(".json"):
                        entry_file_list.append(file)
                        self.entry_dict.update(read_file(fp=os.path.join(self.final_entry_path, file), is_json=True))
                Prompt.info("Entry files: {files}", files=",".join(entry_file_list))
            else:
                self.entry_dict = read_file(fp=self.final_entry_path, is_json=True)
                Prompt.info("Entry file: {file}", file=self.final_entry_path)
        except Exception as e:
            Prompt.panic(
                "Failed to Parse official dict: {final_entry_path}: {e}",
                official_dict_path=self.final_entry_path,
                e=e,
            )

    def handle(self):
        # 写入po文件
        tokens = Token.create_from_dict(self.entry_dict)
        self.po_file.write(mode=PoFileModeEnum.OVERWRITE, tokens=tokens)
