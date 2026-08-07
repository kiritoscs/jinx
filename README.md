# Jinx

Jinx is a one-stop **Django i18n helper**: mark strings, extract entries, machine-translate, export for review, write back, and compile.

## Pipeline

1. **Mark** — wrap user-facing strings with gettext helpers (`marker`, AST-based)
2. **Extract** — push candidates into a `.po` file (`extractor`), or use Django `makemessages`
3. **Translate** — fill empty `msgstr` via Google / Youdao (`translator`)
4. **Review** — export JSON for humans (`exporter`)
5. **Apply** — write confirmed JSON back into PO (`translator -m overwrite|full_match`)
6. **Compile** — PO → MO (`compiler`), or Django `compilemessages`

## Install

```bash
# from source
git clone https://github.com/kiritoscs/jinx
cd jinx
pip install -e ".[dev]"

# then
jinx --help
```

Compatible entrypoint (without install scripts):

```bash
python jinx.py --help
```

Requires **Python 3.11+**.

## Configuration

```bash
cp jinx.template.toml jinx.toml
```

Key sections:

| Section | Purpose |
|---------|---------|
| `[language]` | source (`current`) / target (`dest`) language codes |
| `[marker]` | `strict_mode`, filters, translation func, string conditions |
| `[translator]` | provider: `google_api` \| `youdao_client` |
| `[youdao_client]` | Youdao OpenAPI credentials |

CLI flag `-c /path/to/jinx.toml` overrides discovery. If no config file exists, built-in defaults are used (zh-CN → en).

## Commands

### 1. Mark strings

```bash
jinx marker -t ${YOUR_DJANGO_PROJECT_DIR}
```

Uses an **AST + span edit** pipeline (UTF-8-accurate) to wrap matching string constants with `gettext_lazy as _` (configurable), insert the Django import when missing, and **preserve original formatting/comments**.

- Skips strings already inside gettext calls and docstrings
- Converts common f-strings: `f"你好{name}"` → `_("你好{}").format(name)` (`marker.convert_fstring`)
- Unsupported f-strings (e.g. dynamic format specs) are left unchanged and warned; `strict_mode` skips the whole file if any remain
- Optionally marks Django HTML templates (`suffixes` includes `.html`) with `{% trans "…" %}`

Always review the diff after marking.

### Marker safety modes

```bash
# preview only
jinx marker -t ./myproject --dry-run

# CI: fail if unmarked Chinese strings remain
jinx marker -t ./myproject --check
```


### 2. Extract

**Plan A — Jinx extractor** (based on marker scan):

```bash
jinx extractor -t ${YOUR_DJANGO_PROJECT_DIR} -l ${YOUR_PO_OR_LOCALE}
```

**Plan B — Django (recommended when env is ready):**

```bash
python manage.py makemessages -l en
```

### 3. Machine translate

```bash
jinx translator -p ${YOUR_PO_OR_LOCALE} -o ${OFFICIAL_DICT.json}
```

Modes (`-m`):

| Mode | Behavior |
|------|----------|
| `update` (default) | fill empty `msgstr` only |
| `overwrite` | replace matching entries from translator / dict |
| `full_match` | sync from official dict only (no network) |

Providers: `google_api` (default, free web endpoint, rate-limited), `youdao_client` (API key required).

### 4. Export for review

```bash
jinx exporter -l ${YOUR_PO_OR_LOCALE} -e contents.json
```

### 5. Write reviewed JSON back

```bash
jinx translator -p ${YOUR_PO_OR_LOCALE} -o ${REVIEWED.json} -m overwrite
```

### 6. Compile

```bash
jinx compiler -l ${YOUR_PO_OR_LOCALE}
```

or:

```bash
python manage.py compilemessages
```

## Development

```bash
pip install -e ".[dev]"
pytest -q
```

## License

MIT — see [LICENSE](LICENSE).
