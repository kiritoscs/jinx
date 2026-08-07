"""AST-based internationalization marker for Python source files."""
from __future__ import annotations
import ast
import tokenize
from dataclasses import dataclass
from rich.progress import track
from jinx.common.config import config_util
from jinx.common.prompt import Prompt
from jinx.common.utils import list_files, read_file, write_file
from jinx.marker.plugins.file_filter import get_file_filter
from jinx.marker.plugins.str_conditions import StrCondition
from jinx.marker.utils.token import Token, TokenPoint
from jinx.marker.utils.translation_func import DjangoTranslationFunc, known_call_names, parse_translation_funcs_from_ast

@dataclass
class MarkerConfig:
    strict_mode: bool = False

def get_marker_config() -> MarkerConfig:
    return MarkerConfig(strict_mode=bool(config_util.get('marker.strict_mode', False)))

def _lineno(node: ast.AST) -> int:
    return getattr(node, 'lineno', 1) or 1

def _col(node: ast.AST) -> int:
    return getattr(node, 'col_offset', 0) or 0

class _StringMarker(ast.NodeTransformer):
    """Wrap bare string constants that need gettext with a translation call."""

    def __init__(self, source_lines: list[str], call_names: set[str], alias_name: str, filepath: str) -> None:
        self.source_lines = source_lines
        self.call_names = call_names
        self.alias_name = alias_name
        self.filepath = filepath
        self.tokens: list[Token] = []
        self.illegal_tokens: list[Token] = []
        self.changed = False
        self._in_translation_call = 0

    def visit_Call(self, node: ast.Call) -> ast.AST:
        name = self._call_func_name(node.func)
        wrapped = name in self.call_names
        if wrapped:
            self._in_translation_call += 1
        node = self.generic_visit(node)
        if wrapped:
            self._in_translation_call -= 1
        return node

    @staticmethod
    def _call_func_name(func: ast.AST) -> str | None:
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            return func.attr
        return None

    def visit_JoinedStr(self, node: ast.JoinedStr) -> ast.AST:
        text_parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                text_parts.append(value.value)
        combined = ''.join(text_parts)
        source_line = self._source_line(node)
        if StrCondition(token_text=combined or 'f', source_line=source_line).match() or any((StrCondition(token_text=p, source_line=source_line).match() for p in text_parts if p)):
            token = Token(type=tokenize.STRING, token=combined, start_at=TokenPoint(row=_lineno(node), col=_col(node)), end_at=TokenPoint(row=_lineno(node), col=_col(node)), source_line=source_line)
            self.illegal_tokens.append(token)
            Prompt.warning('Unsupported f-string, {filepath}:{row}', filepath=self.filepath, row=_lineno(node))
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        if not isinstance(node.value, str):
            return node
        if self._in_translation_call > 0:
            return node
        source_line = self._source_line(node)
        if not StrCondition(token_text=node.value, source_line=source_line).match():
            return node
        token = Token(type=tokenize.STRING, token=node.value, start_at=TokenPoint(row=_lineno(node), col=_col(node)), end_at=TokenPoint(row=_lineno(node), col=_col(node) + len(repr(node.value))), source_line=source_line)
        self.tokens.append(token)
        self.changed = True
        return ast.Call(func=ast.Name(id=self.alias_name, ctx=ast.Load()), args=[node], keywords=[])

    def _source_line(self, node: ast.AST) -> str:
        idx = _lineno(node) - 1
        if 0 <= idx < len(self.source_lines):
            return self.source_lines[idx]
        return ''

class _DocstringSafeMarker(_StringMarker):
    """Skip wrapping docstring expression constants."""

    def visit_Module(self, node: ast.Module) -> ast.AST:
        return self._visit_body_container(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        return self._visit_body_container(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        return self._visit_body_container(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        return self._visit_body_container(node)

    def _visit_body_container(self, node: ast.AST) -> ast.AST:
        body = getattr(node, 'body', [])
        new_body = []
        for index, stmt in enumerate(body):
            if index == 0 and isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                new_body.append(stmt)
            else:
                new_body.append(self.visit(stmt))
        node.body = new_body
        for field, old_value in ast.iter_fields(node):
            if field == 'body':
                continue
            if isinstance(old_value, list):
                new_values = []
                for value in old_value:
                    if isinstance(value, ast.AST):
                        new_values.append(self.visit(value))
                    else:
                        new_values.append(value)
                setattr(node, field, new_values)
            elif isinstance(old_value, ast.AST):
                setattr(node, field, self.visit(old_value))
        return node

def _ensure_import(tree: ast.Module, default_func: DjangoTranslationFunc) -> bool:
    """Ensure translation import exists. Returns True if import was inserted."""
    existing = parse_translation_funcs_from_ast(tree)
    wanted_names = {default_func.func_name, default_func.alias_name}
    for func in existing:
        if func.alias_name in wanted_names or func.func_name in wanted_names:
            return False
    import_node = ast.ImportFrom(module='django.utils.translation', names=[ast.alias(name=default_func.func_name, asname=default_func.alias_name)], level=0)
    insert_at = 0
    if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant) and isinstance(tree.body[0].value.value, str):
        insert_at = 1
    while insert_at < len(tree.body):
        stmt = tree.body[insert_at]
        if isinstance(stmt, ast.ImportFrom) and stmt.module == '__future__':
            insert_at += 1
            continue
        break
    idx = insert_at
    while idx < len(tree.body) and isinstance(tree.body[idx], (ast.Import, ast.ImportFrom)):
        idx += 1
    tree.body.insert(idx, import_node)
    return True

class FileMarker:
    """Mark a single Python file for Django i18n using AST transforms."""

    def __init__(self, filepath: str) -> None:
        self._fp = filepath
        self._tokens: list[Token] = []
        self._illegal_tokens: list[Token] = []
        self._source = read_file(filepath)
        self._lines = self._source.splitlines()

    @property
    def is_legal(self) -> bool:
        return not self._illegal_tokens

    @property
    def illegal_tokens(self) -> list[Token]:
        """Tokens that cannot be auto-wrapped (e.g. f-strings)."""
        return self._illegal_tokens

    @property
    def tokens(self) -> list[Token]:
        if not self._tokens and (not self._illegal_tokens):
            self._scan_only()
        return self._tokens

    def _scan_only(self) -> None:
        try:
            tree = ast.parse(self._source)
        except SyntaxError as e:
            Prompt.error('Failed to parse {filepath}: {e}', filepath=self._fp, e=e)
            return
        default = DjangoTranslationFunc.from_config()
        funcs = parse_translation_funcs_from_ast(tree) or [default]
        call_names = known_call_names(funcs)
        transformer = _DocstringSafeMarker(self._lines, call_names, default.alias_name, self._fp)
        transformer.visit(tree)
        self._tokens = transformer.tokens
        self._illegal_tokens = transformer.illegal_tokens

    def handle(self, only_extract_tokens: bool=False) -> None:
        try:
            tree = ast.parse(self._source)
        except SyntaxError as e:
            Prompt.error('Failed to parse {filepath}: {e}', filepath=self._fp, e=e)
            return
        default = DjangoTranslationFunc.from_config()
        funcs = parse_translation_funcs_from_ast(tree)
        if not funcs:
            funcs = [default]
            need_import = True
        else:
            need_import = False
        call_names = known_call_names(funcs)
        transformer = _DocstringSafeMarker(self._lines, call_names, default.alias_name, self._fp)
        new_tree = transformer.visit(tree)
        ast.fix_missing_locations(new_tree)
        self._tokens = transformer.tokens
        self._illegal_tokens = transformer.illegal_tokens
        if only_extract_tokens:
            return
        cfg = get_marker_config()
        if not self.is_legal and cfg.strict_mode:
            return
        if not transformer.changed and (not transformer.illegal_tokens):
            return
        if not transformer.changed:
            return
        if need_import or not parse_translation_funcs_from_ast(new_tree):
            _ensure_import(new_tree, default)
            ast.fix_missing_locations(new_tree)
        try:
            output = ast.unparse(new_tree)
        except Exception as e:
            Prompt.error('Failed to unparse {filepath}: {e}', filepath=self._fp, e=e)
            return
        write_file(self._fp, output)

class MarkerTool:

    def __init__(self, target_path: str | None=None) -> None:
        self._target_path = target_path or ''
        self._tokens: list[Token] = []

    @property
    def files(self) -> list[str]:
        filters = get_file_filter()
        return list_files(target_path=self._target_path, exclude_paths=filters.exclude_paths, exclude_files=filters.exclude_files)

    @property
    def tokens(self) -> list[Token]:
        if not self._tokens:
            self.handle(only_extract_tokens=True)
        return self._tokens

    def handle(self, only_extract_tokens: bool=False) -> None:
        if only_extract_tokens:
            tokens: list[Token] = []
            for file in self.files:
                handler = FileMarker(file)
                handler.handle(only_extract_tokens=True)
                tokens.extend(handler.tokens)
            self._tokens = tokens
            return
        for file in track(self.files, description='Marking...'):
            FileMarker(file).handle()
