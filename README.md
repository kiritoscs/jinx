# Django-18n

## 用法

```
python django-i18n.py --help

Usage: django-i18n.py [OPTIONS] COMMAND [ARGS]...

  国际化工具

Options:
  -c, --config_path PATH  配置文件路径
  --help                  Show this message and exit.

Commands:
  marker  标记国际化字符串
```

### marker, 标记国际化字符串
```
python django-i18n.py marker --help

Usage: django-i18n.py marker [OPTIONS]

  标记国际化字符串

Options:
  -d, --dir_path PATH         要标记的目录  [required]
  -m, --multi_thread BOOLEAN  是否开启多线程
  --help                      Show this message and exit.
```
