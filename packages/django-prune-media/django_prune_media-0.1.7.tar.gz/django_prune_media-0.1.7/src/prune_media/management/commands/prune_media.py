# prune_media.py
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
from rich.progress import Progress

from prune_media.utils import get_unreferenced_media_paths

app = Typer()


@app.command(help=_("Remove unreferenced media files to save space."))
def prune_media(
    self,
    no_interaction: Annotated[  # noqa: FBT002
        bool,
        typer.Option(
            help=_("Don't ask for confirmation before deleting."), is_flag=True
        ),
    ] = False,
    dry_run: Annotated[  # noqa: FBT002
        bool,
        typer.Option(help=_("Do a dry-run without deleting anything."), is_flag=True),
    ] = False,
) -> None:
    """Remove unreferenced media files to save space.

    Args:
        no_interaction (bool): Do not prompt the user for confirmation before proceeding
            to deletion.
        dry_run (bool): Don't delete anything, just display what would be done.

    """
    file_paths = get_unreferenced_media_paths()
    if len(file_paths) == 0:
        self.secho(_("No unreferenced media files found! :-)"), fg=typer.colors.GREEN)
        raise typer.Exit()
    for file_path in file_paths:
        self.secho(file_path)
    self.echo("")
    if dry_run:
        self.secho(
            _(f"This would delete {len(file_paths)} unreferenced media files."),
            fg=typer.colors.GREEN,
        )
        raise typer.Exit()
    if not no_interaction:  # no cov, pytest refuses to let me test this
        confirm = typer.confirm(
            typer.style(
                _(
                    f"Are you sure you want to delete these {len(file_paths)} "
                    "unreferenced media files?"
                ),
                fg=typer.colors.YELLOW,
            )
        )
        if not confirm:
            self.secho(_("Aborting!"), fg=typer.colors.RED)
            raise typer.Exit()
    total_deleted = 0
    with Progress() as progress:
        deletion_task = progress.add_task(
            "[red]Deleting unreferenced media files...", total=len(file_paths)
        )
        for file_path in file_paths:
            try:
                self.secho(f"Deleting {file_path}...")
                default_storage.delete(file_path)
                total_deleted += 1
            except Exception as err:  # no cov
                self.secho(
                    _(
                        f"""Could not delete {file_path}!
                    """
                        f"""Exception details: {err}"""
                    ),
                    err=True,
                )
            progress.update(deletion_task, advance=1)
        progress.update(deletion_task, completed=len(file_paths))
    self.secho(
        _(f"Deleted {total_deleted} unreferenced media files."), fg=typer.colors.GREEN
    )
