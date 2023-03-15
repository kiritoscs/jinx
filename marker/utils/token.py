import tokenize
from dataclasses import dataclass
from io import StringIO
from tokenize import TokenInfo
from typing import Generator

from common.utils import read_file


@dataclass
class TokenPoint:
    """
    :param row: 行号
    :param col: 列号
    """

    row: int
    col: int


@dataclass
class Token:
    """Token"""

    start_at: TokenPoint
    end_at: TokenPoint
    type: int
    token: str = ""
    source_line: str = ""


def generate_tokens(fp: str) -> Generator[TokenInfo, None, None]:
    return tokenize.generate_tokens(StringIO(read_file(fp)).readline)
