# test_management.py
#
# Copyright (c) 2024 Daniel Andrlik
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from io import StringIO

import pytest
from django.core.files.storage import default_storage
from django.core.management import call_command


def test_prune_media_dry_run(record_with_files):
    output = StringIO()
    call_command("prune_media", dry_run=True, stdout=output)
    assert "This would delete 1 unreferenced media files" in output.getvalue()


def test_prune_media_dry_run_no_files():
    orig_file = StringIO(initial_value="This is a test")
    default_storage.save(name="test.txt", content=orig_file)
    default_storage.delete(name="test.txt")
    output = StringIO()
    call_command("prune_media", dry_run=True, stdout=output)
    assert "No unreferenced media files found!" in output.getvalue()


def test_prune_media(record_with_files):
    output = StringIO()
    image_dir = record_with_files.image.name.rsplit("/", maxsplit=1)[0]
    call_command("prune_media", no_interaction=True, stdout=output)
    assert "Deleted 1 unreferenced media files" in output.getvalue()
    assert not default_storage.exists(f"{image_dir}/extra_art.png")


@pytest.mark.parametrize("use_clean", [True, False])
def test_show_empty_none(record_with_files, use_clean):
    output = StringIO()
    call_command("show_empty_media_dirs", clean=use_clean, stdout=output)
    stdout_text = output.getvalue()
    if not use_clean:
        assert "No empty media directories." in stdout_text
    else:
        assert "No empty media directories." not in stdout_text


@pytest.mark.parametrize("use_clean", [True, False])
def test_show_empty_media_dirs_one(record_with_files, use_clean):
    record_with_files.document.delete()
    record_with_files.save()
    output = StringIO()
    call_command("show_empty_media_dirs", clean=use_clean, stdout=output)
    stdout_text = output.getvalue()
    assert "johnny-one_1/docs" in stdout_text
    if not use_clean:
        assert "Found 1 empty media directories" in stdout_text
    else:
        assert "Found 1 empty media directories" not in stdout_text
