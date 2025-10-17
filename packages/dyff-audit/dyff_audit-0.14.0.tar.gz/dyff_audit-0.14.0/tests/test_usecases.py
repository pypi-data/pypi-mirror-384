# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import time

# mypy: disable-error-code="import-untyped"
from datetime import timedelta

import pytest
from conftest import wait_for_success

from dyff.audit.local.platform import DyffLocalPlatform
from dyff.client import Client
from dyff.schema import commands
from dyff.schema.platform import *
from dyff.schema.requests import *


def test_usecases_create(pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx):
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()
    assert isinstance(dyffapi, Client)

    account = ctx["account"]
    usecase = dyffapi.usecases.create(
        ConcernCreateRequest(
            account=account,
            documentation=DocumentationBase(
                title="Underwater Basket-weaving",
                summary="Using ML to weave baskets while underwater.",
            ),
        )
    )
    print(f"usecase: {usecase.id}")
    ctx["usecase"] = usecase

    wait_for_success(
        lambda: dyffapi.usecases.get(usecase.id),
        timeout=timedelta(minutes=2),
    )


@pytest.mark.depends(
    on=[
        "test_usecases_create",
    ]
)
def test_usecases_edit_documentation(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx
):
    if pytestconfig.getoption("skip_documentation"):
        pytest.skip()
    assert isinstance(dyffapi, Client)

    usecase: UseCase = ctx["usecase"]
    print(f"usecase: {usecase.id}")
    dyffapi.usecases.edit_documentation(
        usecase.id,
        DocumentationEditRequest(
            documentation=commands.EditEntityDocumentationPatch(
                title="EditedTitle",
                summary="EditedSummary",
                fullPage="EditedFullPage",
            ),
        ),
    )

    time.sleep(10)
    usecase = dyffapi.usecases.get(usecase.id)
    assert usecase.metadata.documentation.title == "EditedTitle"
    assert usecase.metadata.documentation.summary == "EditedSummary"
    assert usecase.metadata.documentation.fullPage == "EditedFullPage"


@pytest.mark.depends(
    on=[
        "test_usecases_create",
    ]
)
def test_usecases_publish(pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx):
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()
    assert isinstance(dyffapi, Client)

    usecase: UseCase = ctx["usecase"]
    print(f"usecase: {usecase.id}")
    dyffapi.usecases.publish(usecase.id, "preview")

    time.sleep(10)
    labels = dyffapi.usecases.get(usecase.id).labels
    assert labels["dyff.io/access"] == "internal"


@pytest.mark.depends(
    on=[
        "test_methods_create_jupyter_notebook",
        "test_safetycase_publish",
        "test_usecases_publish",
    ]
)
def test_concerns_add(pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx):
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()
    assert isinstance(dyffapi, Client)

    method_jupyter_notebook: Method = ctx["method_jupyter_notebook"]
    print(f"method_jupyter_notebook: {method_jupyter_notebook.id}")
    usecase: UseCase = ctx["usecase"]
    dyffapi.methods.add_concern(method_jupyter_notebook.id, usecase)

    time.sleep(10)
    labels = dyffapi.methods.get(method_jupyter_notebook.id).labels
    assert usecase.label_key() in labels


@pytest.mark.depends(
    on=[
        "test_concerns_add",
    ]
)
def test_concerns_remove(pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx):
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()
    assert isinstance(dyffapi, Client)

    method_jupyter_notebook: Method = ctx["method_jupyter_notebook"]
    print(f"method_jupyter_notebook: {method_jupyter_notebook.id}")
    usecase: UseCase = ctx["usecase"]
    dyffapi.methods.remove_concern(method_jupyter_notebook.id, usecase)

    time.sleep(10)
    labels = dyffapi.methods.get(method_jupyter_notebook.id).labels
    assert usecase.label_key() not in labels
