from collections import namedtuple

from utils.config import Config


DjangoTranslateFunc = namedtuple("DjangoTranslateFunc", ["import_path", "alias_name"])

IMPORT_PATH = "from django.utils.translation import "


class ParseDjangoTranslateFunc(object):
    """解析django翻译函数"""
    def __init__(self, config: Config, contents: list = None):
        # contents 文件内容列表
        self._contents = contents or []
        # 根层级配置
        self._config = config
        self._translate_funcs = []

    def _parse_line(self, line: str):
        # 去除注释
        _origin_line = line
        line = line.split(IMPORT_PATH)[1].strip().split("#")[0].strip()
        # alias函数名
        if "as" in line:
            func_name, alias_name = line.split("as")
            self._translate_funcs.append(DjangoTranslateFunc(import_path=_origin_line, alias_name=alias_name.strip()))
            return
        if "," in line:
            for _f in line.split(","):
                self._translate_funcs.append(
                    DjangoTranslateFunc(import_path=_origin_line, alias_name=_f.strip())
                )
            return
        self._translate_funcs.append(DjangoTranslateFunc(import_path=_origin_line, alias_name=line))

    def parse(self):
        if not self._contents:
            return self._translate_funcs
        # 逐行解析
        for _c in self._contents:
            if not _c.startswith(IMPORT_PATH):
                continue
            self._parse_line(_c)
        return self._translate_funcs

    def use_default(self):
        # 当parse解析为空时候, 使用默认配置
        _translate_func = self._config.get("translate_func", "default", "ugettext_lazy")
        _alias_name = self._config.get("translate_func", "alias", "_")
        _import_path = f"{IMPORT_PATH}{_translate_func} as {_alias_name}"
        return DjangoTranslateFunc(import_path=_import_path, alias_name=_alias_name)
