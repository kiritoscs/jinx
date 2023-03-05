import os

from common.prompt import Prompt


def check_exist(path):
    if not os.path.exists(path):
        Prompt.panic("Path is not exist: {path}", path=path)
