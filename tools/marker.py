import os
import re
import tokenize

from io import StringIO
from dataclasses import dataclass
from collections import namedtuple, defaultdict
from typing import Generator

from rich.progress import track

from tools.base import ToolBase, GlobalConfig, DjangoTranslateFunc
from utils.utils import list_files, read_file, write_file
from utils.condition import Condition
from utils.constants import (
    DJANGO_TRANSLATE_FUNC_IMPORT_PATH_PREFIX,
    DEFAULT_TRANSLATE_FUNC,
    DEFAULT_TRANSLATE_FUNC_ALIAS
)


Suffix = ".py"
TokenPoint = namedtuple("TokenPoint", ["row", "col"])
Token = namedtuple(
    "Token",
    [
        "type",
        "token",
        "start_at",
        "end_at",
        "source_line",
    ],
)

CHINESE_PATTERN = re.compile("[\u4e00-\u9fa5]+")


@dataclass
class MarkerConfig:
    strict_mode: bool = True
    translate_func: DjangoTranslateFunc = None
    str_conditions_source_line: dict = None
    str_conditions_token: dict = None


class DjangoTranslateFuncParser(object):
    """解析django翻译函数"""
    def __init__(self, marker_config: MarkerConfig, contents: list = None):
        self._marker_config = marker_config
        # contents 文件内容列表
        self._contents = contents or []
        # 根层级配置
        self._translate_funcs = []

    def _parse_line(self, line: str):
        # 去除注释
        _origin_line = line
        line = line.split(DJANGO_TRANSLATE_FUNC_IMPORT_PATH_PREFIX)[1].strip().split("#")[0].strip()
        # alias函数名
        if "as" in line:
            func_name, alias_name = line.split("as")
            self._translate_funcs.append(DjangoTranslateFunc(import_path=_origin_line, alias_name=alias_name.strip()))
            return
        if "," in line:
            for _f in line.split(","):
                self._translate_funcs.append(
                    DjangoTranslateFunc(import_path=_origin_line, alias_name=_f.strip())
                )
            return
        self._translate_funcs.append(DjangoTranslateFunc(import_path=_origin_line, alias_name=line))

    def parse(self):
        if not self._contents:
            return self._translate_funcs
        # 逐行解析
        for _c in self._contents:
            if not _c.startswith(DJANGO_TRANSLATE_FUNC_IMPORT_PATH_PREFIX):
                continue
            self._parse_line(_c)
        return self._translate_funcs

    @property
    def default(self):
        return self._marker_config.translate_func


class FileMarker:
    """
    单个py文件国际化标记器
    单文件, 给py文件中的中文字符串添加国际化函数
    """
    def __init__(self, filepath: str, global_config: GlobalConfig, marker_config: MarkerConfig):
        self._fp = filepath
        self._global_config = global_config
        self._marker_config = marker_config
        # _tokens 中文词列表
        self._tokens = defaultdict(list)
        # 所有行
        self._lines = read_file(filepath).split("\n")
        # 非合法的行
        self._illegal_tokens = []
        # 默认翻译函数
        self._default_translate_func = self._marker_config.translate_func
        # 是否需要插入import语句
        self._missing_import = False
        # 翻译函数列表
        self._translate_funcs = self._parse_translate_funcs()

    @property
    def is_legal(self) -> bool:
        """是否合法"""
        return False if self._illegal_tokens else True

    def _build_source_line_condition(self, t: Token) -> Condition:
        """构建原文条件"""
        return Condition(t.source_line, **{
            f"c_{k}": v
            for k, v in self._marker_config.str_conditions_source_line.items()
        })

    def _build_token_condition(self, t: Token) -> Condition:
        """构建token条件"""
        return Condition(t.token, **{
            f"c_{k}": v
            for k, v in self._marker_config.str_conditions_token.items()
        })

    def _parse_translate_funcs(self) -> list[DjangoTranslateFunc]:
        """解析翻译函数"""
        _parser = DjangoTranslateFuncParser(marker_config=self._marker_config, contents=self._lines)
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
            _c_token = self._build_token_condition(t)
            _c_source_line = self._build_source_line_condition(t)
            if not (_c_token.match_chinese(t.token) and _c_token.match() and _c_source_line.match()):
                return
            self._tokens[t.start_at.row].append(t)

        except Exception as e:
            print(f"[ERROR] handler_string, token: {t._asdict()}, error: {e}")

    def _extract_tokens(self) -> None:
        """
        <核心逻辑> 第一步
        遍历所有token, 提取中文字符串
        """
        for _type, _val, _st, _et, _source in self.token_generator:
            _token = Token(_type, _val, TokenPoint(*_st), TokenPoint(*_et), _source)
            if _type == tokenize.STRING:
                self._extract_token(_token)

    @property
    def tokens(self) -> dict:
        """待标记的token"""
        if not self._tokens:
            self._extract_tokens()
        return self._tokens

    def _match_translate_func(self, current_line: str, translate_func: DjangoTranslateFunc, t: Token, offset: int):
        """匹配单个翻译函数"""
        _func_len = len(translate_func.prefix)
        _current_prefix_start = t.start_at.col + offset - _func_len
        _current_prefix_end = t.start_at.col + offset
        _current_prefix = current_line[_current_prefix_start:_current_prefix_end]
        # 如果当前行已经存在翻译函数, 则不再添加
        if _current_prefix.strip() == translate_func.prefix.strip():
            return True
        # 考虑到字符串超长导致的代码格式化, 检查上一行是否添加了翻译函数
        if translate_func.prefix in self._lines[t.start_at.row - 2]:
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
                print(f"国际化不支持f-string格式化, 行: {_t.start_at.row}, 单词: {_t.token}")

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
                        current_line=_current_line, translate_func=_translate_func, t=_t, offset=_line_offset
                    )
                    if _is_match:
                        real_mark_prefix = _translate_func.prefix
                        real_mark_suffix = _translate_func.suffix
                        break
                if _is_match:
                    continue
                _new_line = _current_line[:_t.start_at.col + _line_offset] + real_mark_prefix + _t.token
                _new_line += real_mark_suffix
                _new_line += _current_line[_t.end_at.col + _line_offset:]
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
                print(f"查找空行失败: {e}")
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

    def run(self):
        """
        <核心逻辑>
        主流程
        """
        self._extract_tokens()
        self._check()
        # 严格模式下, 存在需要修复的f-string格式语句, 跳过当前文件的后续流程
        if not self.is_legal and self._marker_config.strict_mode:
            return
        self._mark()
        self._add_import()
        self._write()


class MarkerTool(ToolBase):
    def __init__(self, target_path: str = None, config_path: str = None):
        super().__init__(config_path)
        self._target_path = target_path
        self._marker_config = None
        self._init_module_config()

    def _init_module_config(self):
        self._marker_config = MarkerConfig(
            strict_mode=self._config.get(module="marker", key="strict_mode", default=False),
            translate_func=DjangoTranslateFunc(
                import_path=DJANGO_TRANSLATE_FUNC_IMPORT_PATH_PREFIX,
                func_name=self._config.get(
                    module="marker", key="translate_func", default={}).get("default", DEFAULT_TRANSLATE_FUNC),
                alias_name=self._config.get(
                    module="marker", key="translate_func", default={}).get("alias", DEFAULT_TRANSLATE_FUNC_ALIAS),
                ),
            str_conditions_source_line=self._config.get(
                module="marker", key="str_conditions", default={}).get("source_line", {})
            ,
            str_conditions_token=self._config.get(
                module="marker", key="str_conditions", default={}).get("token", {})
        )

    @property
    def files(self):
        """列出符合过滤条件的所有文件"""
        return list_files(
            target_path=self._target_path,
            exclude_paths=self._global_config.exclude_paths,
            exclude_files=self._global_config.exclude_files
        )

    def run(self):
        for _file in track(self.files, description="Marking..."):
            FileMarker(_file, self._global_config, self._marker_config).run()
