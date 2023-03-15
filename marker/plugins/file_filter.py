from dataclasses import dataclass

from common.config import config_util


@dataclass
class FileFilterConfig:
    """文件过滤配置"""

    exclude_paths: list[str]
    exclude_files: list[str]


file_filter = FileFilterConfig(
    exclude_paths=config_util.get("marker.filter.exclude_paths", []),
    exclude_files=config_util.get("marker.filter.exclude_files", []),
)
