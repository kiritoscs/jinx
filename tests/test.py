import os

import pytest

# 塞入一个环境变量, 让程序知道是在跑单测
os.environ.setdefault("TESTING", "True")

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("BASE_DIR", BASE_DIR)

# 测试缓存文件目录
TEST_CACHE_DIR = os.path.join(BASE_DIR, "tests", "cache")
if not os.path.exists(TEST_CACHE_DIR):
    os.makedirs(TEST_CACHE_DIR)
os.environ.setdefault("TEST_CACHE_DIR", TEST_CACHE_DIR)

# 测试案例文件目录
TEST_CASE_DIR = os.path.join(BASE_DIR, "tests", "test_cases")
if not os.path.exists(TEST_CASE_DIR):
    os.makedirs(TEST_CASE_DIR)
os.environ.setdefault("TEST_CASE_DIR", TEST_CASE_DIR)


# 执行测试
if __name__ == '__main__':
    pytest.main(['-v', "-s", os.path.join(BASE_DIR, "tests")])
