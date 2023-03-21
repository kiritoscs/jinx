import os
import typing

from common import PoUtil, Prompt
from common.config import language
from common.constants import PoFileModeEnum
from marker import MarkerTool
from marker.utils.token import Token


class ExtractTool:
    """
    提取token到po文件里

    微服务架构, 一个项目可能包含多个服务, 每个服务都有自己的po文件

    且django-admin/python manage.py shell make_messages -l 这种形式依赖导入项目的环境变量, 会变得额外繁琐

    所以提供了这个工具, 用于提取token到po文件里
    """

    def __init__(self, target_path: str = None, locale_path: str = None):
        self.target_path = target_path
        self.locale_path = locale_path
        self.tokens: typing.List[Token] = MarkerTool(target_path).tokens
        self._init_po()

    def _init_po(self):
        """初始化po文件"""
        if self.locale_path.endswith(".po"):
            po_file = self.locale_path
        else:
            po_file = os.path.join(self.locale_path, language.dest, "LC_MESSAGES", "django.po")
        self.po_file = PoUtil(po_file)

    def handle(self):
        data = {token.token: "" for token in self.tokens}
        try:
            self.po_file.write(data=data, mode=PoFileModeEnum.APPEND)
            Prompt.info("Extract tokens to {po_file} successfully", po_file=self.po_file.po_file_path)
        except Exception as e:
            Prompt.error("Failed to extract tokens to {po_file}: {e}", po_file=self.po_file.po_file_path, e=e)
