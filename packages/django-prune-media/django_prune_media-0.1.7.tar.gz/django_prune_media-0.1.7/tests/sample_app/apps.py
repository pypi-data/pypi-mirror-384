# apps.py
#
# Copyright (c) 2024 Daniel Andrlik
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from django.apps import AppConfig


class SampleAppConfig(AppConfig):
    name = "tests.sample_app"
    app_label = "sample_app"
    default_auto_field = "django.db.models.AutoField"
