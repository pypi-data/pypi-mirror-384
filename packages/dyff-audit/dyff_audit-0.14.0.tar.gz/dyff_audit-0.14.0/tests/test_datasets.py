# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

# mypy: disable-error-code="import-untyped"
import tempfile
from datetime import timedelta
from pathlib import Path

import pytest
from conftest import (
    DATA_DIR,
    assert_documentation_exist,
    edit_documentation_and_assert,
    wait_for_success,
)

from dyff.audit.local.platform import Dataset, DyffLocalPlatform
from dyff.client import Client


@pytest.mark.datafiles(DATA_DIR)
def test_datasets_create(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    account = ctx["account"]
    dataset_dir = datafiles / "dataset"
    dataset = dyffapi.datasets.create_arrow_dataset(
        dataset_dir, account=account, name="dataset"
    )
    dyffapi.datasets.upload_arrow_dataset(dataset, dataset_dir)
    print(f"dataset: {dataset.id}")
    ctx["dataset"] = dataset

    wait_for_success(
        lambda: dyffapi.datasets.get(dataset.id),
        timeout=timedelta(minutes=2),
    )


@pytest.mark.depends(
    on=[
        "test_datasets_create",
    ]
)
def test_dataset_documentation(pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx):
    if pytestconfig.getoption("skip_documentation"):
        pytest.skip("skip_documentation config should be disabled")

    dataset = ctx["dataset"]
    assert_documentation_exist(dyffapi.datasets.documentation, dataset.id)


@pytest.mark.depends(
    on=[
        "test_datasets_create",
    ]
)
def test_dataset_edit_documentation(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx
):
    if pytestconfig.getoption("skip_documentation"):
        pytest.skip("skip_documentation config should be disabled")

    dataset = ctx["dataset"]
    edit_documentation_and_assert(
        dyffapi.datasets.edit_documentation,
        dataset.id,
        tile="EditedTitle",
        summary="EditedSummary",
        fullpage="EditedFullPage",
    )


@pytest.mark.datafiles(DATA_DIR)
def test_datasets_create_tiny(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    account = ctx["account"]
    dataset_dir = datafiles / "dataset_tiny"
    dataset = dyffapi.datasets.create_arrow_dataset(
        dataset_dir, account=account, name="dataset_tiny"
    )
    dyffapi.datasets.upload_arrow_dataset(dataset, dataset_dir)
    print(f"dataset_tiny: {dataset.id}")
    ctx["dataset_tiny"] = dataset

    wait_for_success(
        lambda: dyffapi.datasets.get(dataset.id),
        timeout=timedelta(minutes=2),
    )


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "test_datasets_create",
    ]
)
def test_datasets_download(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    dataset: Dataset = ctx["dataset"]

    if not pytestconfig.getoption("test_remote"):
        pytest.skip()

    assert isinstance(dyffapi, Client)

    with tempfile.TemporaryDirectory() as tmp:
        dyffapi.datasets.download(dataset.id, Path(tmp) / "nested" / "dataset")

        with pytest.raises(FileExistsError):
            dyffapi.datasets.download(dataset.id, Path(tmp) / "nested")
