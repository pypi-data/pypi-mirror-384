# utils.py
#
# Copyright (c) 2024 Daniel Andrlik
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from dataclasses import dataclass

from django.apps import apps
from django.core.files.storage import Storage, default_storage
from django.db.models import FileField


@dataclass
class FieldListing:
    """Represents a given model field within the Django project.

    Attributes:
        app_label (str): The app label the field belongs to.
        model_name (str): The model label that the field belongs to.
        field_name (str): The field name.
    """

    app_label: str
    model_name: str
    field_name: str


@dataclass
class DirectoryTree:
    """This dataclass is used as Storage backends in Django are not
    guaranteed to support os.walk type functionality.

    Attributes:
        path (str): The relative path of the directory as a string.
        files (str): A list of filenames contained in the directory.
        children (list[DirectoryTree]): A list of DirectoryTree objects representing
            child directories.
    """

    path: str
    files: list[str]
    children: list["DirectoryTree"]

    def add_child(self, child_name: str, storage: Storage = default_storage) -> None:
        """Adds a child directory to the tree and recursively adds its children.

        Args:
            child_name (str): The name of the child directory.
            storage (Storage): The storage instance to use.
        """
        child_path = (
            f"{self.path}/{child_name}" if self.path not in ["", "/"] else child_name
        )
        child = DirectoryTree(path=child_path, files=[], children=[])
        directories, files = storage.listdir(child_path)
        child.files = files
        for directory in directories:
            child.add_child(directory, storage=storage)
        self.children.append(child)

    def get_file_paths(self) -> list[str]:
        """
        Get a list of all file paths within the tree

        Returns:
            list of file paths as strings
        """
        file_paths = [
            f"{self.path}/{file}" if file != "" else file for file in self.files
        ]
        for child in self.children:
            file_paths += child.get_file_paths()
        return file_paths

    def get_empty_child_directories(self) -> list[str]:
        """
        Get a list of empty child directories within the tree.

        Returns:
            list of empty child directory paths as strings
        """
        if len(self.children) == 0:
            return []
        empty_directories = []
        for child in self.children:
            if not child.files and not child.children:
                empty_directories.append(child.path)
            else:
                empty_directories += child.get_empty_child_directories()
        return empty_directories


def get_all_file_fields() -> list[FieldListing]:
    """
    Get all fields in the project where a field is an instance or
    subclass of django.db.models.FileField.

    Returns:
        list of fields as tuples with "app_label",
            "model_name", "field_name"
    """
    file_fields = []
    for app, model_dict in apps.all_models.items():
        if model_dict:
            for model_name, model in model_dict.items():
                for field in model._meta.fields:
                    if isinstance(field, FileField):
                        file_fields.append(
                            FieldListing(
                                app_label=app,
                                model_name=model_name,
                                field_name=field.name,
                            )
                        )
    return file_fields


def get_referenced_file_paths(fields: list[FieldListing]) -> list[str]:
    """
    Get a list of all file paths from the supplied field data.

    Args:
        fields (list[tuple[str, str, str]]): list of fields as tuples with "app_label",
             "model_name", "field_name"

    Returns:
        list of file paths as strings
    """
    filepaths = []
    for model_spec in fields:
        model = apps.get_model(
            app_label=model_spec.app_label, model_name=model_spec.model_name
        )
        filepaths += model.objects.filter(
            **{f"{model_spec.field_name}__isnull": False}
        ).values_list(model_spec.field_name, flat=True)
    return filepaths


def get_media_paths(storage_backend: Storage = default_storage) -> list[str]:
    """
    Get a list of all media files found in the supplied storage instance.

    Args:
        storage_backend (Storage): a Django Storage instance

    Returns:
        list of media file paths as strings
    """
    dirs, files = storage_backend.listdir(".")
    dir_tree = DirectoryTree(path="", files=files, children=[])
    for directory in dirs:
        dir_tree.add_child(directory, storage=storage_backend)
    return dir_tree.get_file_paths()


def get_unreferenced_media_paths(
    storage_backend: Storage = default_storage,
) -> list[str]:
    """Get a list of media files that are not referenced by Django FileFields

    Args:
        storage_backend (Storage): a Django Storage instance

    Returns:
        list of media file paths as strings

    """
    media_paths = get_media_paths(storage_backend=storage_backend)
    return [
        path
        for path in media_paths
        if path not in get_referenced_file_paths(get_all_file_fields())
    ]


def get_empty_media_directories(
    storage_backend: Storage = default_storage,
) -> list[str]:
    """Get a list of empty media directories found in the supplied storage instance.

    Args:
        storage_backend (Storage): a Django Storage instance

    Returns:
        list of empty media directory paths as strings
    """
    dirs, files = storage_backend.listdir(".")
    dir_tree = DirectoryTree(path="", files=files, children=[])
    for directory in dirs:
        dir_tree.add_child(directory, storage=storage_backend)
    return dir_tree.get_empty_child_directories()
