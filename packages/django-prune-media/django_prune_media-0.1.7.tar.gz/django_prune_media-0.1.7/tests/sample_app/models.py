# models.py
#
# Copyright (c) 2024 Daniel Andrlik
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from django.db import models


def upload_file_path(instance, filename):
    """Generate the file path."""
    name_slug = instance.name.replace(" ", "-").lower()
    return f"{name_slug}_{instance.id}/docs/{filename}"


def upload_image_path(instance, filename):
    """Generate the image path."""
    name_slug = instance.name.replace(" ", "-").lower()
    return f"{name_slug}_{instance.id}/img/{filename}"


class Record(models.Model):
    """Basic model for testing purposes"""

    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to=upload_image_path, null=True, blank=True)
    document = models.FileField(upload_to=upload_file_path, null=True, blank=True)

    def __str__(self):  # no cov
        return self.name
