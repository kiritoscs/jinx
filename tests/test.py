import os

import pytest

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("BASE_DIR", BASE_DIR)

# 测试缓存文件目录
TEST_CACHE_DIR = os.path.join(BASE_DIR, "tests", "cache")
if not os.path.exists(TEST_CACHE_DIR):
    os.makedirs(TEST_CACHE_DIR)
os.environ.setdefault("TEST_CACHE_DIR", TEST_CACHE_DIR)

# 测试目录
TEST_DIRS = [
    "common",
]


# 执行测试
if __name__ == '__main__':
    for test_dir in TEST_DIRS:
        pytest.main(['-v', "-s", os.path.join(BASE_DIR, "tests", f"test_{test_dir}")])
