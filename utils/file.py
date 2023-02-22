import os

# 默认编码
DEFAULT_ENCODING = "utf-8"


def is_sub_string(s: str, sub_string_list: list) -> bool:
    """判断路径是否匹配"""
    for _s in sub_string_list:
        if _s in s:
            return True
    return False


def list_files(dir_path: str, exclude_paths: list = None, exclude_files: list = None, suffix: str = "py") -> list:
    """获取指定路径下所有后缀为suffix的文件"""
    if not os.path.isdir(dir_path):
        return [dir_path]
    files = []
    for root, __, file_names in os.walk(dir_path):
        if exclude_paths and is_sub_string(root, exclude_paths):
            continue
        for file_name in file_names:
            if not file_name.endswith(suffix):
                continue
            if exclude_files and is_sub_string(file_name, exclude_files):
                continue
            files.append(os.path.join(root, file_name))

    return files


def read_file(fp: str, encoding: str = None):
    """读取文件"""
    try:
        with open(fp, "r", encoding=DEFAULT_ENCODING) as f:
            return f.read()
    except Exception:  # pylint: disable=broad-except
        with open(fp, "r", encoding=encoding) as f:
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
