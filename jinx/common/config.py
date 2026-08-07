"""Configuration loading (lazy, import-safe)."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jinx.common.constants import LanguageEnum, LanguageRegexEnum
from jinx.common.prompt import Prompt


@dataclass
class LanguageConfig:
    """Source / destination language settings."""

    current: str = LanguageEnum.Chinese.value
    dest: str = LanguageEnum.English.value
    re: str = ""

    def __post_init__(self) -> None:
        LanguageEnum.check_member(self.current)
        LanguageEnum.check_member(self.dest)
        if self.re:
            return
        if self.current not in LanguageRegexEnum:
            Prompt.panic(
                "Built-in RE missing current language: {current}, "
                "please add it to jinx.common.constants.LanguageRegexEnum",
                current=self.current,
            )
        self.re = LanguageRegexEnum[self.current]


class ConfigUtil:
    """TOML config loader with dotted-key access."""

    def __init__(self, config_path: str | Path | None = None) -> None:
        self._fp = Path(config_path) if config_path else None
        self._config: dict[str, Any] = {}
        if self._fp is not None and self._fp.is_file():
            self._load()

    def _load(self) -> None:
        assert self._fp is not None
        with self._fp.open("rb") as f:
            self._config = tomllib.load(f)

    def reload(self, config_path: str | Path) -> None:
        self._fp = Path(config_path)
        self._config = {}
        if self._fp.is_file():
            self._load()

    def get(self, key: str | None = None, default: Any = None) -> Any:
        """
        Read a config value.

        Nested keys use dots, e.g. ``language.current``.
        Missing keys return ``default``. Explicit empty values (``""``, ``[]``,
        ``False``, ``0``) are preserved and not replaced by ``default``.
        """
        if not key:
            return self._config
        node: Any = self._config
        for part in key.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node


_config_util: ConfigUtil | None = None
_language: LanguageConfig | None = None


def _default_config_path() -> Path:
    env = os.environ.get("CONFIG_PATH")
    if env:
        return Path(env)
    base = os.environ.get("BASE_DIR")
    if base:
        return Path(base) / "jinx.toml"
    cwd = Path.cwd() / "jinx.toml"
    if cwd.is_file():
        return cwd
    # package-adjacent template fallback (optional user copy)
    return Path(__file__).resolve().parents[2] / "jinx.toml"


def get_config_util() -> ConfigUtil:
    global _config_util
    if _config_util is None:
        path = _default_config_path()
        _config_util = ConfigUtil(config_path=path if path.is_file() else None)
    return _config_util


def get_language() -> LanguageConfig:
    global _language
    if _language is None:
        cfg = get_config_util()
        _language = LanguageConfig(
            current=cfg.get("language.current", LanguageEnum.Chinese.value),
            dest=cfg.get("language.dest", LanguageEnum.English.value),
            re=cfg.get("language.re", "") or "",
        )
    return _language


def init_config(config_path: str | Path | None = None) -> ConfigUtil:
    """(Re)initialize global config from an explicit path or defaults."""
    global _config_util, _language
    if config_path is not None:
        path = Path(config_path)
        _config_util = ConfigUtil(config_path=path if path.is_file() else None)
    else:
        path = _default_config_path()
        _config_util = ConfigUtil(config_path=path if path.is_file() else None)
    _language = None
    return _config_util


# Backward-compatible module-level accessors used by tools.
# Properties via simple aliases that resolve lazily through functions.


class _ConfigProxy:
    def get(self, key: str | None = None, default: Any = None) -> Any:
        return get_config_util().get(key, default)

    def reload(self, config_path: str | Path) -> None:
        init_config(config_path)


class _LanguageProxy:
    @property
    def current(self) -> str:
        return get_language().current

    @property
    def dest(self) -> str:
        return get_language().dest

    @property
    def re(self) -> str:
        return get_language().re


config_util = _ConfigProxy()
language = _LanguageProxy()

__all__ = [
    "LanguageConfig",
    "ConfigUtil",
    "config_util",
    "language",
    "get_config_util",
    "get_language",
    "init_config",
]
