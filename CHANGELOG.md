# Changelog

## 0.3.0

- Marker: AST f-string → named/positional gettext format; dry-run/check; parallel workers
- Templates: `{% trans %}`, `{% blocktrans %}`, auto `{% load i18n %}`
- Import merge for `django.utils.translation`
- Skip heuristics for identity-like short strings
- CLI: `init`, `status`, `plural-snippet`, `--version`
- Config validation; PO backup prune; translate summary
- PyPI publish workflow (Trusted Publishing)

## 0.2.0

- Package restructure as `jinx.*` with console entry
- Lazy config, stdlib enums, PoUtil fixes, unit tests
