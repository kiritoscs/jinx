# Jinx

## 什么是Jinx
<hr>

Jinx是一个Django项目国际化的一站式辅助工具

包含了`检查翻译标记`, `检查标记语法`, `词条提取`, `词条翻译`等一个Django项目国际化所需要做的所有事情

其中
- [Marker](marker/README.md)负责 `检查翻译标记`, `检查标记语法`
- `词条提取`, 利用Django自带的makemessages命令进行词条提取
- [Translator](translator/README.md)负责 `词条翻译`
