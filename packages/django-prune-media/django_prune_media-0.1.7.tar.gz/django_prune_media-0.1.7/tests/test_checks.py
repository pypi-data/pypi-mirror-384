# test_checks.py
#
# Copyright (c) 2024 Daniel Andrlik
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import SystemCheckError


def test_checks_root_gone(settings):
    settings.MEDIA_ROOT = str(settings.ROOT_DIR / "nowhere")
    output = StringIO()
    with pytest.raises(SystemCheckError):
        call_command("check", stdout=output)
        assert "Your media root does not exist!" in output.getvalue()


def test_checks_incompatible_backend(settings):
    settings.STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.base.Storage",
        }
    }
    with pytest.raises(SystemCheckError):
        output = StringIO()
        call_command("check", stdout=output)
        assert "Your storage backend does not support listdir!" in output.getvalue()
