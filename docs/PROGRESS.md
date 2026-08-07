# Jinx modernization — progress memory

> **Last updated:** 2026-08-07  
> **Repo:** `/Users/kiritoscs/Desktop/jinx`  
> **Branch:** `master` · **ahead of origin/master by 14 commits (not pushed)**  
> **Version:** `0.3.0`  
> **Tests:** `153 passed` (`pytest -q`)

Read this file first in a new session before exploring from scratch.

---

## Goal (user intent)

- Modernize years-old Django i18n CLI tool **jinx**
- Optimize from multiple angles (packaging, correctness, DX, tests)
- **Hard rule:** any surgical change to existing Python code in this repo should prefer **AST** (not regex rewrites of `.py`)
- Feature-oriented commits; full pipeline (“一把梭”)

---

## Current product state

Installable package layout:

```
jinx/
  cli.py
  common/          # config, constants, po, prompt, utils, validate, path
  marker/          # AST marker, fstring, skip, import_merge, templates, plural_hints
  extractor|translator|exporter|compiler/
  commands/        # init, status
  data/jinx.template.toml
demo_django_project/   # mini shop for e2e walkthrough (sources kept unmarked)
```

### CLI (`jinx --help`)

| Command | Notes |
|---------|--------|
| `init` | Write `jinx.toml` from bundled template |
| `status -t … [-l …]` | Pending marks, PO gaps, plural hints; exit 1 if work left |
| `marker -t …` | `--dry-run`, `--check`, `-j/--workers` |
| `extractor` / `translator` / `exporter` / `compiler` | Core pipeline |
| `plural-snippet` | Print `ngettext_lazy` paste snippet |
| `--version` | 0.3.0 |

### Marker capabilities (done)

- AST span edits (UTF-8 byte `col_offset`) → **format-preserving** wraps
- f-string → `_("…{name}").format(name=name)` (Django/Ruff-aligned **named** style)
- `fstring_style = named|positional`
- Dynamic format_spec / nested f-string desugar
- Import **merge** into existing `django.utils.translation` import
- Skip heuristics: short strings, `name="张三"`, `utf-8`, etc. (`marker.skip`)
- Templates: `{% trans %}`, `{% blocktrans %}` + `{{ var }}`, auto `{% load i18n %}`
- Parallel workers (`marker.workers` / `-j`)
- dry-run / check for CI

### Other hardening (done)

- Lazy config, stdlib Enums, `resolve_po_path`, PoUtil write fixes
- Config validate on CLI; translator success/fail summary
- PO backup + prune (`po.backup`, `po.backup_keep`)
- Google translator retries/UA; unit tests ~153
- Design doc: `docs/superpowers/specs/2026-08-07-jinx-modernization-design.md`
- CI: `.github/workflows/main.yml` (3.11/3.12)
- PyPI: `.github/workflows/publish.yml` (Trusted Publishing on release)
- Changelog: `CHANGELOG.md`

---

## Local commits not on origin (newest first)

```
a03e037 feat: jinx init/status/plural-snippet, ngettext hints, v0.3.0 + PyPI workflow
f38647f feat: parallel marker, import merge, fstring styles, blocktrans templates
c957ae3 feat: dry-run/check marker, skip heuristics, config validate, translate summary
144943a fix: emit Django-style named placeholders for f-string i18n
1a7cc5c fix: fully desugar f-strings via AST including dynamic specs
107decb feat: harden marker for f-strings, format-preserving edits, templates
bd220ed chore: keep demo Django project unmarked for reproducible walkthrough
30c92b0 fix: extract msgids already wrapped by gettext; add demo shop project
745e3f1 test: cover core modules with unit and CLI integration tests
829173d docs: refresh README and config template for jinx 0.2
725cba0 ci: run pytest on Python 3.11+ and refresh pre-commit
ce0a802 test: add unit tests for config, po, marker, cli, and utils
48655f6 feat: restructure as installable jinx package with modern core
ff5e34e docs: add modernization design and AST edit policy
```

**Not pushed.** User has not asked to push/PR yet.

---

## How to resume (next session)

```bash
cd /Users/kiritoscs/Desktop/jinx
python3 -m venv .venv && source .venv/bin/activate   # if needed
pip install -e ".[dev]"
pytest -q
jinx --version   # expect 0.3.0

# demo walkthrough (sources are unmarked in git)
jinx -c demo_django_project/jinx.toml marker -t demo_django_project --dry-run
jinx status -t demo_django_project -l demo_django_project/locale
```

---

## Suggested next work (not started)

Priority ideas left on the table:

1. **Push / open PR** to `origin` (14 commits)
2. **PyPI real publish** — configure Trusted Publishing env `pypi` on GitHub, cut GitHub Release `v0.3.0`
3. **Django runserver e2e** — install Django, LocaleMiddleware, switch language, prove runtime
4. **Auto ngettext rewrite** — currently only *hints* + snippet (safe); auto rewrite is risky
5. **% style** gettext: `_("…%(name)s") % {"name": name}` as third `fstring_style`
6. **blocktrans with filters / nested tags** — templates still heuristic
7. **JS/TS** — out of scope unless requested

---

## Hard constraints to remember

1. Prefer **AST** for modifying existing `.py` in this repo (user requirement)
2. Demo shop under `demo_django_project/` should stay **unmarked** in git for reproducible demos
3. Do not commit secrets; Google scrape is still not a production API
4. `name = "张三"` is intentionally **skipped** by heuristics — don’t “fix” without config flag

---

## Key files map

| Path | Role |
|------|------|
| `jinx/marker/marker.py` | Core AST collect + span write + parallel tool |
| `jinx/marker/fstring.py` | f-string → gettext.format |
| `jinx/marker/import_merge.py` | Merge translation imports |
| `jinx/marker/skip.py` | False-positive skips |
| `jinx/marker/template_marker.py` | HTML trans/blocktrans |
| `jinx/marker/plural_hints.py` | ngettext heuristics |
| `jinx/cli.py` | All CLI entrypoints |
| `jinx/commands/init_cmd.py` / `status_cmd.py` | init/status |
| `demo_django_project/` | E2E demo |
| `docs/PROGRESS.md` | **This file** |
