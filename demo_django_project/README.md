# Demo Django shop (for jinx walkthrough)

Minimal Django-style app with Chinese UI strings. Used to exercise jinx end-to-end.

```bash
# from repo root, with jinx installed
pip install -e .

jinx -c demo_django_project/jinx.toml marker -t demo_django_project
jinx -c demo_django_project/jinx.toml extractor -t demo_django_project -l demo_django_project/locale
jinx -c demo_django_project/jinx.toml translator -p demo_django_project/locale \
  -o demo_django_project/official_dict.json -m full_match
jinx -c demo_django_project/jinx.toml exporter -l demo_django_project/locale -e demo_django_project/contents.json
jinx -c demo_django_project/jinx.toml compiler -l demo_django_project/locale
```

Notes:

- `admin.py` contains an f-string with Chinese text; marker reports it and does not auto-wrap it.
- `urls.py` / `settings.py` / `manage.py` are excluded by `jinx.toml`.
