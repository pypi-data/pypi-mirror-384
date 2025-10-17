# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

# mypy: disable-error-code="import-untyped"
from datetime import timedelta

import pytest
from conftest import (
    COMPARISON_REPLICATIONS,
    DATA_DIR,
    assert_documentation_exist,
    edit_documentation_and_assert,
    wait_for_success,
)

from dyff.audit.local.platform import DyffLocalPlatform
from dyff.client import Client
from dyff.schema.platform import *
from dyff.schema.requests import *


@pytest.mark.datafiles(DATA_DIR)
def test_models_create_mock(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if pytestconfig.getoption("skip_inference_mocks"):
        pytest.skip()

    account = ctx["account"]
    model_request = ModelCreateRequest(
        name="mock-model",
        account=account,
        artifact=ModelArtifact(
            kind=ModelArtifactKind.Mock,
        ),
        storage=ModelStorage(
            medium=ModelStorageMedium.Mock,
        ),
        source=ModelSource(
            kind=ModelSourceKinds.Mock,
        ),
        resources=ModelResources(storage="0"),
    )
    model = dyffapi.models.create(model_request)
    print(f"model: {model.id}")
    ctx["model_mock"] = model

    wait_for_success(
        lambda: dyffapi.models.get(model.id),
        timeout=timedelta(minutes=2),
    )


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.parametrize("replication", range(COMPARISON_REPLICATIONS))
def test_models_create_mock_compare(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles, replication
):
    if pytestconfig.getoption("skip_inference_mocks"):
        pytest.skip()
    if not pytestconfig.getoption("enable_comparisons"):
        pytest.skip()

    account = ctx["account"]
    model_request = ModelCreateRequest(
        name=f"mock-model-compare-{replication}",
        account=account,
        artifact=ModelArtifact(
            kind=ModelArtifactKind.Mock,
        ),
        storage=ModelStorage(
            medium=ModelStorageMedium.Mock,
        ),
        source=ModelSource(
            kind=ModelSourceKinds.Mock,
        ),
        resources=ModelResources(storage="0"),
    )
    model = dyffapi.models.create(model_request)
    print(f"model compare {replication}: {model.id}")
    ctx[f"model_mock_compare_{replication}"] = model

    wait_for_success(
        lambda: dyffapi.models.get(model.id),
        timeout=timedelta(minutes=2),
    )


@pytest.mark.datafiles(DATA_DIR)
def test_models_create_huggingface(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if pytestconfig.getoption("skip_huggingface"):
        pytest.skip()
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()

    account = ctx["account"]
    model_request = ModelCreateRequest(
        name="facebook/opt-125m",
        account=account,
        artifact=ModelArtifact(
            kind=ModelArtifactKind.HuggingFaceCache,
            huggingFaceCache=ModelArtifactHuggingFaceCache(
                repoID="facebook/opt-125m",
                revision="27dcfa74d334bc871f3234de431e71c6eeba5dd6",  # pragma: allowlist secret
            ),
        ),
        source=ModelSource(
            kind=ModelSourceKinds.HuggingFaceHub,
            huggingFaceHub=ModelSourceHuggingFaceHub(
                repoID="facebook/opt-125m",
                revision="27dcfa74d334bc871f3234de431e71c6eeba5dd6",  # pragma: allowlist secret
                # Repos sometimes contain multiple copies of the weights in
                # different formats; we want just the regular PyTorch .bin weights
                allowPatterns=[
                    ".gitattributes",
                    "pytorch_model*.bin",
                    "*.json",
                    "*.md",
                    "*.model",
                    "*.py",
                    "*.txt",
                ],
                # Ignore everything in subdirectories
                ignorePatterns=["*/*"],
            ),
        ),
        storage=ModelStorage(
            medium=ModelStorageMedium.ObjectStorage,
        ),
        resources=ModelResources(
            storage="300Mi",
            memory="8Gi",
        ),
    )
    model = dyffapi.models.create(model_request)
    print(f"model_huggingface: {model.id}")
    ctx["model_huggingface"] = model

    wait_for_success(
        lambda: dyffapi.models.get(model.id),
        timeout=timedelta(minutes=5),
    )


@pytest.mark.datafiles(DATA_DIR)
def test_models_create_huggingface_with_fuse(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if not pytestconfig.getoption("enable_fuse"):
        pytest.skip()
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()

    account = ctx["account"]
    model_request = ModelCreateRequest(
        name="facebook/opt-125m",
        account=account,
        artifact=ModelArtifact(
            kind=ModelArtifactKind.HuggingFaceCache,
            huggingFaceCache=ModelArtifactHuggingFaceCache(
                repoID="facebook/opt-125m",
                revision="27dcfa74d334bc871f3234de431e71c6eeba5dd6",  # pragma: allowlist secret
            ),
        ),
        source=ModelSource(
            kind=ModelSourceKinds.HuggingFaceHub,
            huggingFaceHub=ModelSourceHuggingFaceHub(
                repoID="facebook/opt-125m",
                revision="27dcfa74d334bc871f3234de431e71c6eeba5dd6",  # pragma: allowlist secret
                # Repos sometimes contain multiple copies of the weights in
                # different formats; we want just the regular PyTorch .bin weights
                allowPatterns=[
                    ".gitattributes",
                    "pytorch_model*.bin",
                    "*.json",
                    "*.md",
                    "*.model",
                    "*.py",
                    "*.txt",
                ],
                # Ignore everything in subdirectories
                ignorePatterns=["*/*"],
            ),
        ),
        storage=ModelStorage(
            medium=ModelStorageMedium.FUSEVolume,
        ),
        resources=ModelResources(
            storage="300Mi",
            memory="8Gi",
        ),
    )
    model = dyffapi.models.create(model_request)
    print(f"model_huggingface_with_fuse: {model.id}")
    ctx["model_huggingface_with_fuse"] = model

    wait_for_success(
        lambda: dyffapi.models.get(model.id),
        timeout=timedelta(minutes=5),
    )


@pytest.mark.datafiles(DATA_DIR)
def test_models_create_upload(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if isinstance(dyffapi, DyffLocalPlatform):
        pytest.skip()

    account = ctx["account"]
    model_dir = datafiles / "model"

    model = dyffapi.models.create_from_volume(
        model_dir, name="model_volume", account=account, resources=ModelResources()
    )
    print(f"model_volume: {model.id}")
    dyffapi.models.upload_volume(model, model_dir)
    ctx["model_volume"] = model

    wait_for_success(
        lambda: dyffapi.models.get(model.id),
        timeout=timedelta(minutes=2),
    )


@pytest.mark.depends(
    on=[
        "test_models_create_mock",
    ]
)
def test_models_documentation(pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx):
    if pytestconfig.getoption("skip_documentation"):
        pytest.skip("skip_documentation config should be disabled")

    model = ctx["model_mock"]
    assert_documentation_exist(dyffapi.models.documentation, model.id)


@pytest.mark.depends(
    on=[
        "test_models_create_mock",
    ]
)
def test_models_edit_documentation(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx
):
    if pytestconfig.getoption("skip_documentation"):
        pytest.skip("skip_documentation config should be disabled")

    model = ctx["model_mock"]
    edit_documentation_and_assert(
        dyffapi.models.edit_documentation,
        model.id,
        tile="EditedTitle",
        summary="EditedSummary",
        fullpage="EditedFullPage",
    )
