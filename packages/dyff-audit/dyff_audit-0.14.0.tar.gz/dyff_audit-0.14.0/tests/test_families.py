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

# ----------------------------------------------------------------------------
# Families


def test_families_create(pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx):
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()
    if pytestconfig.getoption("skip_families"):
        pytest.skip()
    assert isinstance(dyffapi, Client)

    account = ctx["account"]
    family = dyffapi.families.create(
        FamilyCreateRequest(
            account=account,
            memberKind=FamilyMemberKind.Dataset,
        )
    )
    print(f"family: {family.id}")
    ctx["family"] = family

    wait_for_success(
        lambda: dyffapi.families.get(family.id),
        timeout=timedelta(minutes=2),
    )


@pytest.mark.depends(
    on=[
        "test_families_create",
    ]
)
def test_families_edit_documentation(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx
):
    if pytestconfig.getoption("skip_families"):
        pytest.skip()
    assert isinstance(dyffapi, Client)

    family: Family = ctx["family"]
    print(f"family: {family.id}")
    dyffapi.families.edit_documentation(
        family.id,
        DocumentationEditRequest(
            documentation=commands.EditEntityDocumentationPatch(
                title="EditedTitle",
                summary="EditedSummary",
                fullPage="EditedFullPage",
            ),
        ),
    )

    time.sleep(10)
    family = dyffapi.families.get(family.id)
    assert family.metadata.documentation.title == "EditedTitle"
    assert family.metadata.documentation.summary == "EditedSummary"
    assert family.metadata.documentation.fullPage == "EditedFullPage"


@pytest.mark.depends(
    on=[
        "test_families_create",
    ]
)
def test_families_publish(pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx):
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()
    if pytestconfig.getoption("skip_families"):
        pytest.skip()
    assert isinstance(dyffapi, Client)

    family: Family = ctx["family"]
    print(f"family: {family.id}")
    dyffapi.families.publish(family.id, "preview")

    time.sleep(10)
    labels = dyffapi.families.get(family.id).labels
    assert labels["dyff.io/access"] == "internal"


@pytest.mark.depends(
    on=[
        "test_families_create",
        "test_datasets_create",
        "test_datasets_create_tiny",
    ]
)
def test_families_edit_members(pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx):
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()
    if pytestconfig.getoption("skip_families"):
        pytest.skip()
    assert isinstance(dyffapi, Client)

    family: Family = ctx["family"]
    dataset: Dataset = ctx["dataset"]
    dataset_tiny: Dataset = ctx["dataset_tiny"]

    print(f"family: {family.id}")
    dyffapi.families.edit_members(
        family.id,
        {
            "regular": FamilyMemberBase(
                entity=EntityIdentifier.of(dataset), description="Regular size"
            ),
            "tiny": FamilyMemberBase(
                entity=EntityIdentifier.of(dataset_tiny), description="Tiny size"
            ),
        },
    )

    time.sleep(10)
    family_edited = dyffapi.families.get(family.id)
    ctx["family_edited"] = family_edited
    assert family_edited.members["regular"] == FamilyMember(
        entity=EntityIdentifier.of(dataset),
        description="Regular size",
        name="regular",
        family=family.id,
        creationTime=family_edited.members["regular"].creationTime,
    )
    assert family_edited.members["tiny"] == FamilyMember(
        entity=EntityIdentifier.of(dataset_tiny),
        description="Tiny size",
        name="tiny",
        family=family.id,
        creationTime=family_edited.members["tiny"].creationTime,
    )


@pytest.mark.depends(
    on=[
        "test_families_edit_members",
    ]
)
def test_families_delete_members(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx
):
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()
    if pytestconfig.getoption("skip_families"):
        pytest.skip()
    assert isinstance(dyffapi, Client)

    family_edited: Family = ctx["family_edited"]

    print(f"family_edited: {family_edited.id}")
    dyffapi.families.edit_members(
        family_edited.id,
        {
            "regular": None,
        },
    )

    time.sleep(10)
    family_deleted = dyffapi.families.get(family_edited.id)
    assert "regular" not in family_deleted.members
    assert family_deleted.members["tiny"] == family_edited.members["tiny"]
