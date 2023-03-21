import os

from common import PoUtil, Prompt
from common.config import language


class CompileTool:
    """
    po编译成mo

    微服务架构, 一个项目可能包含多个服务, 每个服务都有自己的po文件

    且django-admin/python manage.py shell compilemessages 这种形式依赖导入项目的环境变量, 会变得额外繁琐

    所以提供了这个工具, 用于编译po->mo
    """

    def __init__(self, locale_path: str = None):
        self.locale_path = locale_path
        self._init_po()

    def _init_po(self):
        """初始化po文件"""
        if self.locale_path.endswith(".po"):
            po_file = self.locale_path
        else:
            po_file = os.path.join(self.locale_path, language.dest, "LC_MESSAGES", "django.po")
        self.po_file = PoUtil(po_file)

    def handle(self):
        """编译po文件"""
        mo_file_path = self.po_file.po_file_path.replace(".po", ".mo")
        try:
            self.po_file.po.save_as_mofile(mo_file_path)
            Prompt.info(
                "Successfully compiled {po_file} to {mo_file}", po_file=self.po_file.po_file_path, mo_file=mo_file_path
            )
        except Exception as e:
            Prompt.error(
                "Failed to compile {po_file} to {mo_file}, {e}",
                po_file=self.po_file.po_file_path,
                mo_file=mo_file_path,
                e=e,
            )
