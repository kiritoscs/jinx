"""Format-preserving AST marker for Python i18n strings."""
from __future__ import annotations
import ast
import tokenize
from dataclasses import dataclass, field
from rich.progress import track
from jinx.common.config import config_util
from jinx.common.prompt import Prompt
from jinx.common.utils import apply_span_replacements, list_files, offset_for_position, read_file, write_file
from jinx.marker.fstring import convert_joined_str, render_expr
from jinx.marker.plugins.file_filter import get_file_filter
from jinx.marker.plugins.str_conditions import StrCondition
from jinx.marker.utils.token import Token, TokenPoint
from jinx.marker.utils.translation_func import DjangoTranslationFunc, known_call_names, parse_translation_funcs_from_ast

@dataclass
class MarkerConfig:
    strict_mode: bool = False
    convert_fstring: bool = True
    suffixes: list[str] = field(default_factory=lambda: ['.py', '.html'])

def get_marker_config() -> MarkerConfig:
    raw_suffixes = config_util.get('marker.suffixes', ['.py', '.html']) or ['.py', '.html']
    return MarkerConfig(strict_mode=bool(config_util.get('marker.strict_mode', False)), convert_fstring=bool(config_util.get('marker.convert_fstring', True)), suffixes=list(raw_suffixes))

def _lineno(node: ast.AST) -> int:
    return getattr(node, 'lineno', 1) or 1

def _col(node: ast.AST) -> int:
    return getattr(node, 'col_offset', 0) or 0

def _end_lineno(node: ast.AST) -> int:
    return getattr(node, 'end_lineno', _lineno(node)) or _lineno(node)

def _end_col(node: ast.AST) -> int:
    return getattr(node, 'end_col_offset', _col(node)) or _col(node)

def _node_span(source: str, node: ast.AST) -> tuple[int, int] | None:
    segment = ast.get_source_segment(source, node)
    if segment is None:
        return None
    start = offset_for_position(source, _lineno(node), _col(node))
    if hasattr(node, 'end_lineno') and node.end_lineno is not None and (node.end_col_offset is not None):
        end = offset_for_position(source, node.end_lineno, node.end_col_offset)
        return (start, end)
    return (start, start + len(segment))

def _is_docstring(parent_stack: list[ast.AST], node: ast.Constant) -> bool:
    if not parent_stack:
        return False
    parent = parent_stack[-1]
    if not isinstance(parent, ast.Expr) or parent.value is not node:
        return False
    if len(parent_stack) < 2:
        return False
    grand = parent_stack[-2]
    if not isinstance(grand, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return False
    body = grand.body
    return bool(body) and body[0] is parent

@dataclass
class _Edit:
    start: int
    end: int
    text: str

class _CollectMarker(ast.NodeVisitor):
    """Collect span replacements without mutating the tree (preserves file formatting)."""

    def __init__(self, source: str, source_lines: list[str], call_names: set[str], alias_name: str, filepath: str, convert_fstring: bool) -> None:
        self.source = source
        self.source_lines = source_lines
        self.call_names = call_names
        self.alias_name = alias_name
        self.filepath = filepath
        self.convert_fstring = convert_fstring
        self.tokens: list[Token] = []
        self.illegal_tokens: list[Token] = []
        self.edits: list[_Edit] = []
        self.changed = False
        self._in_translation_call = 0
        self._stack: list[ast.AST] = []

    def generic_visit(self, node: ast.AST) -> None:
        self._stack.append(node)
        super().generic_visit(node)
        self._stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        name = self._call_func_name(node.func)
        wrapped = name in self.call_names
        if wrapped:
            self._in_translation_call += 1
        self.generic_visit(node)
        if wrapped:
            self._in_translation_call -= 1

    @staticmethod
    def _call_func_name(func: ast.AST) -> str | None:
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            return func.attr
        return None

    def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
        text_parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                text_parts.append(value.value)
        combined = ''.join(text_parts)
        source_line = self._source_line(node)
        needs = StrCondition(token_text=combined or 'f', source_line=source_line).match() or any((StrCondition(token_text=p, source_line=source_line).match() for p in text_parts if p))
        if not needs:
            self.generic_visit(node)
            return
        token = Token(type=tokenize.STRING, token=combined, start_at=TokenPoint(row=_lineno(node), col=_col(node)), end_at=TokenPoint(row=_end_lineno(node), col=_end_col(node)), source_line=source_line)
        if self._in_translation_call > 0:
            self.generic_visit(node)
            return
        if self.convert_fstring:
            result = convert_joined_str(node, self.alias_name)
            if result.ok and result.node is not None:
                span = _node_span(self.source, node)
                if span is not None:
                    self.tokens.append(Token(type=tokenize.STRING, token=result.msgid, start_at=token.start_at, end_at=token.end_at, source_line=source_line))
                    self.edits.append(_Edit(span[0], span[1], render_expr(result.node)))
                    self.changed = True
                    Prompt.info('Converted f-string at {filepath}:{row}', filepath=self.filepath, row=_lineno(node))
                    return
            token.token = combined
            self.illegal_tokens.append(token)
            Prompt.warning('Unsupported f-string (left unchanged), {filepath}:{row}: {reason}', filepath=self.filepath, row=_lineno(node), reason=result.reason if not result.ok else 'span missing')
            return
        self.illegal_tokens.append(token)
        Prompt.warning('Unsupported f-string, {filepath}:{row}', filepath=self.filepath, row=_lineno(node))

    def visit_Constant(self, node: ast.Constant) -> None:
        if not isinstance(node.value, str):
            return
        if _is_docstring(self._stack, node):
            return
        source_line = self._source_line(node)
        if not StrCondition(token_text=node.value, source_line=source_line).match():
            return
        token = Token(type=tokenize.STRING, token=node.value, start_at=TokenPoint(row=_lineno(node), col=_col(node)), end_at=TokenPoint(row=_end_lineno(node), col=_end_col(node)), source_line=source_line)
        self.tokens.append(token)
        if self._in_translation_call > 0:
            return
        span = _node_span(self.source, node)
        if span is None:
            return
        segment = self.source[span[0]:span[1]]
        self.edits.append(_Edit(span[0], span[1], f'{self.alias_name}({segment})'))
        self.changed = True

    def _source_line(self, node: ast.AST) -> str:
        idx = _lineno(node) - 1
        if 0 <= idx < len(self.source_lines):
            return self.source_lines[idx]
        return ''

def _ensure_import_text(source: str, default_func: DjangoTranslationFunc) -> str | None:
    """Return new source with translation import inserted, or None if already present."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    existing = parse_translation_funcs_from_ast(tree)
    wanted = {default_func.func_name, default_func.alias_name}
    for func in existing:
        if func.alias_name in wanted or func.func_name in wanted:
            return None
    import_line = f'from django.utils.translation import {default_func.func_name} as {default_func.alias_name}\n'
    lines = source.splitlines(keepends=True)
    if not lines:
        return import_line + source
    insert_at = 0
    while insert_at < len(lines) and (lines[insert_at].startswith('#!') or (lines[insert_at].startswith('#') and 'coding' in lines[insert_at])):
        insert_at += 1
    try:
        mod = ast.parse(source)
        if mod.body and isinstance(mod.body[0], ast.Expr) and isinstance(mod.body[0].value, ast.Constant) and isinstance(mod.body[0].value.value, str):
            end = mod.body[0].end_lineno or 1
            insert_at = max(insert_at, end)
    except SyntaxError:
        pass
    idx = insert_at
    while idx < len(lines):
        stripped = lines[idx].lstrip()
        if stripped.startswith('from __future__'):
            idx += 1
            continue
        break
    while idx < len(lines):
        stripped = lines[idx].lstrip()
        if stripped.startswith('import ') or stripped.startswith('from '):
            idx += 1
            continue
        break
    lines.insert(idx, import_line)
    return ''.join(lines)

class FileMarker:
    """Mark a single Python file for Django i18n (format-preserving span edits)."""

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
        return self._illegal_tokens

    @property
    def tokens(self) -> list[Token]:
        if not self._tokens and (not self._illegal_tokens):
            self._scan_only()
        return self._tokens

    def _run_collect(self) -> _CollectMarker | None:
        try:
            tree = ast.parse(self._source)
        except SyntaxError as e:
            Prompt.error('Failed to parse {filepath}: {e}', filepath=self._fp, e=e)
            return None
        default = DjangoTranslationFunc.from_config()
        funcs = parse_translation_funcs_from_ast(tree) or [default]
        call_names = known_call_names(funcs)
        cfg = get_marker_config()
        collector = _CollectMarker(source=self._source, source_lines=self._lines, call_names=call_names, alias_name=default.alias_name, filepath=self._fp, convert_fstring=cfg.convert_fstring)
        collector.visit(tree)
        return collector

    def _scan_only(self) -> None:
        collector = self._run_collect()
        if collector is None:
            return
        self._tokens = collector.tokens
        self._illegal_tokens = collector.illegal_tokens

    def handle(self, only_extract_tokens: bool=False) -> None:
        collector = self._run_collect()
        if collector is None:
            return
        self._tokens = collector.tokens
        self._illegal_tokens = collector.illegal_tokens
        if only_extract_tokens:
            return
        cfg = get_marker_config()
        if collector.illegal_tokens and cfg.strict_mode:
            return
        if not collector.changed:
            return
        new_source = apply_span_replacements(self._source, [(e.start, e.end, e.text) for e in collector.edits])
        default = DjangoTranslationFunc.from_config()
        with_import = _ensure_import_text(new_source, default)
        if with_import is not None:
            new_source = with_import
        write_file(self._fp, new_source)

class MarkerTool:

    def __init__(self, target_path: str | None=None) -> None:
        self._target_path = target_path or ''
        self._tokens: list[Token] = []

    @property
    def files(self) -> list[str]:
        filters = get_file_filter()
        cfg = get_marker_config()
        suffixes = [s for s in cfg.suffixes if s == '.py'] or ['.py']
        return list_files(target_path=self._target_path, exclude_paths=filters.exclude_paths, exclude_files=filters.exclude_files, suffixes=suffixes)

    @property
    def tokens(self) -> list[Token]:
        if not self._tokens:
            self.handle(only_extract_tokens=True)
        return self._tokens

    def handle(self, only_extract_tokens: bool=False) -> None:
        from jinx.marker.template_marker import TemplateMarkerTool
        cfg = get_marker_config()
        if only_extract_tokens:
            tokens: list[Token] = []
            for file in self.files:
                handler = FileMarker(file)
                handler.handle(only_extract_tokens=True)
                tokens.extend(handler.tokens)
            if '.html' in cfg.suffixes or '.htm' in cfg.suffixes:
                tokens.extend(TemplateMarkerTool(self._target_path).tokens)
            self._tokens = tokens
            return
        for file in track(self.files, description='Marking Python...'):
            FileMarker(file).handle()
        if '.html' in cfg.suffixes or '.htm' in cfg.suffixes:
            TemplateMarkerTool(self._target_path).handle()
