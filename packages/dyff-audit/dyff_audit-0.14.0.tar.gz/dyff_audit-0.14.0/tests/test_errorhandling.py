# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

# mypy: disable-error-code="import-untyped"
from datetime import datetime, timedelta, timezone

import pydantic
import pytest
from conftest import (
    DATA_DIR,
    _create_client,
    wait_for_success,
    wait_for_terminal_status,
)

from dyff.audit.local.platform import DyffLocalPlatform
from dyff.client import Client, Timeout
from dyff.schema.base import int32
from dyff.schema.dataset import ReplicatedItem, arrow
from dyff.schema.platform import *
from dyff.schema.requests import *


class BlurstCountScoredItem(ReplicatedItem):
    blurstCount: int32() = pydantic.Field(  # type: ignore
        description="Number of times the word 'blurst' is used in the response."
    )
    cromulent: int32() = pydantic.Field(  # type: ignore
        description="Whether the text is cromulent."
    )
    embiggen: str = pydantic.Field(description="Which man to embiggen.")


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "tests/test_models.py::test_models_create_mock",
    ]
)
def test_inferenceservices_create_mock_transient_errors(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()
    if pytestconfig.getoption("skip_errors"):
        pytest.skip()
    assert isinstance(dyffapi, Client)

    account = ctx["account"]
    model: Model = ctx["model_mock"]

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
            endpoint="openai/v1/completions/transient-errors",
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
    print(f"inferenceservice_mock_transient_errors: {inferenceservice.id}")
    ctx["inferenceservice_mock_transient_errors"] = inferenceservice

    wait_for_success(
        lambda: dyffapi.inferenceservices.get(inferenceservice.id),
        timeout=timedelta(minutes=2),
    )


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "tests/test_datasets.py::test_datasets_create_tiny",
        "tests/test_inference.py::test_inferenceservices_create_mock_transient_errors",
    ]
)
def test_evaluations_create_transient_errors(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    account = ctx["account"]
    dataset = ctx["dataset_tiny"]

    inferenceservice = ctx["inferenceservice_mock_transient_errors"]
    evaluation_request = EvaluationCreateRequest(
        account=account,
        dataset=dataset.id,
        inferenceSession=EvaluationInferenceSessionRequest(
            inferenceService=inferenceservice.id,
            expires=datetime.now(timezone.utc) + timedelta(days=1),
            replicas=1,
            useSpotPods=False,
        ),
        # Extra replications to make sure we get some failures
        replications=10,
        workersPerReplica=10,
    )
    evaluation = dyffapi.evaluations.create(evaluation_request)
    print(f"evaluation_transient_errors: {evaluation.id}")
    ctx["evaluation_transient_errors"] = evaluation

    wait_for_success(
        lambda: dyffapi.evaluations.get(evaluation.id),
        timeout=timedelta(minutes=5),
    )


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "tests/test_models.py::test_models_create_mock",
    ]
)
def test_inferenceservices_create_mock_errors_400(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()
    if pytestconfig.getoption("skip_errors"):
        pytest.skip()
    assert isinstance(dyffapi, Client)

    account = ctx["account"]
    model: Model = ctx["model_mock"]

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
            # Always raise a BadRequest
            endpoint="errors/400",
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
    print(f"inferenceservice_mock_errors_400: {inferenceservice.id}")
    ctx["inferenceservice_mock_errors_400"] = inferenceservice

    wait_for_success(
        lambda: dyffapi.inferenceservices.get(inferenceservice.id),
        timeout=timedelta(minutes=2),
    )


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "tests/test_datasets.py::test_datasets_create_tiny",
        "tests/test_inference.py::test_inferenceservices_create_mock_errors_400",
    ]
)
def test_evaluations_create_errors_400(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    account = ctx["account"]
    dataset = ctx["dataset_tiny"]

    inferenceservice = ctx["inferenceservice_mock_errors_400"]
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
    print(f"evaluation_errors_400: {evaluation.id}")
    ctx["evaluation_errors_400"] = evaluation

    terminal_status = wait_for_terminal_status(
        lambda: dyffapi.evaluations.get(evaluation.id),
        timeout=timedelta(minutes=2),
    )

    # Expected to raise exception -> failure status
    assert is_status_failure(terminal_status)


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "tests/test_datasets.py::test_datasets_create_tiny",
        "tests/test_inference.py::test_inferenceservices_create_mock_errors_400",
    ]
)
def test_evaluations_create_errors_400_skip(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    account = ctx["account"]
    dataset = ctx["dataset_tiny"]

    inferenceservice = ctx["inferenceservice_mock_errors_400"]
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
        client=EvaluationClientConfiguration(
            badRequestPolicy="Skip",
        ),
    )
    evaluation = dyffapi.evaluations.create(evaluation_request)
    print(f"evaluation_errors_400_skip: {evaluation.id}")
    ctx["evaluation_errors_400_skip"] = evaluation

    wait_for_success(
        lambda: dyffapi.evaluations.get(evaluation.id),
        timeout=timedelta(minutes=2),
    )


@pytest.mark.depends(
    on=[
        "tests/test_analysis.py::test_modules_create_python_function",
    ]
)
def test_methods_python_function_raises_error(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx
):
    """Create a Method backed by a Python function that deliberately raises an error."""
    if pytestconfig.getoption("skip_errors"):
        pytest.skip()
    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()

    account = ctx["account"]
    module_python_function = ctx["module_python_function"]
    method_python_function_request = MethodCreateRequest(
        account=account,
        modules=[module_python_function.id],
        name="method_python_function",
        scope=MethodScope.Evaluation,
        description="""# Method that deliberately raises an error""",
        implementation=MethodImplementation(
            kind=MethodImplementationKind.PythonFunction,
            pythonFunction=MethodImplementationPythonFunction(
                fullyQualifiedName="dyff.fake.method.raise_error",
            ),
        ),
        parameters=[
            MethodParameter(keyword="embiggen", description="Who is being embiggened")
        ],
        inputs=[
            MethodInput(kind=MethodInputKind.Dataset, keyword="dataset"),
            MethodInput(kind=MethodInputKind.Evaluation, keyword="outputs"),
        ],
        output=MethodOutput(
            kind=MethodOutputKind.Measurement,
            measurement=MeasurementSpec(
                name="example.dyff.io/blurst-count",
                description="The number of times the word 'blurst' appears in the text.",
                level=MeasurementLevel.Instance,
                schema=DataSchema(
                    arrowSchema=arrow.encode_schema(
                        arrow.arrow_schema(BlurstCountScoredItem)
                    )
                ),
            ),
        ),
    )
    method_python_function_raises_error = dyffapi.methods.create(
        method_python_function_request
    )
    print(
        f"method_python_function_raises_error: {method_python_function_raises_error.id}"
    )
    ctx["method_python_function_raises_error"] = method_python_function_raises_error

    wait_for_success(
        lambda: dyffapi.methods.get(method_python_function_raises_error.id),
        timeout=timedelta(minutes=2),
    )


@pytest.mark.depends(
    on=[
        "tests/test_datasets.py::test_datasets_create",
        "tests/test_evaluation.py::test_evaluations_create",
        "tests/test_errorhandling.py::test_methods_python_function_raises_error",
    ]
)
def test_measurements_python_function_raises_error(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx
):
    """Run a Measurement that calls a Python function that deliberately raises an
    error."""
    if pytestconfig.getoption("skip_errors"):
        pytest.skip()
    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()

    account = ctx["account"]
    evaluation = ctx["evaluation"]
    inferenceservice = ctx["inferenceservice_mock"]
    model = ctx["model_mock"]
    dataset = ctx["dataset"]
    method_python_function_raises_error = ctx["method_python_function_raises_error"]
    measurement_python_function_request = AnalysisCreateRequest(
        account=account,
        method=method_python_function_raises_error.id,
        scope=AnalysisScope(
            evaluation=evaluation.id,
            dataset=dataset.id,
            inferenceService=inferenceservice.id,
            model=(model and model.id),
        ),
        arguments=[
            AnalysisArgument(keyword="embiggen", value="smallest"),
        ],
        inputs=[
            AnalysisInput(keyword="dataset", entity=dataset.id),
            AnalysisInput(keyword="outputs", entity=evaluation.id),
        ],
    )
    measurement_python_function_raises_error = dyffapi.measurements.create(
        measurement_python_function_request
    )
    print(
        f"measurement_python_function_raises_error: {measurement_python_function_raises_error.id}"
    )
    ctx["measurement_python_function_raises_error"] = (
        measurement_python_function_raises_error
    )

    terminal_status = wait_for_terminal_status(
        lambda: dyffapi.measurements.get(measurement_python_function_raises_error.id),
        timeout=timedelta(minutes=5),
    )

    # Expected to raise exception -> failure status
    assert is_status_failure(terminal_status)


@pytest.mark.depends(
    on=[
        "tests/test_errorhandling.py::test_measurements_python_function_raises_error",
    ]
)
def test_measurements_error_log(pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx):
    """Test that the logs from a Measurement that raised an error are present and
    contain the expected error information."""
    if pytestconfig.getoption("skip_errors"):
        pytest.skip()
    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()

    expected_logs = {
        "stdout message": False,
        "stderr message": False,
        "RuntimeError: deliberate error": False,
        "Traceback": False,
    }
    if isinstance(dyffapi, DyffLocalPlatform):
        # TODO: LocalPlatform hasn't implemented .logs() yet
        pytest.skip()
    measurement = ctx["measurement_python_function_raises_error"]
    logs = list(dyffapi.measurements.logs(measurement.id))
    for line in logs:
        for k in expected_logs:
            if k in line:
                expected_logs[k] = True
    missing = [k for k, v in expected_logs.items() if not v]
    assert missing == []


@pytest.mark.depends(
    on=[
        "tests/test_datasets.py::test_datasets_create",
        "tests/test_evaluation.py::test_evaluations_create",
        "tests/test_analysis.py::test_modules_create_python_rubric",
    ]
)
def test_reports_rubric_raises_error(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx
):
    """Run a Report that calls a Python function that deliberately raises an error."""

    if pytestconfig.getoption("skip_errors"):
        pytest.skip()
    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()

    account = ctx["account"]
    evaluation = ctx["evaluation"]
    module = ctx["module_python_rubric"]
    report_request = ReportCreateRequest(
        account=account,
        rubric="dyff.fake.rubric.RaiseError",
        evaluation=evaluation.id,
        modules=[module.id],
    )
    report = dyffapi.reports.create(report_request)
    print(f"report_rubric_raises_error: {report.id}")
    ctx["report_rubric_raises_error"] = report

    terminal_status = wait_for_terminal_status(
        lambda: dyffapi.reports.get(report.id),
        timeout=timedelta(minutes=5),
    )

    # Expected to raise exception -> failure status
    assert is_status_failure(terminal_status)


@pytest.mark.depends(
    on=[
        "tests/test_errorhandling.py::test_reports_rubric_raises_error",
    ]
)
def test_reports_error_log(pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx):
    """Test that the logs from a Report that raised an error are present and contain the
    expected error information."""
    if pytestconfig.getoption("skip_errors"):
        pytest.skip()
    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()

    expected_logs = {
        "stdout message": False,
        "stderr message": False,
        "RuntimeError: deliberate error": False,
        "Traceback": False,
    }
    if isinstance(dyffapi, DyffLocalPlatform):
        # TODO: LocalPlatform hasn't implemented .logs() yet
        pytest.skip()
    report = ctx["report_rubric_raises_error"]
    logs = list(dyffapi.reports.logs(report.id))
    for line in logs:
        for k in expected_logs:
            if k in line:
                expected_logs[k] = True
    missing = [k for k, v in expected_logs.items() if not v]
    assert missing == []


@pytest.mark.datafiles(DATA_DIR)
def test_client_impossible_timeout(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if pytestconfig.getoption("skip_errors"):
        pytest.skip()
    if not pytestconfig.getoption("enable_flaky"):
        pytest.skip()
    if isinstance(dyffapi, DyffLocalPlatform):
        pytest.skip()

    import httpx

    timeout_client = _create_client(pytestconfig, timeout=Timeout(5.0, write=0.0001))

    account = ctx["account"]
    dataset_dir = datafiles / "dataset"
    dataset = timeout_client.datasets.create_arrow_dataset(
        dataset_dir, account=account, name="dataset"
    )
    with pytest.raises(httpx.WriteTimeout):
        timeout_client.datasets.upload_arrow_dataset(dataset, dataset_dir)


@pytest.mark.depends(
    on=[
        "tests/test_analysis.py::test_modules_create_jupyter_notebook",
    ]
)
def test_methods_create_jupyter_notebook_raises_error(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx
):
    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()
    if pytestconfig.getoption("skip_errors"):
        pytest.skip()

    account = ctx["account"]
    module_jupyter_notebook = ctx["module_jupyter_notebook"]
    method_jupyter_notebook_request = MethodCreateRequest(
        name="method_notebook",
        scope=MethodScope.InferenceService,
        description="""# Markdown Description""",
        implementation=MethodImplementation(
            kind=MethodImplementationKind.JupyterNotebook,
            jupyterNotebook=MethodImplementationJupyterNotebook(
                notebookModule=module_jupyter_notebook.id,
                notebookPath="test-notebook-raises-error.ipynb",
            ),
        ),
        parameters=[MethodParameter(keyword="trueName", description="His real name")],
        output=MethodOutput(
            kind=MethodOutputKind.SafetyCase,
            safetyCase=SafetyCaseSpec(
                name="safetycase_notebook",
                description="""# Markdown Description""",
            ),
        ),
        scores=[
            ScoreSpec(
                name="int",
                title="Integer",
                summary="An Integer score",
                valence="positive",
            ),
        ],
        modules=[module_jupyter_notebook.id],
        account=account,
    )
    method_jupyter_notebook = dyffapi.methods.create(method_jupyter_notebook_request)
    print(f"method_jupyter_notebook_raises_error: {method_jupyter_notebook.id}")
    ctx["method_jupyter_notebook_raises_error"] = method_jupyter_notebook

    wait_for_success(
        lambda: dyffapi.methods.get(method_jupyter_notebook.id),
        timeout=timedelta(minutes=2),
    )


@pytest.mark.depends(
    on=[
        "tests/test_errorhandling.py::test_methods_create_jupyter_notebook_raises_error",
    ]
)
def test_safetycase_raises_error(
    pytestconfig,
    dyffapi: Client | DyffLocalPlatform,
    ctx,
):
    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()
    if pytestconfig.getoption("skip_errors"):
        pytest.skip()

    account = ctx["account"]
    inferenceservice = ctx["inferenceservice_mock"]
    model = ctx["model_mock"]
    method_jupyter_notebook = ctx["method_jupyter_notebook_raises_error"]

    # SafetyCase for JupyterNotebook
    safetycase_jupyter_notebook_request = AnalysisCreateRequest(
        account=account,
        method=method_jupyter_notebook.id,
        scope=AnalysisScope(
            evaluation=None,
            dataset=None,
            inferenceService=inferenceservice.id,
            model=(model and model.id),
        ),
        arguments=[
            AnalysisArgument(keyword="trueName", value="Hans Sprungfeld"),
        ],
    )
    safetycase_jupyter_notebook = dyffapi.safetycases.create(
        safetycase_jupyter_notebook_request
    )
    print(f"safetycase_jupyter_notebook_raises_error: {safetycase_jupyter_notebook.id}")
    ctx["safetycase_jupyter_notebook_raises_error"] = safetycase_jupyter_notebook

    terminal_status = wait_for_terminal_status(
        lambda: dyffapi.safetycases.get(safetycase_jupyter_notebook.id),
        timeout=timedelta(minutes=5),
    )

    # Expected to raise exception -> failure status
    assert is_status_failure(terminal_status)
