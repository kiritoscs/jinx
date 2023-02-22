import os

# 默认编码
DEFAULT_ENCODING = "utf-8"


def list_files(dir_path: str, exclude_paths: list = None, exclude_files: list = None, suffix: str = "py") -> list:
    """获取指定路径下所有后缀为suffix的文件"""
    if not os.path.isdir(dir_path):
        return [dir_path]
    files = []
    for root, dir_names, file_names in os.walk(dir_path):
        for dir_name in dir_names:
            if exclude_paths and dir_name in exclude_paths:
                continue
            for file_name in file_names:
                if exclude_files and file_name in exclude_files:
                    continue
                if file_name.endswith(suffix):
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
