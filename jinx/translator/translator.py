import os
import typing
from dataclasses import dataclass

from jinx.common import PoUtil, Prompt
from jinx.common.config import config_util
from jinx.common.constants import TranslatorModeEnum, TranslatorProviderEnum
from jinx.common.token import Token
from jinx.common.utils import read_file
from jinx.config import language
from jinx.translator.provider import Provider


@dataclass
class TranslatorConfig:
    """翻译配置"""

    provider: str = TranslatorProviderEnum.GoogleAPI

    def __post_init__(self):
        TranslatorProviderEnum.check_member(self.provider)


translator_config = TranslatorConfig(
    provider=config_util.get("translator.provider", TranslatorProviderEnum.GoogleAPI),
)


class TranslatorTool:
    def __init__(self, locale_path: str = None, official_dict_path: str = None, mode: str = TranslatorModeEnum.UPDATE):
        """
        翻译工具
        :param locale_path: Django locale目录, 也可以是po文件路径
        :param official_dict_path: 官方词典路径
        """
        self.locale_path = locale_path
        self.official_dict_path = official_dict_path
        self.mode = mode
        self.po_file: PoUtil
        self.official_dict: typing.Dict[str, str] = {}
        self._init_po()
        self._init_official_dict()
        self._client = None
        self._init_client()

    def _init_po(self):
        """初始化po文件"""
        if self.locale_path.endswith(".po"):
            po_file = self.locale_path
        else:
            po_file = os.path.join(self.locale_path, language.dest, "LC_MESSAGES", "django.po")
        self.po_file = PoUtil(po_file)

    def _init_official_dict(self):
        """初始化官方词典"""
        if not self.official_dict_path:
            self.official_dict = {}
            return
        try:
            if os.path.isdir(self.official_dict_path):
                _official_dict_file_list = []
                for file in os.listdir(self.official_dict_path):
                    if file.endswith(".json"):
                        _official_dict_file_list.append(file)
                        self.official_dict.update(
                            read_file(fp=os.path.join(self.official_dict_path, file), is_json=True)
                        )
                Prompt.info("Official dict files: {files}", files=",".join(_official_dict_file_list))
            else:
                self.official_dict = read_file(fp=self.official_dict_path, is_json=True)
                Prompt.info("Official dict file: {file}", file=self.official_dict_path)
        except Exception as e:
            Prompt.panic(
                "Failed to Parse official dict: {official_dict_path}: {e}",
                official_dict_path=self.official_dict_path,
                e=e,
            )

    def _init_client(self):
        if self.mode == TranslatorModeEnum.UPDATE:
            tokens = [Token.create_from_po_entry(entry) for entry in self.po_file.read_list() if not entry.msgstr]
        else:
            tokens = [Token.create_from_po_entry(entry) for entry in self.po_file.read_list()]
        self._client = Provider.get_instance(
            source_lang=language.current,
            dest_lang=language.dest,
            official_dict=self.official_dict,
            provider=translator_config.provider,
            tokens=tokens,
        )

    def handle(self):
        # 翻译
        self._client.batch_translate()
        # # 写入po文件
        self.po_file.write(mode=self.mode, tokens=self._client.result)
