import os

from common.config import language
from common.po import PoUtil


class ExportTool:
    """
    提取工具
    :param locale_path: Django locale目录, 也可以是po文件路径
    :param export_path: 导出路径
    """

    def __init__(self, locale_path: str = None, export_path: str = "contents.json"):
        """ """
        self.locale_path = locale_path
        self._init_po()
        self.export_path = export_path

    def _init_po(self):
        """初始化po文件"""
        if self.locale_path.endswith(".po"):
            po_file = self.locale_path
        else:
            po_file = os.path.join(self.locale_path, language.dest, "LC_MESSAGES", "django.po")
        self.po_file = PoUtil(po_file)

    def handle(self):
        self.po_file.export(self.export_path)
