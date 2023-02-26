from dataclasses import dataclass

from utils.config import Config
from utils.utils import list_files
from utils.constants import (
    DJANGO_TRANSLATE_FUNC_IMPORT_PATH_PREFIX,
    DEFAULT_TRANSLATE_FUNC,
    DEFAULT_TRANSLATE_FUNC_ALIAS,
    LanguageEnum,
    LanguageRegexEnum,
)


@dataclass
class LanguageConfig:
    current: str = LanguageEnum.CHINESE
    target: str = LanguageEnum.ENGLISH
    re: str = LanguageRegexEnum[LanguageEnum.CHINESE]

    def __post_init__(self):
        if self.current not in LanguageEnum.__dict__.values():
            raise ValueError(f"当前语言不支持: {self.current}")
        if self.target not in LanguageEnum.__dict__.values():
            raise ValueError(f"目标语言不支持: {self.target}")


@dataclass
class DjangoTranslateFunc:
    import_path: str = None,
    func_name: str = DEFAULT_TRANSLATE_FUNC,
    alias_name: str = DEFAULT_TRANSLATE_FUNC_ALIAS

    def __post_init__(self):
        if not self.import_path:
            self.import_path = f"{DJANGO_TRANSLATE_FUNC_IMPORT_PATH_PREFIX}{self.func_name} as {self.alias_name}"

    @property
    def prefix(self):
        """翻译函数前缀"""
        return f"{self.alias_name}("

    @property
    def suffix(self):
        """翻译函数后缀"""
        return ")"


@dataclass
class GlobalConfig:
    """全局配置"""
    # 语言配置
    language: LanguageConfig = None
    # 排除的路径列表
    exclude_paths: list[str] = None
    # 排除的文件列表
    exclude_files: list[str] = None


class ToolBase:
    """工具基类"""
    # def __init__(self, target_path: str = None, config_path: str = None):
    def __init__(self, config_path: str = None):
        # self._target_path = target_path
        self._config = Config(config_path)
        self._global_config = None
        self._init_global_config()

    def _init_global_config(self):
        """初始化全局配置"""
        self._global_config = GlobalConfig(
            language=LanguageConfig(
                current=self._config.get(module="language", key="current", default=LanguageEnum.CHINESE),
                target=self._config.get(module="language", key="target", default=LanguageEnum.ENGLISH),
                re=self._config.get(module="language", key="re", default=LanguageRegexEnum[LanguageEnum.CHINESE]),
            ),
            exclude_paths=self._config.get(key="exclude_paths", default=[]),
            exclude_files=self._config.get(key="exclude_files", default=[]),
        )

    # @property
    # def files(self):
    #     """列出符合过滤条件的所有文件"""
    #     return list_files(
    #         target_path=self._target_path,
    #         exclude_paths=self._global_config.exclude_paths,
    #         exclude_files=self._global_config.exclude_files
    #     )
