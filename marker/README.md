# Marker - 一个易用的国际化文本标记器

<hr>

## 背景
摘自[Django官方文档](https://docs.djangoproject.com/zh-hans/4.1/topics/i18n/translation/)

为了使Django项目可以翻译, 你需要在Python代码和模板中添加少量钩子, 这些钩子被成为 translation strings.

它们告知Django: 如果在终端用户语言里, 这个文本有对应的翻译, 那么应该使用翻译.

标记字符串是你的职责, 系统只会翻译它知道的字符串, 然后Django提供工具将翻译字符串提取到message file中.

## 什么是Marker
<hr>

Marker是一个将需要翻译文本给标记出来的工具

代码迭代期间, 难免会出现遗漏的情况, 因为Django只会翻译它知道的字符串, 所以需要一个工具来帮助我们标记需要翻译的字符串

## 原理
<hr>

核心模块: `tokenize`, `re`

tokenize模块提供了一个简单的接口, 用于将源代码分解为一个个token

re模块提供了正则表达式的功能, 用于匹配指定语言的字符串

通过tokenize模块, 我们可以获取到源代码中的字符串, 然后根据配置文件中的条件进行判断, 如果满足条件, 则将字符串添加上标记

## 配置说明
<hr>

### strict_mode
是否开启严格模式, 默认为False

如果该文件中需要翻译的字符串是通过f-string形式格式化的, 则会提示具体的行数以及内容, 该文件跳过标记, 但不会影响其他文件的标记

### translate_func
默认的翻译函数, 即文件中并没有使用翻译函数时, 会使用该函数进行标记

- translate_func.default: 翻译函数名, 默认: ugettext_lazy
- translate_func.alias: 翻译函数别名, 默认: _

### str_conditions
字符串条件, 用于判断是否需要标记

- source_line: 原文
- token: 词法分析后的token

目前支持以下条件:
- startswith: 判断字符串是否以某个字符串开头
- not_startswith: 判断字符串是否不以某个字符串开头
- endswith: 判断字符串是否以某个字符串结尾
- not_endswith: 判断字符串是否不以某个字符串结尾
- contains: 判断字符串是否包含某个字符串
- not_contains: 判断字符串是否不包含某个字符串

## 暂时可能标记错误的场景
- f-string格式化的字符串, 暂时通过提示的方式进行处理, 需要手动处理
- 过长的字符串, 或者多行字符串, 暂未能处理
