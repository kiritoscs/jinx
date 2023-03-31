from setuptools import setup

with open('README.md', encoding='utf-8') as readme_file:
    readme = readme_file.read()

# 依赖
requirements = [
    "arrow >= 1.2.2",
    "click >= 8.1.3",
    "polib >= 1.2.0",
    "requests >= 2.28.2",
    "rich >= 13.3.2",
    "json5 >= 0.9.11",
]

setup(
    name='jinx',
    version='1.0.0',
    description="A full-stack i18n solution for Django",
    long_description=readme,
    author="kiritoscs",
    author_email="kiritoscs@gmail.com",
    install_requires=requirements,
    license="MIT license",
    python_required=">=3.11",
    packages=['jinx'],
    py_modules=['jinx'],
    package_dir={'jinx': 'jinx'},
    entry_points={'console_scripts': ['jinx = jinx.cli:cli']},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords=[
        "django",
        "i18n",
        "internationalization",
        "translation",
        "localization",
        "l10n",
        "django-i18n",
        "django-internationalization",
        "django-translation",
        "django-localization",
        "django-l10n",
    ],
)
