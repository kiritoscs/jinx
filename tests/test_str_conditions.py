"""String condition filter tests."""

from __future__ import annotations

from jinx.marker.plugins.str_conditions import StrCondition, StrConditionConfig, StrConditions


def test_language_match_chinese(clean_config) -> None:
    assert StrCondition(token_text="你好", source_line="x = '你好'").match()
    assert not StrCondition(token_text="hello", source_line="x = 'hello'").match()


def test_not_contains_source_line(clean_config) -> None:
    conditions = StrConditions(
        source_line=StrConditionConfig(not_contains=["logger"]),
        token=StrConditionConfig(),
    )
    assert not StrCondition(
        token_text="你好",
        source_line='logger.info("你好")',
        conditions=conditions,
    ).match()
    assert StrCondition(
        token_text="你好",
        source_line='msg = "你好"',
        conditions=conditions,
    ).match()


def test_contains_token(clean_config) -> None:
    conditions = StrConditions(
        source_line=StrConditionConfig(),
        token=StrConditionConfig(contains=["错误"]),
    )
    assert StrCondition(token_text="发生错误", source_line="", conditions=conditions).match()
    assert not StrCondition(token_text="成功", source_line="", conditions=conditions).match()


def test_startswith_endswith(clean_config) -> None:
    conditions = StrConditions(
        source_line=StrConditionConfig(),
        token=StrConditionConfig(startswith=["前"], endswith=["后"], not_endswith=['"""']),
    )
    assert StrCondition(token_text="前后", source_line="", conditions=conditions).match()
    assert not StrCondition(token_text="后前", source_line="", conditions=conditions).match()
