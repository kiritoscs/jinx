"""String matching conditions for i18n candidates."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from jinx.common.config import config_util, language


@dataclass
class StrConditionConfig:
    contains: list[str] = field(default_factory=list)
    not_contains: list[str] = field(default_factory=list)
    startswith: list[str] = field(default_factory=list)
    not_startswith: list[str] = field(default_factory=list)
    endswith: list[str] = field(default_factory=list)
    not_endswith: list[str] = field(default_factory=list)


@dataclass
class StrConditions:
    source_line: StrConditionConfig = field(default_factory=StrConditionConfig)
    token: StrConditionConfig = field(default_factory=StrConditionConfig)


def _cfg(section: str) -> StrConditionConfig:
    raw = config_util.get(section, {}) or {}
    return StrConditionConfig(
        contains=list(raw.get("contains") or []),
        not_contains=list(raw.get("not_contains") or []),
        startswith=list(raw.get("startswith") or []),
        not_startswith=list(raw.get("not_startswith") or []),
        endswith=list(raw.get("endswith") or []),
        not_endswith=list(raw.get("not_endswith") or []),
    )


def get_str_conditions() -> StrConditions:
    return StrConditions(
        source_line=_cfg("marker.str_conditions.source_line"),
        token=_cfg("marker.str_conditions.token"),
    )


class StrCondition:
    """Match a string value + source line against configured filters and language regex."""

    def __init__(
        self,
        token_text: str,
        source_line: str = "",
        conditions: StrConditions | None = None,
        language_re: str | None = None,
    ) -> None:
        self.token_text = token_text
        self.source_line = source_line
        self.conditions = conditions or get_str_conditions()
        self.language_re = language_re if language_re is not None else language.re

    def match(self) -> bool:
        return self._match_part("source_line") and self._match_part("token") and self._match_language()

    def _part_content(self, part: str) -> str:
        return self.source_line if part == "source_line" else self.token_text

    def _match_language(self) -> bool:
        return re.search(self.language_re, self.token_text) is not None

    def _match_part(self, part: str) -> bool:
        for key in asdict(getattr(self.conditions, part)):
            method = getattr(self, f"_build_{key}")
            if not method(part):
                return False
        return True

    def _build_contains(self, part: str) -> bool:
        content = self._part_content(part)
        conditions: StrConditionConfig = getattr(self.conditions, part)
        if not conditions.contains:
            return True
        return any(c in content for c in conditions.contains)

    def _build_not_contains(self, part: str) -> bool:
        content = self._part_content(part)
        conditions: StrConditionConfig = getattr(self.conditions, part)
        if not conditions.not_contains:
            return True
        return not any(c in content for c in conditions.not_contains)

    def _build_startswith(self, part: str) -> bool:
        content = self._part_content(part)
        conditions: StrConditionConfig = getattr(self.conditions, part)
        if not conditions.startswith:
            return True
        return any(content.startswith(c) for c in conditions.startswith)

    def _build_not_startswith(self, part: str) -> bool:
        content = self._part_content(part)
        conditions: StrConditionConfig = getattr(self.conditions, part)
        if not conditions.not_startswith:
            return True
        return not any(content.startswith(c) for c in conditions.not_startswith)

    def _build_endswith(self, part: str) -> bool:
        content = self._part_content(part)
        conditions: StrConditionConfig = getattr(self.conditions, part)
        if not conditions.endswith:
            return True
        return any(content.endswith(c) for c in conditions.endswith)

    def _build_not_endswith(self, part: str) -> bool:
        content = self._part_content(part)
        conditions: StrConditionConfig = getattr(self.conditions, part)
        if not conditions.not_endswith:
            return True
        return not any(content.endswith(c) for c in conditions.not_endswith)
