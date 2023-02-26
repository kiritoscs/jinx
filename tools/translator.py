import googletrans

from utils.utils import array_chunk
from utils.config import Config


# 默认目标语言
DEFAULT_DEST = "en"
# 最大同时请求语句数
MAX_CONCURRENT_REQUEST = 10


class TranslateProviderEnum:
    GOOGLE = "google"


class TranslatorBase:
    """翻译基类"""
    def __init__(self, provider: str, config: Config, contents: list[str], official_dict: dict[str, str]):
        self._provider = provider
        self._contents = contents
        self._official_dict = official_dict
        self._config = {}
        self.init_config(config)
        # 翻译结果
        self._result = dict.fromkeys(self._contents, "")

    # 保持输入顺序输出翻译结果
    def get_result(self):
        return [
            self._result.get(_content, _content)
            for _content in self._contents
        ]

    # 初始化配置
    def init_config(self, config: Config):
        raise NotImplementedError

    def translate(self):
        raise NotImplementedError


class GoogleTranslator(TranslatorBase):
    """谷歌翻译"""
    def __init__(self, config: Config, contents: list[str], official_dict: dict[str, str]):
        super(TranslatorBase).__init__(
            provider=TranslateProviderEnum.GOOGLE,
            config=config,
            contents=contents,
            official_dict=official_dict
        )

    def init_config(self, config: Config):
        self._config = {
            "dest": config.get("translator" "dest", default=DEFAULT_DEST),
        }

    def translate(self):
        translator = googletrans.Translator()
        for _slice_contents in array_chunk(self._contents, MAX_CONCURRENT_REQUEST):
            _result = translator.translate(
                _slice_contents,
                dest=self._config.get("dest", DEFAULT_DEST)
            )
            for _r in _result:
                self._result[_r.origin] = _r.text
