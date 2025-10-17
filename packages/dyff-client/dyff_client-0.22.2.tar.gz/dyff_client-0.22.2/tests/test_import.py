# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

import importlib

import pytest


@pytest.mark.parametrize(
    "module_name",
    [
        "dyff.client.client",
        "dyff.client",
    ],
)
def test_import_module(module_name):
    importlib.import_module(module_name)
