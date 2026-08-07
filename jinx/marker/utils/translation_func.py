"""Django translation function helpers (AST-based import detection)."""

from __future__ import annotations

import ast
from dataclasses import dataclass

from jinx.common.config import config_util
from jinx.common.constants import (
    DEFAULT_TRANSLATION_FUNC_ALIAS,
    DJANGO_TRANSLATE_FUNC_IMPORT_PATH_PREFIX,
    DjangoTranslationFuncEnum,
)


@dataclass
class DjangoTranslateFuncConfig:
    default: str
    alias: str

    def __post_init__(self) -> None:
        DjangoTranslationFuncEnum.check_member(self.default)


def get_translate_func_config() -> DjangoTranslateFuncConfig:
    return DjangoTranslateFuncConfig(
        default=config_util.get("marker.translation_func.default", DjangoTranslationFuncEnum.gettext_lazy.value),
        alias=config_util.get("marker.translation_func.alias", DEFAULT_TRANSLATION_FUNC_ALIAS),
    )


@dataclass
class DjangoTranslationFunc:
    import_path: str
    func_name: str
    alias_name: str

    @classmethod
    def from_config(cls) -> DjangoTranslationFunc:
        cfg = get_translate_func_config()
        import_path = f"{DJANGO_TRANSLATE_FUNC_IMPORT_PATH_PREFIX}{cfg.default} as {cfg.alias}"
        return cls(import_path=import_path, func_name=cfg.default, alias_name=cfg.alias)

    @property
    def call_names(self) -> set[str]:
        return {self.func_name, self.alias_name}


def parse_translation_funcs_from_ast(tree: ast.AST) -> list[DjangoTranslationFunc]:
    """Collect django.utils.translation imports from an AST module."""
    found: list[DjangoTranslationFunc] = []
    if not isinstance(tree, ast.Module):
        return found
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.module != "django.utils.translation":
            continue
        for alias in node.names:
            func_name = alias.name
            alias_name = alias.asname or alias.name
            if alias.asname:
                import_path = f"{DJANGO_TRANSLATE_FUNC_IMPORT_PATH_PREFIX}{func_name} as {alias_name}"
            else:
                import_path = f"{DJANGO_TRANSLATE_FUNC_IMPORT_PATH_PREFIX}{func_name}"
            found.append(
                DjangoTranslationFunc(import_path=import_path, func_name=func_name, alias_name=alias_name)
            )
    return found


def known_call_names(funcs: list[DjangoTranslationFunc]) -> set[str]:
    names: set[str] = set()
    for func in funcs:
        names |= func.call_names
    # always treat common aliases as translation wrappers
    names.update({"_", "gettext", "gettext_lazy", "ugettext", "ugettext_lazy", "pgettext", "pgettext_lazy"})
    return names
