import os
import re
import tokenize

from io import StringIO
from collections import namedtuple, defaultdict
from typing import Generator, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from rich.progress import track

from utils.file import list_files, read_file, write_file
from utils.config import Config
from utils.constants import MAX_WORKERS
from utils.condition import Condition
from utils.parse_django_translate_func import DjangoTranslateFunc, ParseDjangoTranslateFunc


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


class FileMarker(object):
    """
    给py文件中的中文字符串添加国际化函数, 单个文件
    """
    def __init__(self, filepath: str, config: Config):
        self._fp = filepath
        self._config = config
        # 非合法的
        self._is_legal = False
        self.token_generator = self.generate_tokens()
        # _tokens 中文词列表
        self._tokens = defaultdict(list)
        # 所有行
        self._lines = read_file(self._fp).split("\n")
        # 需要标记的前缀, 可能同时存在lazy和非lazy
        self._mark_prefixs = []
        # 需要标记的后缀
        self._mark_suffix = ")"
        # 是否缺少翻译函数
        self._missing_translate_funcs = True
        # 翻译函数
        self._default_mark_prefix = None
        self._translate_funcs = self._parse_translate_funcs()

    def _build_condition(self, _t: Token) -> Tuple[Condition, Condition]:
        """构建条件"""
        _c_token = Condition(_t.token, **{
            f"c_{k}": v
            for k, v in self._config.get("marker", "str_conditions", {}).get("token", {}).items()
        })
        _c_source_line = Condition(_t.source_line, **{
            f"c_{k}": v
            for k, v in self._config.get("marker", "str_conditions", {}).get("source_line", {}).items()
        })
        return _c_token, _c_source_line

    def _parse_translate_funcs(self) -> list[DjangoTranslateFunc]:
        """解析翻译函数"""
        _parser = ParseDjangoTranslateFunc(config=self._config, contents=self._lines)
        _funcs = _parser.parse()
        self._default_mark_prefix = f"{_parser.use_default().alias_name}("
        if not _funcs:
            _default_translate_func = _parser.use_default()
            _funcs.append(_parser.use_default())
        else:
            self._missing_translate_funcs = False
        for _f in _funcs:
            self._mark_prefixs.append(f"{_f.alias_name}(")
        return _funcs

    def get_tokens(self) -> defaultdict:
        """对外, 获取标记后的中文词列表"""
        if not self._tokens:
            self.extract_tokens()
        return self._tokens

    def _write_file(self) -> None:
        """写入文件"""
        if not self._tokens:
            return
        write_file(self._fp, self._lines)

    def generate_tokens(self) -> Generator[tokenize.TokenInfo, None, None]:
        """利用tokenize标记py代码文件"""
        return tokenize.generate_tokens(StringIO(read_file(self._fp)).readline)

    def _extract_token(self, _t: Token) -> None:
        """提取token"""
        try:
            # 根据过滤规则, 将符合条件的中文字符串添加到待标记列表中
            _c_token, _c_source_line = self._build_condition(_t)
            if not (_c_token.match_chinese(_t.token) and _c_token.match() and _c_source_line.match()):
                return
            self._tokens[_t.start_at.row].append(_t)

        except Exception as e:
            print(f"[ERROR] handler_string, token: {_t._asdict()}, error: {e}")

    def extract_tokens(self) -> None:
        """第一步, 遍历所有token, 提取中文字符串"""
        for _type, _val, _st, _et, _source in self.token_generator:
            _token = Token(_type, _val, TokenPoint(*_st), TokenPoint(*_et), _source)
            if _type == tokenize.STRING:
                self._extract_token(_token)

    def _mark_translate_func(self, current_line: str, mark_prefix: str, _t: Token, offset: int):
        """匹配单个翻译函数"""
        _func_len = len(mark_prefix)
        _current_prefix_start = _t.start_at.col + offset - _func_len
        _current_prefix_end = _t.start_at.col + offset
        _current_prefix = current_line[_current_prefix_start:_current_prefix_end]
        # 如果当前行已经存在翻译函数, 则不再添加
        if _current_prefix.strip() == mark_prefix.strip():
            return True
        # 考虑到字符串超长导致的代码格式化, 检查上一行是否添加了翻译函数
        if mark_prefix.strip() in self._lines[_t.start_at.row - 2]:
            return True
        return False

    def check(self) -> None:
        """第二步, 因为国际化函数不支持f-string字符串格式化方法, 所以需要要把不符合的过滤出来提示修改"""
        if not self._tokens:
            return
        _del_rows = []
        for _row in self._tokens.keys():
            _current_line = self._lines[_row - 1]
            _legal_tokens = []
            for _t in self._tokens[_row]:
                if _current_line[_t.start_at.col] == "f":
                    print(f"[ERROR] 国际化不支持f-string, {self._fp}:{_row}, line: {_current_line}")
                    continue
                _legal_tokens.append(_t)
            if _legal_tokens:
                self._tokens[_row] = _legal_tokens
            else:
                _del_rows.append(_row)
        for _row in _del_rows:
            del self._tokens[_row]
        if not _del_rows:
            self._is_legal = True

    def mark(self) -> None:
        """第三步, 打标记"""
        if not self._tokens:
            return
        for _row in self._tokens.keys():
            _current_line = self._lines[_row - 1]
            # 当前因添加翻译函数所增加的列偏移量
            _line_offset = 0
            for _t in self._tokens[_row]:
                # 先置为默认翻译函数
                real_mark_prefix = self._default_mark_prefix
                _is_match = False
                for _mark_prefix in self._mark_prefixs:
                    _is_match = self._mark_translate_func(
                        current_line=_current_line, mark_prefix=_mark_prefix, _t=_t, offset=_line_offset
                    )
                    if _is_match:
                        real_mark_prefix = _mark_prefix
                        break
                if _is_match:
                    continue
                _new_line = _current_line[:_t.start_at.col + _line_offset] + real_mark_prefix + _t.token
                _new_line += self._mark_suffix
                _new_line += _current_line[_t.end_at.col + _line_offset:]
                _current_line = _new_line
                _line_offset += len(real_mark_prefix) + len(self._mark_suffix)
            if self._lines[_row - 1] != _current_line:
                self._lines[_row - 1] = _current_line

    def add_import(self):
        """第四步, 添加导入语句"""
        if not self._missing_translate_funcs and self._tokens:
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
                print(f"find empty line error: {e}")
        if not insert_idx:
            for _idx, _line in enumerate(self._lines):
                if _line == "\n" or not _line.startswith("#"):
                    insert_idx = _idx
                    break
        for _translate_func in self._translate_funcs:
            self._lines.insert(insert_idx, _translate_func.import_path)

    def process(self):
        """主逻辑函数, 给py文件中的中文字符串添加国际化函数"""
        self.extract_tokens()
        self.check()
        if not self._is_legal and self._config.get(key="force_mode", default=False):
            return
        self.mark()
        self.add_import()
        self._write_file()


class Marker(object):
    """标记器"""
    def __init__(self, dir_path: str = None, config_path: str = None, multi_thread: bool = False):
        self._dir_path = dir_path
        self._config = Config(config_path)
        self._files = self._list_files()
        self._multi_thread = multi_thread

    def _list_files(self):
        """列出所有py文件"""
        return list_files(
            dir_path=self._dir_path,
            exclude_paths=self._config.get(key="exclude_paths", default=[]),
            exclude_files=self._config.get(key="exclude_files", default=[]),
            suffix=self._config.get(key="suffix", default=".py"),
        )

    def run(self):
        """运行"""
        if self._multi_thread:
            print("Start Marking with multi thread...")
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
                tasks = [ex.submit(FileMarker(fp, self._config).process) for fp in self._files]
                if as_completed(tasks):
                    print("all tasks done")
        else:
            for _file in track(self._files, description="Marking..."):
                FileMarker(_file, self._config).process()
