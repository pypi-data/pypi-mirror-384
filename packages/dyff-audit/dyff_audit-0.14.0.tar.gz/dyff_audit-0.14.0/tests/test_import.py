# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

import importlib

import pytest


@pytest.mark.parametrize(
    "module_name",
    [
        "dyff.audit",
        "dyff.audit.analysis",
        "dyff.audit.analysis.context",
        "dyff.audit.analysis.jupyter",
        "dyff.audit.analysis.legacy",
        "dyff.audit.analysis.python",
        "dyff.audit.data",
        "dyff.audit.data.text",
        "dyff.audit.dynamic_import",
        "dyff.audit.local",
        "dyff.audit.local.platform",
        "dyff.audit.metrics.base",
        "dyff.audit.metrics.text",
        "dyff.audit.metrics",
        "dyff.audit.scoring.base",
        "dyff.audit.scoring.example",
        "dyff.audit.scoring.text",
        "dyff.audit.scoring",
        "dyff.audit.scoring.classification",
        "dyff.audit.workflows",
    ],
)
def test_import_module(module_name):
    importlib.import_module(module_name)
