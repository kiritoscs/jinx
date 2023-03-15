from dataclasses import dataclass

from common.config import config_util
from common.constants import (
    DEFAULT_TRANSLATION_FUNC_ALIAS,
    DJANGO_TRANSLATE_FUNC_IMPORT_PATH_PREFIX,
    DjangoTranslationFuncEnum,
)


@dataclass
class DjangoTranslateFuncConfig:
    """Django默认翻译函数配置"""

    default: str
    alias: str

    def __post_init__(self):
        DjangoTranslationFuncEnum.check_member(self.default)


django_translate_func_config = DjangoTranslateFuncConfig(
    default=config_util.get("marker.translation_func.default", DjangoTranslationFuncEnum.ugettext_lazy),
    alias=config_util.get("marker.translation_func.alias", DEFAULT_TRANSLATION_FUNC_ALIAS),
)


@dataclass
class DjangoTranslationFunc:
    """Django翻译函数"""

    import_path: str
    func_name: str = django_translate_func_config.default
    alias_name: str = django_translate_func_config.alias

    def __post_init__(self):
        """翻译函数导入路径"""
        if not self.import_path or self.import_path == DJANGO_TRANSLATE_FUNC_IMPORT_PATH_PREFIX:
            self.import_path = f"{DJANGO_TRANSLATE_FUNC_IMPORT_PATH_PREFIX}{self.func_name} as {self.alias_name}"

    @property
    def prefix(self):
        """翻译函数前缀"""
        return f"{self.alias_name}("

    @property
    def suffix(self):
        """翻译函数后缀"""
        return ")"


class DjangoTranslationFuncParser:
    """
    解析django翻译函数
    :param contents: 文件内容列表
    """

    def __init__(self, contents: list[str] = None):
        # contents 文件内容列表
        self._contents = contents or []
        # 根层级配置
        self._translate_funcs: list[DjangoTranslationFunc] = []

    def _parse_line(self, line: str):
        # 去除注释
        _origin_line = line
        line = line.split(DJANGO_TRANSLATE_FUNC_IMPORT_PATH_PREFIX)[1].strip().split("#")[0].strip()
        # alias函数名
        if "as" in line:
            func_name, alias_name = line.split("as")
            self._translate_funcs.append(
                DjangoTranslationFunc(import_path=_origin_line, func_name=func_name, alias_name=alias_name.strip())
            )
            return
        if "," in line:
            for _f in line.split(","):
                self._translate_funcs.append(DjangoTranslationFunc(import_path=_origin_line, alias_name=_f.strip()))
            return
        self._translate_funcs.append(DjangoTranslationFunc(import_path=_origin_line, alias_name=line))

    def parse(self):
        if not self._contents:
            return self._translate_funcs
        # 逐行解析
        for _c in self._contents:
            if not _c.startswith(DJANGO_TRANSLATE_FUNC_IMPORT_PATH_PREFIX):
                continue
            self._parse_line(_c)
        return self._translate_funcs

    @property
    def default(self):
        return DjangoTranslationFunc(
            import_path="",
            func_name=django_translate_func_config.default,
            alias_name=django_translate_func_config.alias,
        )
