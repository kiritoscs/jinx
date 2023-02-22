# Jinx

## 用法

```
python jinx.py --help

Usage: jinx.py [OPTIONS] COMMAND [ARGS]...

  Jinx, 一个方便的国际化工具

Options:
  -c, --config_path PATH  配置文件路径
  --help                  Show this message and exit.

Commands:
  marker  标记国际化字符串
```

### marker, 标记国际化字符串
```
python jinx.py marker --help

Usage: jinx.py marker [OPTIONS]

  标记国际化字符串

Options:
  -d, --dir_path PATH         要标记的目录  [required]
  -m, --multi_thread BOOLEAN  是否开启多线程
  --help                      Show this message and exit.
```
