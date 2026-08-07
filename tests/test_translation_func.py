"""AST translation-func parser tests."""

from __future__ import annotations

import ast

from jinx.marker.utils.translation_func import (
    DjangoTranslationFunc,
    known_call_names,
    parse_translation_funcs_from_ast,
)


def test_parse_import_with_alias() -> None:
    tree = ast.parse("from django.utils.translation import gettext_lazy as _\n")
    funcs = parse_translation_funcs_from_ast(tree)
    assert len(funcs) == 1
    assert funcs[0].func_name == "gettext_lazy"
    assert funcs[0].alias_name == "_"


def test_parse_import_without_alias() -> None:
    tree = ast.parse("from django.utils.translation import gettext\n")
    funcs = parse_translation_funcs_from_ast(tree)
    assert funcs[0].alias_name == "gettext"
    assert funcs[0].func_name == "gettext"


def test_parse_multiple_names() -> None:
    tree = ast.parse("from django.utils.translation import gettext, gettext_lazy as _\n")
    funcs = parse_translation_funcs_from_ast(tree)
    names = {(f.func_name, f.alias_name) for f in funcs}
    assert ("gettext", "gettext") in names
    assert ("gettext_lazy", "_") in names


def test_parse_ignores_other_imports() -> None:
    tree = ast.parse("from os import path\nimport sys\n")
    assert parse_translation_funcs_from_ast(tree) == []


def test_parse_non_module_returns_empty() -> None:
    node = ast.parse("x = 1").body[0]
    assert parse_translation_funcs_from_ast(node) == []


def test_from_config_defaults(clean_config) -> None:
    func = DjangoTranslationFunc.from_config()
    assert func.alias_name == "_"
    assert "gettext" in func.func_name
    assert "django.utils.translation" in func.import_path


def test_known_call_names_includes_builtins() -> None:
    names = known_call_names([])
    assert "_" in names
    assert "gettext_lazy" in names
