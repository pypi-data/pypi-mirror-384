# Django Prune Media

A Django app that provides management commands for pruning unused media files.

[![PyPI](https://img.shields.io/pypi/v/django-prune-media)](https://pypi.org/project/django-prune-media/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/django-prune-media)
![PyPI - Versions from Framework Classifiers](https://img.shields.io/pypi/frameworkversions/django/django-prune-media)
[![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/andrlik/django-prune-media/blob/main/.pre-commit-config.yaml)
[![License](https://img.shields.io/pypi/l/django-prune-media)](https://codeberg.org/andrlik/django-prune-media/src/branch/main/LICENSE)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Security: bandit](https://img.shields.io/badge/security-bandit-green.svg)](https://github.com/PyCQA/bandit)
[![Checked with pyright](https://microsoft.github.io/pyright/img/pyright_badge.svg)](https://microsoft.github.io/pyright/)
[![Semantic Versions](https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--versions-e10079.svg)](https://github.com/andrlik/django-prune-media/releases)
![Test results](https://ci.codeberg.org/api/badges/15172/status.svg?branch=main)
[![Coverage Status](https://coveralls.io/repos/github/andrlik/django-prune-media/badge.svg?branch=main)](https://coveralls.io/github/andrlik/django-prune-media?branch=main)
[![Documentation](https://app.readthedocs.org/projects/django-prune-media/badge/?version=latest)](https://django-prune-media.readthedocs.io/en/latest/)

## Installation

```bash
uv add django-prune-media
```

Add it to your settings.py.

```python
INSTALLED_APPS = [..., "prune_media", ...]
```

!!! warning

    This application assumes you are not using the same storage for your static and media files.
    It will look at whatever storage you have configured for `default`. If you are commingling them,
    i.e. not using a separate "staticfiles" entry in STORAGES, this can result in false positives.

Usage:

To list or delete the media to be pruned:

```bash
$ python manage.py prune_media --help
```
<!-- [[[cog
import subprocess
import cog

list = subprocess.run(["just", "manage", "prune_media", "--help"], stdout=subprocess.PIPE)
cog.out(
    f"```\n{list.stdout.decode('utf-8')}```"
)
]]] -->
```
                                                                                
 Usage: django-admin prune_media [OPTIONS]                                      
                                                                                
 Remove unreferenced media files to save space.                                 
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --no-interaction    --no-no-interaction      Don't ask for confirmation      │
│                                              before deleting.                │
│                                              [default: no-no-interaction]    │
│ --dry-run           --no-dry-run             Do a dry-run without deleting   │
│                                              anything.                       │
│                                              [default: no-dry-run]           │
│ --help                                       Show this message and exit.     │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Django ─────────────────────────────────────────────────────────────────────╮
│ --version                  Show program's version number and exit.           │
│ --settings           TEXT  The Python path to a settings module, e.g.        │
│                            "myproject.settings.main". If this isn't          │
│                            provided, the DJANGO_SETTINGS_MODULE environment  │
│                            variable will be used.                            │
│ --pythonpath         PATH  A directory to add to the Python path, e.g.       │
│                            "/home/djangoprojects/myproject".                 │
│                            [default: None]                                   │
│ --traceback                Raise on CommandError exceptions                  │
│ --no-color                 Don't colorize the command output.                │
│ --force-color              Force colorization of the command output.         │
│ --skip-checks              Skip system checks.                               │
╰──────────────────────────────────────────────────────────────────────────────╯

```
<!-- [[[end]]] -->

Or to find empty directories:

```bash
$ python manage.py show_empty_media_dirs --help
```
<!-- [[[cog
import subprocess
import cog

list = subprocess.run(["just", "manage", "show_empty_media_dirs", "--help"], stdout=subprocess.PIPE)
cog.out(
    f"```\n{list.stdout.decode('utf-8')}```"
)
]]] -->
```
                                                                                
 Usage: django-admin show_empty_media_dirs [OPTIONS]                            
                                                                                
 List empty media directories for review or to pipe to another command.         
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --clean    --no-clean      Print paths only so they can be piped to other    │
│                            commands                                          │
│                            [default: no-clean]                               │
│ --help                     Show this message and exit.                       │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Django ─────────────────────────────────────────────────────────────────────╮
│ --version                  Show program's version number and exit.           │
│ --settings           TEXT  The Python path to a settings module, e.g.        │
│                            "myproject.settings.main". If this isn't          │
│                            provided, the DJANGO_SETTINGS_MODULE environment  │
│                            variable will be used.                            │
│ --pythonpath         PATH  A directory to add to the Python path, e.g.       │
│                            "/home/djangoprojects/myproject".                 │
│                            [default: None]                                   │
│ --traceback                Raise on CommandError exceptions                  │
│ --no-color                 Don't colorize the command output.                │
│ --force-color              Force colorization of the command output.         │
│ --skip-checks              Skip system checks.                               │
╰──────────────────────────────────────────────────────────────────────────────╯

```
<!-- [[[end]]] -->

## FAQ

### Why another app for this?

Most of the apps I've found operate from the assumption that you are using Django's FileSystemStorage
which is often not the case in production. If you're hosting your media files via object storage at a CDN, `os.walk` is not going to work for you.

This application solely uses the Django [Storage API](https://docs.djangoproject.com/en/5.1/ref/files/storage/#the-storage-class), which means
it works for custom backends like Django Storages too.

### What are the limitations?

Django's Storage API doesn't support deleting anything other than files, so you can end up with empty directories. This is why the `show_empty_media_dirs` command exists. When using the `--clean` option you can pipe the results to a command that's appropriate to your setup.

### Should I use this?

🤷‍♂️

I made this because I didn't want to keep copying this between projects. I want to make it as useful as possible though so contributions, even if it's only a failing test case for me to fix, are very welcome!
