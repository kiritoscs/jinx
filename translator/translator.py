import os
import typing
from dataclasses import dataclass

from common import Prompt
from common.config import config_util, language
from common.constants import TranslatorModeEnum, TranslatorProviderEnum
from common.po import PoUtil
from common.utils import read_file
from translator.provider import Provider


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
            self.official_dict = read_file(fp=self.official_dict_path, is_json=True)
        except Exception as e:
            Prompt.panic("官方词典文件{official_dict_path}格式错误: {e}", official_dict_path=self.official_dict_path, e=e)

    def _init_client(self):
        if self.mode == TranslatorModeEnum.UPDATE:
            contents = [entry.msgid for entry in self.po_file.po if entry.msgstr == ""]
        else:
            contents = self.po_file.msgid_list
        self._client = Provider.get_instance(
            source_lang=language.current,
            dest_lang=language.dest,
            official_dict=self.official_dict,
            provider=translator_config.provider,
            contents=contents,
        )

    def handle(self):
        # 翻译
        self._client.translate()
        # 写入po文件
        self.po_file.write(data=self._client.result, mode=self.mode)
