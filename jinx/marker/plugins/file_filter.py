"""File path filters for the marker."""

from __future__ import annotations

from dataclasses import dataclass, field

from jinx.common.config import config_util


@dataclass
class FileFilterConfig:
    exclude_paths: list[str] = field(default_factory=list)
    exclude_files: list[str] = field(default_factory=list)


def get_file_filter() -> FileFilterConfig:
    return FileFilterConfig(
        exclude_paths=config_util.get("marker.filter.exclude_paths", []) or [],
        exclude_files=config_util.get("marker.filter.exclude_files", []) or [],
    )


# lazy-friendly default used by MarkerTool
file_filter = get_file_filter
