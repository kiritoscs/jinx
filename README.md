# Jinx

## 什么是Jinx
Jinx是一个Django项目国际化的一站式辅助工具

包含了`检查翻译标记`, `检查标记语法`, `词条提取`, `词条翻译`等一个Django项目国际化所需要做的所有事情

其中
- [Marker](marker/README.md)负责 `检查翻译标记`, `检查标记语法`
- `词条提取`, 利用Django自带的makemessages命令进行词条提取
- [Translator](translator/README.md)负责 `词条翻译`


## 快速开始

### 安装
因为暂时未提供pip的方式, 可以使用git clone的方式安装, 推荐使用poetry安装依赖

```bash
git clone https://github.com/kiritoscs/jinx

cd jinx

poetry install
```

如果你不想使用poetry, 可以使用pip安装依赖

参考[pyproject.toml](pyproject.toml)里的`[tool.poetry.dependencies]`

### 生成配置文件
```bash
mv jinx.template.toml jinx.toml
```

### 标记

```bash
python jinx.py marker -d ${YOUR_DJANGO_PROJECT_DIR}
```
- YOUR_DJANGO_PROJECT_DIR: 你的Django项目目录

详细配置参考[配置说明](#配置说明)

### 翻译

```bash
python jinx.py translator -p ${YOUR_PO_FILE} -o {YOUR_OFFICIAL_DICT_DIR}
```
- YOUR_PO_FILE: 你的po文件目录, 也支持填入locale目录, 会自动寻找locale目录下的对应语言po文件
- YOUR_OFFICIAL_DICT_DIR: 你的官方词典目录, 用于翻译时的参考, 最大匹配翻译

默认白嫖使用GoogleAPI翻译, 略慢

目前内置了以下翻译来源
- youdao_client, 有道翻译服务, 需要自己去申请
- google_api, 暂时通过爬虫的形式使用, 速度较慢

详细配置参考[配置说明](#配置说明)

### 配置说明

```toml
[language]
# 当前项目语言, 枚举参考 common/constants.py/LanguageEnum
current = "zh-CN"
# 翻译目标语言, 枚举参考 common/constants.py/LanguageEnum
dest = "en"

[marker]
# 标记器
## 严格模式, 存在f-string格式化的需要国际化的字符串时, 会跳过该文件的标记
strict_mode = false

[marker.filter]
# 过滤器, 不想翻译的文件或者目录
## 过滤目录
exclude_paths = [
    "web",
    "scripts",
    "migrations",
    "tests"
]
## 过滤文件
exclude_files = [
    "manage.py",
    "urls.py",
    "wsgi.py",
    "tests.py"
]

[marker.translation_func]
# 默认的翻译函数配置
## 默认的翻译函数
default = "ugettext_lazy"
## 翻译函数别名
alias = "_"

[marker.str_conditions]
# 字符串条件配置

[marker.str_conditions.token]
# token(单词)的字符串条件配置
## 包含
contains = []
## 不包含
not_contains = []
## 以...开头
startswith = []
## 不以...开头
not_startswith = []
## 以...结尾
endswith = []
## 不以...结尾
not_endswith = ["\"\"\"", "'''"]

[marker.str_conditions.source_line]
# source_line(源码)的字符串条件配置
## 包含
contains = []
## 不包含
not_contains = ["logger", "__name__"]
## 以...开头
startswith = []
## 不以...开头
not_startswith = []
## 以...结尾
endswith = []
## 不以...结尾
not_endswith = ["\"\"\"", "'''"]


[translator]
# 翻译器
provider = "google_api"
mode = "update"


[youdao_client]
# 有道翻译客户端配置
url = "https://openapi.youdao.com/api"
app_key = ""
app_secret = ""
# domain是有道翻译的一个参数, 用于区分不同的翻译场景, 一般不需要修改
# 支持的领域参考: common/constants.py/YouDaoSupportDomainEnum
domain = "general"

```
