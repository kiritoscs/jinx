import os

from common.po import PoUtil
from common.token import Pos, Token

# 项目根目录
BASE_DIR = os.environ.get("BASE_DIR", "")

# 测试缓存文件目录
TEST_CACHE_DIR = os.environ.get("TEST_CACHE_DIR", "")

# 测试用po文件路径
PO_FILE = os.path.join(BASE_DIR, "tests", "test_cases", "test.po")

# 测试用po文件metadata
METADATA = {
    "Project-Id-Version": "PACKAGE VERSION",
    "Report-Msgid-Bugs-To": "",
    "POT-Creation-Date": "2022-04-13 11:10+0800",
    "PO-Revision-Date": "YEAR-MO-DA HO:MI+ZONE",
    "Last-Translator": "FULL NAME <EMAIL@ADDRESS>",
    "Language-Team": "LANGUAGE <LL@li.org>",
    "Language": "",
    "MIME-Version": "1.0",
    "Content-Type": "text/plain; charset=UTF-8",
    "Content-Transfer-Encoding": "8bit",
}
# 测试用po文件信息, 包含过期
MESSAGES = [
    {
        "msgid": "测试空msgid",
        "msgstr": "",
        "comment": "comment_1",
        "flags": ["fuzzy"],
        "occurrences": [("dir_1/file_1.py", '1')],
    },
    {
        "msgid": "测试msgid",
        "msgstr": "test msgid",
        "comment": "comment_2",
        "flags": [],
        "occurrences": [("dir_1/file_1.py", '2')],
    },
    {
        "msgid": "测试删除msgid",
        "msgstr": "test delete msgid",
        "comment": "comment_3",
        "flags": [],
        "occurrences": [("dir_1/file_1.py", '3')],
    },
]
# 测试用po文件信息, 不包含过期
MESSAGES_WITH_NO_OBSOLETE = MESSAGES[:-1]


# 测试追加写入
TEST_APPEND_WRITE_FILE = os.path.join(TEST_CACHE_DIR, "test_append_write.po")
TEST_APPEND_WRITE_FILE_WITH_NO_OBSOLETE = os.path.join(TEST_CACHE_DIR, "test_append_write_with_no_obsolete.po")


APPEND_TOKENS = [
    Token(
        msgid="测试新增msgid",
        msgstr="test append msgid",
        comment="comment_4",
        flags=[],
        occurrences=[("dir_1/file_1.py", '4')],
        start=Pos(),
        end=Pos(),
    ),
]

APPEND_MESSAGES = [
    {
        "msgid": "测试新增msgid",
        "msgstr": "test append msgid",
        "comment": "comment_4",
        "flags": [],
        "occurrences": [("dir_1/file_1.py", '4')],
    }
]


RESULT_APPEND_MESSAGES = MESSAGES[:-1] + APPEND_MESSAGES + [MESSAGES[-1]]
RESULT_APPEND_WITH_NO_OBSOLETE_MESSAGES = MESSAGES_WITH_NO_OBSOLETE + APPEND_MESSAGES

# 测试覆盖写入
OVERWRITE_TOKENS = [
    Token(
        msgid="测试覆盖msgid",
        msgstr="test overwrite msgid",
        comment="comment_5",
        flags=[],
        occurrences=[],
        start=Pos(),
        end=Pos(),
    )
]


# 测试类
class TestPoBase:
    """
    po文件测试基类
    """

    po = PoUtil(PO_FILE)

    def assert_entry_with_message(self, entry_list, messages):
        """
        验证entry
        """
        assert len(entry_list) == len(messages)
        for seq in range(len(entry_list)):
            assert entry_list[seq].msgid == messages[seq]["msgid"]
            assert entry_list[seq].msgstr == messages[seq]["msgstr"]
            if not entry_list[seq].obsolete:
                assert entry_list[seq].comment == messages[seq]["comment"]
                assert entry_list[seq].flags == messages[seq]["flags"]
                assert entry_list[seq].occurrences == messages[seq]["occurrences"]


class TestPoUtilRead(TestPoBase):
    def test_metadata(self):
        # 验证metadata
        for _key in METADATA:
            assert self.po.po.metadata[_key] == METADATA[_key]

    def test_read_with_obsolete(self):
        # 验证读取所有msgid和msgstr
        entry_list = self.po.read_list(with_obsolete=True)
        self.assert_entry_with_message(entry_list, MESSAGES)

    def test_read_without_obsolete(self):
        # 验证读取所有未过期msgid和msgstr
        entry_list = self.po.read_list(with_obsolete=False)
        self.assert_entry_with_message(entry_list, MESSAGES_WITH_NO_OBSOLETE)


class TestPoUtilWrite(TestPoBase):
    def test_append(self):
        # 验证追加msgid
        self.po.append_write(tokens=APPEND_TOKENS, with_obsolete=True, new_po_file_path=TEST_APPEND_WRITE_FILE)
        new_po = PoUtil(TEST_APPEND_WRITE_FILE)

        entry_list = new_po.read_list(with_obsolete=True)
        self.assert_entry_with_message(entry_list, RESULT_APPEND_MESSAGES)

    def test_append_with_no_obsolete(self):
        # 验证追加msgid, 不包含过期
        self.po.append_write(
            tokens=APPEND_TOKENS, with_obsolete=False, new_po_file_path=TEST_APPEND_WRITE_FILE_WITH_NO_OBSOLETE
        )
        new_po = PoUtil(TEST_APPEND_WRITE_FILE_WITH_NO_OBSOLETE)
        entry_list = new_po.read_list(with_obsolete=False)
        self.assert_entry_with_message(entry_list, RESULT_APPEND_WITH_NO_OBSOLETE_MESSAGES)

    def teardown_method(self):
        # 删除测试用po文件
        if os.path.exists(TEST_APPEND_WRITE_FILE):
            os.remove(TEST_APPEND_WRITE_FILE)
        if os.path.exists(TEST_APPEND_WRITE_FILE_WITH_NO_OBSOLETE):
            os.remove(TEST_APPEND_WRITE_FILE_WITH_NO_OBSOLETE)
