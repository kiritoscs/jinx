import json

from dataclasses import dataclass

from utils import config
from utils.utils import read_file
from utils.translator import Translator, TranslatorProviderEnum


class TranslateTool:
    """
    翻译工具
    :param locate_path: locate目录(存放各个语言的po, mo文件)
    :param official_dict_path: 官方词典路径
    """
    def __init__(self, locate_path: str = None, official_dict_path: str = None):
        self._locate_path = locate_path
        if not official_dict_path:
            self._official_dict = {}
        else:
            try:
                self._official_dict = json.load(read_file(official_dict_path))
            except Exception as e:
                raise ValueError(f"官方词典文件{official_dict_path}格式错误: {e}")
        self._translate_class = Translator(provider=config.translator.provider).get_instance()
