"""Heuristics to skip false-positive i18n candidates."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field

from jinx.common.config import config_util

# Common assignment targets that hold identifiers / names, not UI copy
_DEFAULT_SKIP_ASSIGN_NAMES = [
    "name",
    "username",
    "user_name",
    "first_name",
    "last_name",
    "full_name",
    "id",
    "pk",
    "slug",
    "code",
    "key",
    "token",
    "uuid",
    "email",
    "phone",
    "mobile",
    "path",
    "url",
    "uri",
    "filename",
    "file_name",
    "prefix",
    "suffix",
    "app_label",
    "related_name",
    "db_table",
    "db_column",
]

_DEFAULT_SKIP_EXACT = [
    "utf-8",
    "utf8",
    "ascii",
    "zh-cn",
    "zh-hans",
    "en-us",
    "content-type",
    "application/json",
]


@dataclass
class SkipConfig:
    min_length: int = 2
    max_length: int = 500
    skip_assign_names: list[str] = field(default_factory=lambda: list(_DEFAULT_SKIP_ASSIGN_NAMES))
    skip_exact: list[str] = field(default_factory=lambda: list(_DEFAULT_SKIP_EXACT))
    skip_if_only_cjk_name_like: bool = True
    # pure 2–4 CJK chars often personal/product names when assigned to name-like targets
    name_like_max_len: int = 4


def get_skip_config() -> SkipConfig:
    raw_names = config_util.get("marker.skip.skip_assign_names")
    raw_exact = config_util.get("marker.skip.skip_exact")
    return SkipConfig(
        min_length=int(config_util.get("marker.skip.min_length", 2) or 2),
        max_length=int(config_util.get("marker.skip.max_length", 500) or 500),
        skip_assign_names=list(raw_names) if raw_names is not None else list(_DEFAULT_SKIP_ASSIGN_NAMES),
        skip_exact=list(raw_exact) if raw_exact is not None else list(_DEFAULT_SKIP_EXACT),
        skip_if_only_cjk_name_like=bool(config_util.get("marker.skip.skip_if_only_cjk_name_like", True)),
        name_like_max_len=int(config_util.get("marker.skip.name_like_max_len", 4) or 4),
    )


_CJK_ONLY = re.compile(r"^[\u4e00-\u9fff·•]+$")


def should_skip_string(
    text: str,
    *,
    source_line: str = "",
    assign_target: str | None = None,
    cfg: SkipConfig | None = None,
) -> bool:
    """Return True if ``text`` should not be wrapped for i18n."""
    cfg = cfg or get_skip_config()
    s = text.strip()
    if not s:
        return True
    if len(s) < cfg.min_length:
        return True
    if len(s) > cfg.max_length:
        return True
    if s.lower() in {x.lower() for x in cfg.skip_exact}:
        return True
    # logging / debug patterns already partly handled by not_contains on source_line
    if assign_target and assign_target in cfg.skip_assign_names:
        # skip short CJK "names" and any string bound to identity-like names when short
        if cfg.skip_if_only_cjk_name_like and _CJK_ONLY.match(s) and len(s) <= cfg.name_like_max_len:
            return True
        if assign_target in {"id", "pk", "slug", "code", "key", "token", "uuid", "db_table", "db_column", "related_name", "app_label"}:
            return True
    # very short single CJK glyph alone is rarely UI copy
    if len(s) == 1 and _CJK_ONLY.match(s):
        return True
    return False


def assignment_target_for_constant(stack: list[ast.AST], node: ast.Constant) -> str | None:
    """If ``node`` is the value of a simple assignment ``name = "..."``, return name."""
    if not stack:
        return None
    # ... Assign targets = Constant
    # walk up: Constant <- ... <- Assign
    for i in range(len(stack) - 1, -1, -1):
        parent = stack[i]
        if isinstance(parent, ast.Assign):
            if len(parent.targets) == 1 and isinstance(parent.targets[0], ast.Name):
                # value may be Constant directly or nested
                if parent.value is node or _contains_node(parent.value, node):
                    return parent.targets[0].id
            return None
        if isinstance(parent, ast.AnnAssign):
            if isinstance(parent.target, ast.Name) and parent.value is not None:
                if parent.value is node or _contains_node(parent.value, node):
                    return parent.target.id
            return None
    return None


def _contains_node(tree: ast.AST, target: ast.AST) -> bool:
    for child in ast.walk(tree):
        if child is target:
            return True
    return False
