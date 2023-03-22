# Jinx

## 什么是Jinx
Jinx是一个Django项目国际化的一站式辅助工具

Django国际化常常包含以下流程
1. 检查翻译标记
2. 提取词条
3. 机器翻译词条
4. 人工检验词条(将机器翻译好的词条导出交付给相应的人员进行校对)
5. 将确认无误的词条写入po文件
6. 编译

可以看到国际化不是一蹴而就的, 而且每个项目的国际化流程都不尽相同

那么jinx可以帮助你完成以下工作

1. [检查翻译标记](#1检查翻译标记)由[Marker](marker/README.md)负责
2. [提取词条](#2提取词条) 由[Extractor](extractor/README.md)负责, 或者 利用Django自带makemessages命令进行词条提取
3. [机器翻译词条](#3机器翻译词条) 由[Translator](translator/README.md)负责
4. [人工检验词条](#4人工检验词条) 由[Exporter](exporter/README.md)导出json文件, 交付给负责人
5. [将确认无误的词条写入po文件](#5将确认无误的词条写入po文件) 由[Translator](translator/README.md)负责
6. [编译](#6编译) 由[Compiler](compiler/README.md)负责, 或者 利用Django自带compilemessages命令进行编译


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

### 1.检查翻译标记

```bash
python jinx.py marker -d ${YOUR_DJANGO_PROJECT_DIR}
```
- YOUR_DJANGO_PROJECT_DIR: 你的Django项目目录

详细配置参考[配置说明](#配置说明)

标记之后, 需要检查一下标记是否正确, 有时候会出现标记错误的情况, 具体参考[Marker](marker/README.md)

### 2.提取词条
**PlanA**: 利用extractor提取词条, 本质是基于marker的结果进行提取, 所以需要先检查标记结果
```bash
python jinx.py extractor -t ${YOUR_DJANGO_PROJECT_DIR} -l ${YOUR_PO_FILE}
```
- YOUR_DJANGO_PROJECT_DIR: 你的Django项目目录
- YOUR_PO_FILE: 你的po文件目录, 也支持填入locale目录, 会自动寻找locale目录下的对应语言po文件


**PlanB**: Django自带的makemessages命令(推荐)
```bash
python manage.py makemessages -l ${YOUR_LANGUAGE}
```
或者
```bash
djano-admin makemessages -l ${YOUR_LANGUAGE}
```

### 3.机器翻译词条
```bash
python jinx.py translator -p ${YOUR_PO_FILE} -o {YOUR_OFFICIAL_DICT_DIR}
```
- YOUR_PO_FILE: 你的po文件目录, 也支持填入locale目录, 会自动寻找locale目录下的对应语言po文件
- YOUR_OFFICIAL_DICT_DIR: 你的官方词典目录, JSON格式, 用于翻译时的参考, 最大匹配翻译, 参考[官方词典official_dict](official_dict.template.json)

默认白嫖使用GoogleAPI翻译, 略慢

目前内置了以下翻译来源
- youdao_client, 有道翻译服务, 需要自己去申请
- google_api, 暂时通过爬虫的形式使用, 速度较慢

详细配置参考[配置说明](#配置说明)

### 4.人工检验词条
导出词条
```bash
python jinx.py exporter -p ${YOUR_PO_FILE} -e ${YOUR_OUTPUT_DIR}
```
- YOUR_PO_FILE: 你的po文件目录, 也支持填入locale目录, 会自动寻找locale目录下的对应语言po文件
- YOUR_OUTPUT_DIR: 你的输出文件名, 暂时支持json, 默认为contents.json

### 5.将确认无误的词条写入po文件
```bash
python jinx.py translator -p ${YOUR_PO_FILE} -o ${YOUR_FINAL_JSON_FILE} -m overwrite
```
- YOUR_PO_FILE: 你的po文件目录, 也支持填入locale目录, 会自动寻找locale目录下的对应语言po文件
- YOUR_FINAL_JSON_FILE: 你的最终json文件, 用于更新po文件

### 6.编译
**PlanA**: 利用compiler编译
```bash
python jinx.py compiler -l ${YOUR_PO_FILE}
```
- YOUR_PO_FILE: 你的po文件目录, 也支持填入locale目录, 会自动寻找locale目录下的对应语言po文件

**PlanB**: 利用Django compilemessages编译
```bash
python manage.py compilemessages
```
或者
```bash
djano-admin compilemessages
```


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
