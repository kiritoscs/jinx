"""Lightweight token model used by extractor / reporting."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TokenPoint:
    row: int
    col: int


@dataclass
class Token:
    """A string candidate discovered by the marker."""

    start_at: TokenPoint
    end_at: TokenPoint
    type: int
    token: str = ""
    source_line: str = ""
