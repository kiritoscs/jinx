import os
import tokenize
import typing
from collections import defaultdict
from dataclasses import asdict, dataclass
from io import StringIO
from typing import Generator

from rich.progress import track

from common import Prompt
from common.config import config_util
from common.utils import list_files, read_file, write_file
from marker.plugins.file_filter import file_filter
from marker.plugins.str_conditions import StrCondition
from marker.utils.token import Token, TokenPoint, generate_tokens
from marker.utils.translation_func import (
    DjangoTranslationFunc,
    DjangoTranslationFuncParser,
)


@dataclass
class MarkerConfig:
    strict_mode: bool


marker_config = MarkerConfig(strict_mode=config_util.get("marker.strict_mode", False))


class FileMarker:
    """
    单个py文件国际化标记器
    单文件, 给py文件中的中文字符串添加国际化函数
    :param filepath: 文件路径
    """

    def __init__(self, filepath: str):
        self._fp = filepath
        # _tokens 中文词列表
        self._tokens: typing.Dict[typing.Any, list] = defaultdict(list)
        # 所有行
        self._lines = read_file(filepath).split("\n")
        # 非合法的行
        self._illegal_tokens: typing.List[Token] = []
        # 默认翻译函数
        self._default_translate_func = DjangoTranslationFuncParser(contents=self._lines).default
        # 是否需要插入import语句
        self._missing_import = False
        # 翻译函数列表
        self._translate_funcs = self._parse_translate_funcs()

    @property
    def is_legal(self) -> bool:
        """是否合法"""
        return False if self._illegal_tokens else True

    def _parse_translate_funcs(self) -> list[DjangoTranslationFunc]:
        """解析翻译函数"""
        _parser = DjangoTranslationFuncParser(contents=self._lines)
        _funcs = _parser.parse()
        if not _funcs:
            _funcs.append(self._default_translate_func)
        else:
            self._missing_import = True
        return _funcs

    @property
    def token_generator(self) -> Generator[tokenize.TokenInfo, None, None]:
        """利用tokenize标记py代码文件"""
        return tokenize.generate_tokens(StringIO(read_file(self._fp)).readline)

    def _extract_token(self, t: Token) -> None:
        """匹配规则, 根据过滤规则, 判断是否提取token"""
        try:
            if not StrCondition(token=t).match():
                return
            self._tokens[t.start_at.row].append(t)

        except Exception as e:
            Prompt.error("handler_string, token: {token}, error: {e}", token=asdict(t), e=e)

    def _extract_tokens(self) -> None:
        """
        <核心逻辑> 第一步
        遍历所有token, 提取中文字符串
        """
        for _type, _val, _st, _et, _source in generate_tokens(self._fp):
            _token = Token(
                type=_type, token=_val, start_at=TokenPoint(*_st), end_at=TokenPoint(*_et), source_line=_source
            )
            if _type == tokenize.STRING:
                self._extract_token(_token)

    @property
    def tokens(self) -> list[Token]:
        """待标记的token"""
        if not self._tokens:
            self._extract_tokens()
        tokens = []
        for _tokens in self._tokens.values():
            tokens.extend(_tokens)

        return tokens

    def _match_translate_func(
        self,
        current_line: str,
        translation_func: DjangoTranslationFunc,
        t: Token,
        offset: int,
    ):
        """匹配单个翻译函数"""
        _func_len = len(translation_func.prefix)
        _current_prefix_start = t.start_at.col + offset - _func_len
        _current_prefix_end = t.start_at.col + offset
        _current_prefix = current_line[_current_prefix_start:_current_prefix_end]
        # 如果当前行已经存在翻译函数, 则不再添加
        if _current_prefix.strip() == translation_func.prefix.strip():
            return True
        # 考虑到字符串超长导致的代码格式化, 检查上一行是否添加了翻译函数
        if translation_func.prefix in self._lines[t.start_at.row - 2]:
            return True
        return False

    def _check(self) -> None:
        """
        <核心逻辑> 第二步
        检查是否存在需要国际化的字符串是通过f-string格式化的
        """
        if not self._tokens:
            return
        _del_rows = []
        for _row in self._tokens.keys():
            _current_line = self._lines[_row - 1]
            _legal_tokens = []
            for _t in self._tokens[_row]:
                if _current_line[_t.start_at.col] == "f":
                    self._illegal_tokens.append(_t)
                    continue
                _legal_tokens.append(_t)
            if _legal_tokens:
                self._tokens[_row] = _legal_tokens
            else:
                _del_rows.append(_row)
        for _row in _del_rows:
            del self._tokens[_row]

        if not self.is_legal:
            for _t in self._illegal_tokens:
                Prompt.warning("Unsupported f-string, row: {row}, token: {token}", row=_t.start_at.row, token=_t.token)

    def _mark(self) -> None:
        """
        <核心逻辑> 第三步
        给需要国际化的字符串添加翻译函数
        """
        if not self._tokens:
            return
        for _row in self._tokens.keys():
            _current_line = self._lines[_row - 1]
            # 当前因添加翻译函数所增加的列偏移量
            _line_offset = 0
            for _t in self._tokens[_row]:
                # 先置为默认翻译函数
                real_mark_prefix = self._default_translate_func.prefix
                real_mark_suffix = self._default_translate_func.suffix
                _is_match = False
                for _translate_func in self._translate_funcs:
                    _is_match = self._match_translate_func(
                        current_line=_current_line,
                        translation_func=_translate_func,
                        t=_t,
                        offset=_line_offset,
                    )
                    if _is_match:
                        real_mark_prefix = _translate_func.prefix
                        real_mark_suffix = _translate_func.suffix
                        break
                if _is_match:
                    continue
                _new_line = _current_line[: _t.start_at.col + _line_offset] + real_mark_prefix + _t.token
                _new_line += real_mark_suffix
                _new_line += _current_line[_t.end_at.col + _line_offset :]
                _current_line = _new_line
                _line_offset += len(real_mark_prefix) + len(real_mark_suffix)
            if self._lines[_row - 1] != _current_line:
                self._lines[_row - 1] = _current_line

    def _add_import(self):
        """
        <核心逻辑> 第四步
        添加导入语句
        """
        if self._missing_import and self._tokens:
            return
        insert_idx = 0
        for _idx, _line in enumerate(self._lines):
            try:
                if (
                    (_line.startswith("import") or _line.startswith("from"))
                    and _idx < len(self._lines) - 1
                    # 空行可能为"", "\n"
                    and self._lines[_idx + 1] in ["", os.linesep]
                ):
                    insert_idx = _idx + 1
                    break
            except Exception as e:
                Prompt.error(f"Failed to find empty line: {e}")
        if not insert_idx:
            for _idx, _line in enumerate(self._lines):
                if _line == "\n" or not _line.startswith("#"):
                    insert_idx = _idx
                    break
        for _translate_func in self._translate_funcs:
            self._lines.insert(insert_idx, _translate_func.import_path)

    def _write(self):
        """
        <核心逻辑> 第五步
        将修改后的内容写入文件
        """
        if not self._tokens:
            return
        write_file(self._fp, self._lines)

    def handle(self, only_extract_tokens: bool = False):
        """
        <核心逻辑>
        主流程
        """
        self._extract_tokens()
        self._check()
        # 仅提取tokens, 不做后续处理
        if only_extract_tokens:
            return
        # 严格模式下, 存在需要修复的f-string格式语句, 跳过当前文件的后续流程
        if not self.is_legal and marker_config.strict_mode:
            return
        self._mark()
        self._add_import()
        self._write()


class MarkerTool:
    def __init__(self, target_path: str = None):
        self._target_path = target_path
        self._tokens: typing.List[Token] = []

    @property
    def files(self):
        """列出符合过滤条件的所有文件"""
        return list_files(
            target_path=self._target_path,
            exclude_paths=file_filter.exclude_paths,
            exclude_files=file_filter.exclude_files,
        )

    @property
    def tokens(self):
        if not self._tokens:
            self.handle(only_extract_tokens=True)
        return self._tokens

    def handle(self, only_extract_tokens: bool = False):
        if only_extract_tokens:
            tokens = []
            for _file in self.files:
                _handler = FileMarker(_file)
                _handler.handle(only_extract_tokens)
                tokens.extend(_handler.tokens)
            self._tokens = tokens
        else:
            for _file in track(self.files, description="Marking..."):
                FileMarker(_file).handle()
