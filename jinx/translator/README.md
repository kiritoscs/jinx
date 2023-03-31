# Translator - 懒人翻译器
<hr>

## Translator是什么
Translator是一个将po文件中词条进行翻译的工具, 支持指定词典功能


## 快速开始
<hr>
`python jinx.py -c [config_path] translator -p [po_path] -o [official_dict_path]`

config_path: 配置文件路径, 默认为jinx/jinx.toml

po_path: 需要翻译的po文件路径, 例如: ${project_path}/locale/en/LC_MESSAGES/django.po

official_dict_path: 官方词典JSON文件路径, 例如: jinx/official_dict.json

## 原理
<hr>

核心模块: `polib`, `requests`, 各个翻译API

polib模块提供了一个简单的接口, 用于读写po文件

通过读取po文件以及官方词典, 将词条进行翻译, 并将翻译结果写入po文件中

官方词典匹配原则: 最大替换原则, 即不能完全匹配的时候, 会取最长匹配到的词条进行替换
