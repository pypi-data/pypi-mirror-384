# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import time

# mypy: disable-error-code="import-untyped"
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from conftest import COMPARISON_REPLICATIONS, DATA_DIR, wait_for_ready, wait_for_success

from dyff.audit.local import mocks
from dyff.audit.local.platform import DyffLocalPlatform
from dyff.client import Client
from dyff.schema import commands
from dyff.schema.platform import *
from dyff.schema.requests import *


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "tests/test_models.py::test_models_create_mock",
    ]
)
def test_inferenceservices_create_mock(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    account = ctx["account"]
    model: Model = ctx["model_mock"]

    if pytestconfig.getoption("test_remote"):
        assert isinstance(dyffapi, Client)

        service_request = InferenceServiceCreateRequest(
            account=account,
            name="mock-llm",
            model=model.id,
            runner=InferenceServiceRunner(
                kind=InferenceServiceRunnerKind.MOCK,
                resources=ModelResources(
                    storage="1Gi",
                    memory="2Gi",
                ),
                image=ContainerImageSource(
                    host="registry.gitlab.com",
                    name="dyff/workflows/inferenceservice-mock",
                    digest="sha256:f7becd37affa559a60e7ef2d3a0b1e4766e6cd6438cef701d58d2653767e7e54",
                    tag="0.2.1",
                ),
            ),
            interface=InferenceInterface(
                # This is the inference endpoint for the vLLM runner
                endpoint="openai/v1/completions",
                # The output records should look like: {"text": "To be, or not to be"}
                outputSchema=DataSchema.make_output_schema(
                    DyffDataSchema(
                        components=["text.Text"],
                    ),
                ),
                # How to convert the input dataset into the format the runner expects
                inputPipeline=[
                    # {"text": "The question"} -> {"prompt": "The question"}
                    SchemaAdapter(
                        kind="TransformJSON",
                        configuration={"prompt": "$.text", "model": model.id},
                    ),
                ],
                # How to convert the runner output to match outputSchema
                outputPipeline=[
                    SchemaAdapter(
                        kind="ExplodeCollections",
                        configuration={"collections": ["choices"]},
                    ),
                    SchemaAdapter(
                        kind="TransformJSON",
                        configuration={"text": "$.choices.text"},
                    ),
                ],
            ),
        )

        inferenceservice = dyffapi.inferenceservices.create(service_request)
        print(f"inferenceservice_mock: {inferenceservice.id}")
        ctx["inferenceservice_mock"] = inferenceservice
    else:
        assert isinstance(dyffapi, DyffLocalPlatform)

        inferenceservice = dyffapi.inferenceservices.create_mock(
            mocks.TextCompletion,
            account=account,
            model=model.id,
        )
        print(f"inferenceservice_mock: {inferenceservice.id}")
        ctx["inferenceservice_mock"] = inferenceservice

    wait_for_success(
        lambda: dyffapi.inferenceservices.get(inferenceservice.id),
        timeout=timedelta(minutes=2),
    )


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "tests/test_inference.py::test_inferenceservices_create_mock",
    ]
)
def test_edit_documentation(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if pytestconfig.getoption("skip_documentation"):
        pytest.skip()

    inferenceservice: InferenceService = ctx["inferenceservice_mock"]

    dyffapi.inferenceservices.edit_documentation(
        inferenceservice.id,
        DocumentationEditRequest(
            documentation=commands.EditEntityDocumentationPatch(
                title="Mock Svc", summary="Main Mock Svc"
            )
        ),
    )

    time.sleep(10)
    documentation = dyffapi.inferenceservices.documentation(inferenceservice.id)
    assert documentation.title == "Mock Svc"
    assert documentation.summary == "Main Mock Svc"
    assert documentation.fullPage is None


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "tests/test_models.py::test_models_create_mock_compare",
    ]
)
@pytest.mark.parametrize("replication", range(COMPARISON_REPLICATIONS))
def test_inferenceservices_create_mock_compare(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles, replication
):
    if not pytestconfig.getoption("enable_comparisons"):
        pytest.skip()

    account = ctx["account"]
    model: Model = ctx[f"model_mock_compare_{replication}"]

    if pytestconfig.getoption("test_remote"):
        assert isinstance(dyffapi, Client)

        service_request = InferenceServiceCreateRequest(
            account=account,
            name=f"mock-llm-svc-compare-{replication}",
            model=model.id,
            runner=InferenceServiceRunner(
                kind=InferenceServiceRunnerKind.MOCK,
                resources=ModelResources(
                    storage="1Gi",
                    memory="2Gi",
                ),
            ),
            interface=InferenceInterface(
                # This is the inference endpoint for the vLLM runner
                endpoint="generate",
                # The output records should look like: {"text": "To be, or not to be"}
                outputSchema=DataSchema.make_output_schema(
                    DyffDataSchema(
                        components=["text.Text"],
                    ),
                ),
                # How to convert the input dataset into the format the runner expects
                inputPipeline=[
                    # {"text": "The question"} -> {"prompt": "The question"}
                    SchemaAdapter(
                        kind="TransformJSON",
                        configuration={"prompt": "$.text"},
                    ),
                ],
                # How to convert the runner output to match outputSchema
                outputPipeline=[
                    # {"text": ["The answer"]} -> [{"text": "The answer"}]
                    SchemaAdapter(
                        kind="ExplodeCollections",
                        configuration={"collections": ["text"]},
                    ),
                ],
            ),
        )

        inferenceservice = dyffapi.inferenceservices.create(service_request)
        print(f"inferenceservice_mock_compare_{replication}: {inferenceservice.id}")
        ctx[f"inferenceservice_mock_compare_{replication}"] = inferenceservice
    else:
        assert isinstance(dyffapi, DyffLocalPlatform)

        inferenceservice = dyffapi.inferenceservices.create_mock(
            mocks.TextCompletion,
            account=account,
            model=model.id,
        )
        print(f"inferenceservice_mock_{replication}: {inferenceservice.id}")
        ctx[f"inferenceservice_mock_{replication}"] = inferenceservice

    wait_for_success(
        lambda: dyffapi.inferenceservices.get(inferenceservice.id),
        timeout=timedelta(minutes=2),
    )


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "tests/test_models.py::test_models_create_upload",
        "tests/test_artifacts.py::test_artifacts_finalize",
    ]
)
def test_inferenceservices_create_container(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()
    assert isinstance(dyffapi, Client)

    account = ctx["account"]
    model: Model = ctx["model_volume"]
    artifact: OCIArtifact = ctx["artifact"]

    service_request = InferenceServiceCreateRequest(
        account=account,
        name=model.name,
        model=model.id,
        runner=InferenceServiceRunner(
            kind=InferenceServiceRunnerKind.CONTAINER,
            imageRef=EntityIdentifier.of(artifact),
            # FIXME: .storage is necessary because we're not calculating size
            # based on the individual File objects in the volumes.
            resources=ModelResources(storage="10Mi"),
            volumeMounts=[
                VolumeMount(
                    kind=VolumeMountKind.data,
                    name="model",
                    mountPath=Path("/dyff/mnt/volume"),
                    data=VolumeMountData(
                        source=EntityIdentifier.of(model),
                    ),
                ),
            ],
        ),
        interface=InferenceInterface(
            # This is the inference endpoint for the vLLM runner
            endpoint="v1/completions",
            # The output records should look like: {"text": "To be, or not to be"}
            outputSchema=DataSchema.make_output_schema(
                DyffDataSchema(
                    components=["text.Text"],
                ),
            ),
            # How to convert the input dataset into the format the runner expects
            inputPipeline=[
                # {"text": "The question"} -> {"prompt": "The question"}
                SchemaAdapter(
                    kind="TransformJSON",
                    configuration={"prompt": "$.text", "model": model.id},
                ),
            ],
            # How to convert the runner output to match outputSchema
            outputPipeline=[
                SchemaAdapter(
                    kind="ExplodeCollections",
                    configuration={"collections": ["choices"]},
                ),
                SchemaAdapter(
                    kind="TransformJSON",
                    configuration={"text": "$.choices.text"},
                ),
            ],
        ),
    )

    inferenceservice = dyffapi.inferenceservices.create(service_request)
    print(f"inferenceservice_container: {inferenceservice.id}")
    ctx["inferenceservice_container"] = inferenceservice

    wait_for_success(
        lambda: dyffapi.inferenceservices.get(inferenceservice.id),
        timeout=timedelta(minutes=2),
    )


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "tests/test_models.py::test_models_create_huggingface",
    ]
)
def test_inferenceservices_create_huggingface(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if pytestconfig.getoption("skip_huggingface"):
        pytest.skip()
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()

    account = ctx["account"]
    model: Model = ctx["model_huggingface"]

    assert isinstance(dyffapi, Client)

    service_request = InferenceServiceCreateRequest(
        account=account,
        name=model.name,
        model=model.id,
        runner=InferenceServiceRunner(
            kind=InferenceServiceRunnerKind.HUGGINGFACE,
            image=ContainerImageSource(
                host="registry.gitlab.com",
                name="dyff/workflows/huggingface-runner",
                digest="sha256:2d200fa3f56f8b0e902b9d2c079e1d73528a42f7f668883d8f56e4fe585a845f",
                tag="0.1.3",
            ),
            resources=ModelResources(
                storage="1Gi",
                memory="2Gi",
            ),
        ),
        interface=InferenceInterface(
            # This is the inference endpoint for the vLLM runner
            endpoint="generate",
            # The output records should look like: {"text": "To be, or not to be"}
            outputSchema=DataSchema.make_output_schema(
                DyffDataSchema(
                    components=["text.Text"],
                ),
            ),
            # How to convert the input dataset into the format the runner expects
            inputPipeline=[
                # {"text": "The question"} -> {"prompt": "The question"}
                SchemaAdapter(
                    kind="TransformJSON",
                    configuration={
                        "prompt": "$.text",
                        # When using HuggingFace runner, max_tokens counts the
                        # length of the input, too, so we need to override
                        # the default.
                        "max_new_tokens": 20,
                    },
                ),
            ],
            # How to convert the runner output to match outputSchema
            outputPipeline=[
                # {"text": ["The answer"]} -> [{"text": "The answer"}]
                SchemaAdapter(
                    kind="ExplodeCollections",
                    configuration={"collections": ["text"]},
                ),
            ],
        ),
    )

    inferenceservice = dyffapi.inferenceservices.create(service_request)
    print(f"inferenceservice_huggingface: {inferenceservice.id}")
    ctx["inferenceservice_huggingface"] = inferenceservice

    wait_for_success(
        lambda: dyffapi.inferenceservices.get(inferenceservice.id),
        timeout=timedelta(minutes=2),
    )


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "tests/test_models.py::test_models_create_huggingface",
    ]
)
def test_inferenceservices_create_vllm(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if not pytestconfig.getoption("enable_vllm"):
        pytest.skip()
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()

    account = ctx["account"]
    model: Model = ctx["model_huggingface"]

    assert isinstance(dyffapi, Client)

    service_request = InferenceServiceCreateRequest(
        account=account,
        name=model.name,
        model=model.id,
        runner=InferenceServiceRunner(
            kind=InferenceServiceRunnerKind.VLLM,
            image=ContainerImageSource(
                host="registry.gitlab.com",
                name="dyff/workflows/vllm-runner",
                digest="sha256:18607d33c6f4bb6bdb3da1b63d34cc4001526ddd2a9e467ced730e0761749c51",
                tag="0.7.0",
            ),
            # T4 GPUs don't support bfloat format, so force standard float format
            args=[
                "--served-model-name",
                model.id,
                model.name,
                "--dtype",
                "float16",
            ],
            accelerator=Accelerator(
                kind="GPU",
                gpu=AcceleratorGPU(
                    hardwareTypes=["nvidia.com/gpu-t4"],
                    memory="300Mi",
                    count=1,
                ),
            ),
            resources=ModelResources(
                storage="1Gi",
                # vLLM requires lot of memory, even for small models
                memory="8Gi",
            ),
        ),
        interface=InferenceInterface(
            # This is the inference endpoint for the vLLM runner
            endpoint="v1/completions",
            # The output records should look like: {"text": "To be, or not to be"}
            outputSchema=DataSchema.make_output_schema(
                DyffDataSchema(
                    components=["text.Text"],
                ),
            ),
            # How to convert the input dataset into the format the runner expects
            inputPipeline=[
                # {"text": "The question"} -> {"prompt": "The question"}
                SchemaAdapter(
                    kind="TransformJSON",
                    configuration={"prompt": "$.text", "model": model.id},
                ),
            ],
            # How to convert the runner output to match outputSchema
            outputPipeline=[
                SchemaAdapter(
                    kind="ExplodeCollections",
                    configuration={"collections": ["choices"]},
                ),
                SchemaAdapter(
                    kind="TransformJSON",
                    configuration={"text": "$.choices.text"},
                ),
            ],
        ),
    )

    inferenceservice = dyffapi.inferenceservices.create(service_request)
    print(f"inferenceservice_vllm: {inferenceservice.id}")
    ctx["inferenceservice_vllm"] = inferenceservice

    wait_for_success(
        lambda: dyffapi.inferenceservices.get(inferenceservice.id),
        timeout=timedelta(minutes=2),
    )


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "tests/test_models.py::test_models_create_huggingface_with_fuse",
    ]
)
def test_inferenceservices_create_vllm_multinode(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if not pytestconfig.getoption("enable_vllm_multinode"):
        pytest.skip()
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()

    account = ctx["account"]
    model: Model = ctx["model_huggingface_with_fuse"]

    assert isinstance(dyffapi, Client)

    # Multi-node config
    nodes = 2
    service_request = InferenceServiceCreateRequest(
        account=account,
        name=model.name,
        model=model.id,
        runner=InferenceServiceRunner(
            kind=InferenceServiceRunnerKind.VLLM,
            image=ContainerImageSource(
                host="registry.gitlab.com",
                name="dyff/workflows/vllm-runner",
                digest="sha256:18607d33c6f4bb6bdb3da1b63d34cc4001526ddd2a9e467ced730e0761749c51",
                tag="0.7.0",
            ),
            args=[
                "--served-model-name",
                model.id,
                model.name,
                # T4 GPUs don't support bfloat format, so force standard float format
                "--dtype",
                "float16",
                # Multi-node config
                "--pipeline-parallel-size",
                str(nodes),
            ],
            accelerator=Accelerator(
                kind="GPU",
                gpu=AcceleratorGPU(
                    hardwareTypes=["nvidia.com/gpu-t4"],
                    memory="300Mi",
                    count=1,
                ),
            ),
            resources=ModelResources(
                storage="1Gi",
                # vLLM requires lot of memory, even for small models
                memory="8Gi",
            ),
            # Multi-node config
            nodes=nodes,
        ),
        interface=InferenceInterface(
            # This is the inference endpoint for the vLLM runner
            endpoint="v1/completions",
            # The output records should look like: {"text": "To be, or not to be"}
            outputSchema=DataSchema.make_output_schema(
                DyffDataSchema(
                    components=["text.Text"],
                ),
            ),
            # How to convert the input dataset into the format the runner expects
            inputPipeline=[
                # {"text": "The question"} -> {"prompt": "The question"}
                SchemaAdapter(
                    kind="TransformJSON",
                    configuration={"prompt": "$.text", "model": model.id},
                ),
            ],
            # How to convert the runner output to match outputSchema
            outputPipeline=[
                SchemaAdapter(
                    kind="ExplodeCollections",
                    configuration={"collections": ["choices"]},
                ),
                SchemaAdapter(
                    kind="TransformJSON",
                    configuration={"text": "$.choices.text"},
                ),
            ],
        ),
    )

    inferenceservice = dyffapi.inferenceservices.create(service_request)
    print(f"inferenceservice_vllm_multinode: {inferenceservice.id}")
    ctx["inferenceservice_vllm_multinode"] = inferenceservice

    wait_for_success(
        lambda: dyffapi.inferenceservices.get(inferenceservice.id),
        timeout=timedelta(minutes=2),
    )


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "tests/test_inference.py::test_inferenceservices_create_mock",
    ]
)
def test_inferencesessions_create_mock(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    account = ctx["account"]
    service: InferenceService = ctx["inferenceservice_mock"]

    session_request = InferenceSessionCreateRequest(
        account=account,
        inferenceService=service.id,
        useSpotPods=False,
        accelerator=service.runner.accelerator if service.runner else None,
    )
    session_and_token = dyffapi.inferencesessions.create(session_request)
    session = session_and_token.inferencesession

    print(f"inferencesession_mock: {session.id}")
    ctx["inferencesession_mock"] = session
    ctx["session_token_mock"] = session_and_token.token

    wait_for_ready(dyffapi, session.id, timeout=timedelta(minutes=5))


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "tests/test_inference.py::test_inferencesessions_create_mock",
    ]
)
def test_inferencesessions_infer_mock(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    session: InferenceSession = ctx["inferencesession_mock"]

    if pytestconfig.getoption("test_remote"):
        assert isinstance(dyffapi, Client)
        session_client = dyffapi.inferencesessions.client(
            session.id,
            ctx["session_token_mock"],
            interface=session.inferenceService.interface,
        )
        response = session_client.infer({"text": "Open the pod bay doors, Hal!"})
    else:
        assert isinstance(dyffapi, DyffLocalPlatform)
        response = dyffapi.inferencesessions.infer(
            session.id, "generate", {"text": "Open the pod bay doors, Hal!"}
        )
    print(f"infer_mock: {response}")


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "tests/test_inference.py::test_inferencesessions_create_mock",
    ]
)
def test_inferencesessions_infer_with_created_token(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    session: InferenceSession = ctx["inferencesession_mock"]
    token = dyffapi.inferencesessions.token(
        session.id, expires=datetime.now(timezone.utc) + timedelta(minutes=5)
    )

    if pytestconfig.getoption("test_remote"):
        assert isinstance(dyffapi, Client)
        session_client = dyffapi.inferencesessions.client(
            session.id,
            token,
            interface=session.inferenceService.interface,
        )
        response = session_client.infer({"text": "Open the pod bay doors, Hal!"})
    else:
        assert isinstance(dyffapi, DyffLocalPlatform)
        response = dyffapi.inferencesessions.infer(
            session.id, "generate", {"text": "Open the pod bay doors, Hal!"}
        )
    print(f"infer_with_created_token: {response}")


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "tests/test_inference.py::test_inferenceservices_create_huggingface",
    ]
)
def test_inferencesessions_create_huggingface(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if pytestconfig.getoption("skip_huggingface"):
        pytest.skip()

    account = ctx["account"]
    service: InferenceService = ctx["inferenceservice_huggingface"]

    session_request = InferenceSessionCreateRequest(
        account=account,
        inferenceService=service.id,
        useSpotPods=False,
        accelerator=service.runner.accelerator if service.runner else None,
    )
    session_and_token = dyffapi.inferencesessions.create(session_request)
    session = session_and_token.inferencesession

    print(f"inferencesession_huggingface: {session.id}")
    ctx["inferencesession_huggingface"] = session
    ctx["session_token_huggingface"] = session_and_token.token

    wait_for_ready(dyffapi, session.id, timeout=timedelta(minutes=10))


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "tests/test_inference.py::test_inferencesessions_create_huggingface",
    ]
)
def test_inferencesessions_infer_huggingface(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if pytestconfig.getoption("skip_huggingface"):
        pytest.skip()

    session: InferenceSession = ctx["inferencesession_huggingface"]

    if pytestconfig.getoption("test_remote"):
        assert isinstance(dyffapi, Client)
        session_client = dyffapi.inferencesessions.client(
            session.id,
            ctx["session_token_huggingface"],
            interface=session.inferenceService.interface,
        )
        response = session_client.infer({"text": "Open the pod bay doors, Hal!"})
    else:
        assert isinstance(dyffapi, DyffLocalPlatform)
        response = dyffapi.inferencesessions.infer(
            session.id, "generate", {"text": "Open the pod bay doors, Hal!"}
        )
    print(f"infer_huggingface: {response}")
