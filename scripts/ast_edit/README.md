# AST edit scripts

When changing existing Python sources in this repository, prefer transformers under this directory (or ad-hoc `ast.parse` / `NodeTransformer` / `ast.unparse` scripts) instead of regex or textual search-replace on `.py` files.

New modules may be written directly; surgical edits to existing modules should go through AST.
