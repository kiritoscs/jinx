import typing

from rich.progress import track


def match_official_dict(official_dict: typing.Dict[str, str], content: str) -> str:
    """匹配官方词典, 最大匹配"""
    if official_dict:
        if content in official_dict:
            return official_dict[content]
        max_official_content = ""
        for official_content, translate_content in official_dict.items():
            if official_content in content:
                if len(official_content) > len(max_official_content):
                    max_official_content = official_content
        if max_official_content:
            content = content.replace(max_official_content, official_dict[max_official_content])
    return content


class TranslatorBase:
    """翻译接口/Client基类"""

    def __init__(
        self,
        source_lang: str,
        dest_lang: str,
        official_dict: typing.Dict[str, str] = None,
        contents: typing.List[str] = None,
    ):
        self._source_lang = source_lang
        self._dest_lang = dest_lang
        self._official_dict = official_dict if official_dict else {}
        self._contents = contents
        self._result: typing.Dict[str, str] = {}

    @property
    def result(self) -> typing.Dict[str, str]:
        """翻译结果"""
        return self._result

    def pre_translate(self, content: str) -> str:
        """预翻译, 即匹配官方词典"""
        return match_official_dict(self._official_dict, content)

    def translate_once(self, content: str) -> str:
        """翻译单个语句, 各个翻译接口/Client需要实现该方法"""
        raise NotImplementedError

    def translate(self) -> None:
        """翻译, 如果有API/Client支持批量翻译, 可以重写该方法"""
        for content in track(self._contents, description="翻译中..."):
            if content in self._result:
                continue
            self._result[content] = self.translate_once(content)
