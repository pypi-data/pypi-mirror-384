# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

# mypy: disable-error-code="import-untyped"
from datetime import datetime, timedelta, timezone

import pytest
from conftest import (
    DATA_DIR,
    download_and_assert,
    wait_for_success,
)

from dyff.audit.local.platform import DyffLocalPlatform
from dyff.client import Client
from dyff.schema.requests import (
    EvaluationCreateRequest,
    EvaluationInferenceSessionRequest,
)


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "tests/test_datasets.py::test_datasets_create",
        "tests/test_inference.py::test_inferenceservices_create_mock",
    ]
)
def test_evaluations_create(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    account = ctx["account"]
    dataset = ctx["dataset"]

    inferenceservice = ctx["inferenceservice_mock"]
    evaluation_request = EvaluationCreateRequest(
        account=account,
        dataset=dataset.id,
        inferenceSession=EvaluationInferenceSessionRequest(
            inferenceService=inferenceservice.id,
            expires=datetime.now(timezone.utc) + timedelta(days=1),
            replicas=1,
            useSpotPods=False,
        ),
        replications=2,
        workersPerReplica=2,
    )
    evaluation = dyffapi.evaluations.create(evaluation_request)
    print(f"evaluation: {evaluation.id}")
    ctx["evaluation"] = evaluation

    wait_for_success(
        lambda: dyffapi.evaluations.get(evaluation.id),
        timeout=timedelta(minutes=10),
    )


@pytest.mark.depends(on=["tests/test_evaluation.py::test_evaluations_create"])
def test_evaluations_download(pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx):
    if not pytestconfig.getoption("test_remote"):
        pytest.skip("evaluation download test requires remote API")

    evaluation = ctx["evaluation"]
    download_and_assert(dyffapi.evaluations.download, evaluation.id, "data/evaluation")


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "tests/test_datasets.py::test_datasets_create_tiny",
        "tests/test_inference.py::test_inferenceservices_create_container",
    ]
)
def test_evaluations_create_container(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    account = ctx["account"]
    dataset = ctx["dataset_tiny"]

    inferenceservice = ctx["inferenceservice_container"]
    evaluation_request = EvaluationCreateRequest(
        account=account,
        dataset=dataset.id,
        inferenceSession=EvaluationInferenceSessionRequest(
            inferenceService=inferenceservice.id,
            expires=datetime.now(timezone.utc) + timedelta(days=1),
            replicas=1,
            useSpotPods=False,
        ),
        replications=2,
        workersPerReplica=2,
    )
    evaluation = dyffapi.evaluations.create(evaluation_request)
    print(f"evaluation_container: {evaluation.id}")
    ctx["evaluation_container"] = evaluation

    wait_for_success(
        lambda: dyffapi.evaluations.get(evaluation.id),
        timeout=timedelta(minutes=10),
    )


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "tests/test_datasets.py::test_datasets_create_tiny",
        "tests/test_inference.py::test_inferenceservices_create_huggingface",
    ]
)
def test_evaluations_create_huggingface(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if pytestconfig.getoption("skip_huggingface"):
        pytest.skip()

    account = ctx["account"]
    dataset = ctx["dataset_tiny"]

    inferenceservice = ctx["inferenceservice_huggingface"]
    evaluation_request = EvaluationCreateRequest(
        account=account,
        dataset=dataset.id,
        inferenceSession=EvaluationInferenceSessionRequest(
            inferenceService=inferenceservice.id,
            expires=datetime.now(timezone.utc) + timedelta(days=1),
            replicas=1,
            useSpotPods=False,
        ),
        replications=2,
        workersPerReplica=2,
    )
    evaluation = dyffapi.evaluations.create(evaluation_request)
    print(f"evaluation_huggingface: {evaluation.id}")
    ctx["evaluation_huggingface"] = evaluation

    wait_for_success(
        lambda: dyffapi.evaluations.get(evaluation.id),
        timeout=timedelta(minutes=10),
    )


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "tests/test_datasets.py::test_datasets_create_tiny",
        "tests/test_inference.py::test_inferenceservices_create_vllm",
    ]
)
def test_evaluations_create_vllm(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if pytestconfig.getoption("skip_huggingface"):
        pytest.skip()
    if not pytestconfig.getoption("enable_vllm"):
        pytest.skip()

    account = ctx["account"]
    dataset = ctx["dataset_tiny"]

    inferenceservice = ctx["inferenceservice_vllm"]
    evaluation_request = EvaluationCreateRequest(
        account=account,
        dataset=dataset.id,
        inferenceSession=EvaluationInferenceSessionRequest(
            inferenceService=inferenceservice.id,
            expires=datetime.now(timezone.utc) + timedelta(days=1),
            replicas=1,
            useSpotPods=False,
        ),
        replications=2,
        workersPerReplica=2,
    )
    evaluation = dyffapi.evaluations.create(evaluation_request)
    print(f"evaluation_vllm: {evaluation.id}")
    ctx["evaluation_vllm"] = evaluation

    wait_for_success(
        lambda: dyffapi.evaluations.get(evaluation.id),
        # It can take a really long time to 1) allocate a GPU node, and then
        # 2) pull the gigantic CUDA-enabled Docker image
        timeout=timedelta(minutes=30),
    )


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "tests/test_datasets.py::test_datasets_create_tiny",
        "tests/test_inference.py::test_inferenceservices_create_vllm_multinode",
    ]
)
def test_evaluations_create_vllm_multinode(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if not pytestconfig.getoption("enable_vllm_multinode"):
        pytest.skip()

    account = ctx["account"]
    dataset = ctx["dataset_tiny"]

    inferenceservice = ctx["inferenceservice_vllm_multinode"]
    evaluation_request = EvaluationCreateRequest(
        account=account,
        dataset=dataset.id,
        inferenceSession=EvaluationInferenceSessionRequest(
            inferenceService=inferenceservice.id,
            expires=datetime.now(timezone.utc) + timedelta(days=1),
            replicas=1,
            useSpotPods=False,
        ),
        replications=2,
        workersPerReplica=2,
    )
    evaluation = dyffapi.evaluations.create(evaluation_request)
    print(f"evaluation_vllm_multinode: {evaluation.id}")
    ctx["evaluation_vllm_multinode"] = evaluation

    wait_for_success(
        lambda: dyffapi.evaluations.get(evaluation.id),
        # It can take a really long time to 1) allocate a GPU node, and then
        # 2) pull the gigantic CUDA-enabled Docker image
        timeout=timedelta(minutes=30),
    )


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "tests/test_datasets.py::test_datasets_create_tiny",
        "tests/test_inference.py::test_inferencesessions_create_mock",
    ]
)
def test_evaluations_create_with_session_reference(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    account = ctx["account"]
    dataset = ctx["dataset_tiny"]
    session = ctx["inferencesession_mock"]

    evaluation_request = EvaluationCreateRequest(
        account=account,
        dataset=dataset.id,
        inferenceSessionReference=session.id,
        replications=2,
        workersPerReplica=2,
    )
    evaluation = dyffapi.evaluations.create(evaluation_request)
    print(f"evaluation_with_session_reference: {evaluation.id}")

    wait_for_success(
        lambda: dyffapi.evaluations.get(evaluation.id),
        timeout=timedelta(minutes=5),
    )


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "tests/test_datasets.py::test_datasets_create",
    ]
)
def test_evaluations_import(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if pytestconfig.getoption("test_remote"):
        pytest.skip()
    assert isinstance(dyffapi, DyffLocalPlatform)

    account = ctx["account"]
    dataset = ctx["dataset"]

    evaluation_request = EvaluationCreateRequest(
        account=account,
        dataset=dataset.id,
        inferenceSession=EvaluationInferenceSessionRequest(inferenceService=""),
    )
    evaluation = dyffapi.evaluations.import_data(
        datafiles / "evaluation", evaluation_request=evaluation_request
    )

    print(f"evaluation_import: {evaluation.id}")
