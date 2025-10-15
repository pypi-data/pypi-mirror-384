# test_utils.py
#
# Copyright (c) 2024 Daniel Andrlik
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from prune_media.utils import (
    FieldListing,
    get_all_file_fields,
    get_empty_media_directories,
    get_media_paths,
    get_referenced_file_paths,
    get_unreferenced_media_paths,
)


def test_get_all_file_fields():
    fields = get_all_file_fields()
    assert len(fields) == 2
    assert (
        FieldListing(app_label="sample_app", model_name="record", field_name="image")
        in fields
    )
    assert (
        FieldListing(app_label="sample_app", model_name="record", field_name="document")
        in fields
    )


def test_get_referenced_file_paths(record_with_files):
    file_paths = get_referenced_file_paths(get_all_file_fields())
    assert len(file_paths) == 2
    assert record_with_files.image.name in file_paths
    assert record_with_files.document.name in file_paths


def test_get_media_paths(record_with_files):
    file_paths = get_media_paths()
    assert len(file_paths) == 3
    assert record_with_files.image.name in file_paths
    assert record_with_files.document.name in file_paths
    directory = record_with_files.image.name.rsplit("/", maxsplit=1)[0]
    assert f"{directory}/extra_art.png" in file_paths


def test_get_unreferenced_media_paths(record_with_files):
    file_paths = get_unreferenced_media_paths()
    assert len(file_paths) == 1
    directory = record_with_files.image.name.rsplit("/", maxsplit=1)[0]
    assert f"{directory}/extra_art.png" in file_paths


def test_get_empty_media_directories(record_with_files):
    filename = record_with_files.document.name
    directory = filename.rsplit("/", maxsplit=1)[0]
    record_with_files.document.delete()
    record_with_files.save()
    dir_paths = get_empty_media_directories()
    assert len(dir_paths) == 1
    assert directory in dir_paths
