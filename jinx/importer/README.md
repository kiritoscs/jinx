# Importer - 词条录入
<hr>

## Importer是什么
Importer即指定JSON文件, 将其词条写入po文件中


## 快速开始
<hr>
`python jinx.py -c ${CONFIG_PATH} importer -p ${PO_PATH} -o {$YOUR_FINAL_DICT_PATH}`

CONFIG_PATH: 配置文件路径, 默认为: jinx/jinx.toml

PO_PATH: 需要翻译的po文件路径, 例如: ${project_path}/locale/en/LC_MESSAGES/django.po

YOUR_FINAL_DICT_PATH: 产品核对之后的JSON文件路径, 支持指定目录搜索目录下的json文件, 例如: jinx/official_dict.json

## 原理
<hr>

核心模块: `polib`, `json/json5`

polib模块提供了一个简单的接口, 用于读写po文件

json/json5模块提供了一个简单的接口, 用于读写json文件, 为什么json5, 因为json5支持注释, 有利于词条的管理
