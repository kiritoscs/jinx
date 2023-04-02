"""
This file contains utility functions for the project.
"""
import os
import shutil
import typing
from importlib import import_module

import arrow
import json5 as json

from jinx.common.constants import DEFAULT_ENCODING, FILE_SUFFIX


def array_chunk(data: list[typing.Any], size=100):
    return [data[i : i + size] for i in range(0, len(data), size)]


def is_sub_string(s: str, sub_string_list: list[typing.Any]) -> bool:
    """
    遍历字符串列表，判断字符串是否包含其中的字符串
    """
    for _s in sub_string_list:
        if _s in s:
            return True
    return False


def list_files(target_path: str, exclude_paths: list = None, exclude_files: list = None) -> list[str]:
    """获取指定路径下所有后缀为suffix的文件"""
    if not os.path.isdir(target_path):
        return [target_path]
    files = []
    for root, __, file_names in os.walk(target_path):
        if exclude_paths and is_sub_string(root, exclude_paths):
            continue
        for file_name in file_names:
            if not file_name.endswith(FILE_SUFFIX):
                continue
            if exclude_files and is_sub_string(file_name, exclude_files):
                continue
            files.append(os.path.join(root, file_name))

    return files


def read_file(fp: str, encoding: str = None, is_json: bool = False):
    """读取文件"""
    try:
        with open(fp, encoding=DEFAULT_ENCODING) as f:
            if is_json:
                return json.load(f)
            return f.read()
    except Exception:  # pylint: disable=broad-except
        with open(fp, encoding=encoding) as f:
            if is_json:
                return json.load(f)
            return f.read()


def write_file(fp: str, contents: list = None, encoding: str = None):
    """写文件"""
    if not contents:
        return
    content = "\n".join(contents)
    try:
        with open(fp, "w", encoding=DEFAULT_ENCODING) as f:
            f.write(content)
    except Exception:  # pylint: disable=broad-except
        with open(fp, "w", encoding=encoding) as f:
            f.write(content)


def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    """
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError as err:
        raise ImportError("%s doesn't look like a module path" % dotted_path) from err

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError as err:
        raise ImportError('Module "%s" does not define a "%s" attribute/class' % (module_path, class_name)) from err


def copy_file(file_path: str, target_path: str = None):
    """
    copy file from file_path to target_path
    :param file_path: file path
    :param target_path: target path, default is file_path_bak_current_time
    """
    if not target_path:
        current = arrow.now().format("YYYY-MM-DDTHH-mm-ss")
        target_path = f"{file_path}_bak_{current}"
    shutil.copyfile(file_path, target_path)
