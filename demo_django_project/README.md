# Demo Django shop (jinx walkthrough)

Minimal Django-style app with Chinese strings in **Python** and **HTML templates**.

```bash
# from repo root
pip install -e .

jinx -c demo_django_project/jinx.toml marker -t demo_django_project
# → wraps _("…"), converts f"中文{x}" → _("中文{}").format(x)
# → wraps template text/attrs with {% trans "…" %}

jinx -c demo_django_project/jinx.toml extractor -t demo_django_project -l demo_django_project/locale
jinx -c demo_django_project/jinx.toml translator -p demo_django_project/locale \
  -o demo_django_project/official_dict.json -m full_match
jinx -c demo_django_project/jinx.toml exporter -l demo_django_project/locale -e demo_django_project/contents.json
jinx -c demo_django_project/jinx.toml compiler -l demo_django_project/locale
```

Sources are kept **unmarked** so you can re-run the pipeline cleanly.
