"""Translation provider unit tests (network mocked)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from jinx.common.constants import TranslatorProviderEnum
from jinx.translator.provider.google_api import GoogleAPI
from jinx.translator.provider.provider import Provider
from jinx.translator.provider.youdao_client import YoudaoClient, get_youdao_config


def test_provider_google_instance() -> None:
    client = Provider.get_instance(
        source_lang="zh-CN",
        dest_lang="en",
        provider=TranslatorProviderEnum.GoogleAPI.value,
        contents=["x"],
    )
    assert isinstance(client, GoogleAPI)


def test_provider_youdao_instance() -> None:
    client = Provider.get_instance(
        source_lang="zh-CN",
        dest_lang="en",
        provider=TranslatorProviderEnum.YoudaoClient.value,
        contents=["x"],
    )
    assert isinstance(client, YoudaoClient)


def test_provider_unknown_panics() -> None:
    with pytest.raises(SystemExit):
        Provider.get_instance(
            source_lang="zh-CN",
            dest_lang="en",
            provider="not_a_provider",
            contents=[],
        )


def test_google_full_match_skips_network() -> None:
    client = GoogleAPI(
        source_lang="zh-CN",
        dest_lang="en",
        official_dict={"你好": "hello"},
        contents=["你好"],
    )
    with patch("jinx.translator.provider.google_api.requests.get") as get:
        assert client.translate_once("你好") == "hello"
        get.assert_not_called()


def test_google_parses_result_container() -> None:
    client = GoogleAPI(source_lang="zh-CN", dest_lang="en", contents=["你好"])
    html_body = '<div class="result-container">Hello &amp; Hi</div>'
    mock_resp = MagicMock()
    mock_resp.text = html_body
    mock_resp.raise_for_status = MagicMock()
    with patch("jinx.translator.provider.google_api.requests.get", return_value=mock_resp) as get:
        assert client.translate_once("你好") == "Hello & Hi"
        get.assert_called_once()
        assert "timeout" in get.call_args.kwargs


def test_google_parses_t0_class() -> None:
    client = GoogleAPI(source_lang="zh-CN", dest_lang="en", contents=["x"])
    mock_resp = MagicMock()
    mock_resp.text = '<div class="t0">World</div>'
    mock_resp.raise_for_status = MagicMock()
    with patch("jinx.translator.provider.google_api.requests.get", return_value=mock_resp):
        assert client.translate_once("世界") == "World"


def test_google_empty_when_no_match() -> None:
    client = GoogleAPI(source_lang="zh-CN", dest_lang="en", contents=["x"])
    mock_resp = MagicMock()
    mock_resp.text = "<html>nope</html>"
    mock_resp.raise_for_status = MagicMock()
    with patch("jinx.translator.provider.google_api.requests.get", return_value=mock_resp):
        assert client.translate_once("世界") == ""


def test_google_request_error() -> None:
    client = GoogleAPI(source_lang="zh-CN", dest_lang="en", contents=["x"])
    with patch(
        "jinx.translator.provider.google_api.requests.get",
        side_effect=requests.Timeout("slow"),
    ):
        assert client.translate_once("世界") == ""


def test_google_generate_url_contains_langs() -> None:
    client = GoogleAPI(source_lang="zh-CN", dest_lang="en")
    url = client._generate_url("你好")
    assert "tl=en" in url
    assert "sl=zh-CN" in url
    assert "translate.google.com" in url


def test_youdao_full_match_skips_network() -> None:
    client = YoudaoClient(
        source_lang="zh-CN",
        dest_lang="en",
        official_dict={"你好": "hello"},
        contents=["你好"],
    )
    with patch("jinx.translator.provider.youdao_client.requests.post") as post:
        assert client.translate_once("你好") == "hello"
        post.assert_not_called()


def test_youdao_success() -> None:
    client = YoudaoClient(source_lang="zh-CN", dest_lang="en", contents=["你好"])
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"translation": ["Hello"]}
    with patch("jinx.translator.provider.youdao_client.requests.post", return_value=mock_resp) as post:
        assert client.translate_once("你好") == "Hello"
        post.assert_called_once()
        assert post.call_args.kwargs.get("timeout") is not None


def test_youdao_empty_translation_list() -> None:
    client = YoudaoClient(source_lang="zh-CN", dest_lang="en", contents=["x"])
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"translation": []}
    with patch("jinx.translator.provider.youdao_client.requests.post", return_value=mock_resp):
        assert client.translate_once("世界") == ""


def test_youdao_request_error() -> None:
    client = YoudaoClient(source_lang="zh-CN", dest_lang="en", contents=["x"])
    with patch(
        "jinx.translator.provider.youdao_client.requests.post",
        side_effect=requests.ConnectionError("down"),
    ):
        assert client.translate_once("世界") == ""


def test_youdao_truncate_helpers() -> None:
    assert YoudaoClient.truncate(None) is None
    assert YoudaoClient.truncate("short") == "short"
    long = "a" * 25
    out = YoudaoClient.truncate(long)
    assert out is not None
    assert str(len(long)) in out
    assert out.startswith("aaaaaaaaaa")


def test_youdao_encrypt_stable() -> None:
    assert YoudaoClient.encrypt("abc") == YoudaoClient.encrypt("abc")
    assert len(YoudaoClient.encrypt("abc")) == 64


def test_get_youdao_config_defaults(clean_config) -> None:
    cfg = get_youdao_config()
    assert cfg.domain == "general"
    assert "youdao" in cfg.url
