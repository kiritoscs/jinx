# Jinx Modernization Design

**Date:** 2026-08-07  
**Scope:** Full-stack quality upgrade of the Django i18n CLI tool  
**Package layout:** `jinx.*`  
**Commits:** One feature per commit  
**Python edit rule:** All in-repo Python modifications use AST transforms (no regex-based rewrites of `.py`)

## Goals

1. Installable package with `jinx` console entry
2. Lazy, safe configuration loading
3. stdlib `Enum` instead of hand-rolled enums
4. Correct PO write modes and literal msgid handling
5. Shared PO path resolution
6. Marker rewritten with AST for correctness
7. Hardened translators (timeouts, errors)
8. Real unit tests + modern CI
9. Updated README and config template

## Non-goals

- New translation providers
- Runtime Django integration
- Replacing click with another CLI framework

## Architecture

```
jinx/
  cli.py                 # click group
  common/                # config, constants, po, prompt, utils, path
  marker/                # AST-based FileMarker + filters
  extractor/
  translator/provider/
  exporter/
  compiler/
```

CLI sets `CONFIG_PATH` / loads config lazily; tools never require import-time side effects beyond package import.

## Marker (AST)

- Parse file with `ast.parse`
- `NodeTransformer` wraps bare string constants that match language + conditions
- Skip strings already inside known translation calls
- Detect f-strings (`JoinedStr`) containing target language → illegal; strict mode skips file
- Ensure `from django.utils.translation import X as _` via AST import nodes
- Write with `ast.unparse` (+ trailing newline)

## Verification

- `pip install -e .` → `jinx --help`
- pytest for config, po, marker, cli
- CI on Python 3.11+
