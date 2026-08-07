"""Utility tests."""

from jinx.common.utils import array_chunk, is_sub_string
from jinx.translator.provider.base import match_official_dict


def test_array_chunk() -> None:
    assert array_chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]


def test_is_sub_string() -> None:
    assert is_sub_string("/a/migrations/b", ["migrations"])
    assert not is_sub_string("/a/b", ["migrations"])


def test_match_official_dict_full() -> None:
    mr = match_official_dict({"你好": "hello"}, "你好")
    assert mr.full_match
    assert mr.content == "hello"


def test_match_official_dict_partial() -> None:
    mr = match_official_dict({"你好": "hello"}, "你好世界")
    assert not mr.full_match
    assert "hello" in mr.content
