# show_empty_media_dirs.py
#
# Copyright (c) 2024 - 2025 Daniel Andrlik
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from typing import Annotated

import typer
from django.core.files.storage import default_storage
from django.utils.translation import gettext_lazy as _
from django_typer.management import Typer

from prune_media.utils import get_empty_media_directories

app = Typer()


@app.command(help=_(
    "List empty media directories for review or to pipe to another command."
))
def show_empty_media_dirs(
    self,
    clean: Annotated[  # noqa: FBT002
        bool,
        typer.Option(
            help=_("Print paths only so they can be piped to other commands"),
            is_flag=True,
        ),
    ] = False,
) -> None:
    """List empty media directories.

    The storage API does not support deletion of directories but at least this
    way you know what can be removed.

    Args:
        clean (bool): Display the list of empty media directories with no formatting or
            additional text so that it can be piped to another command.
    """
    empty_dirs = get_empty_media_directories(storage_backend=default_storage)
    if not empty_dirs:
        if not clean:
            self.echo(_("No empty media directories."))
        raise typer.Exit()
    for empty_dir in empty_dirs:
        self.echo(empty_dir)
    if not clean:
        self.echo(_(f"Found {len(empty_dirs)} empty media directories."))
