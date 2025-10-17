# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import time

# mypy: disable-error-code="import-untyped"
from datetime import timedelta

import pydantic
import pytest
from conftest import (
    COMPARISON_REPLICATIONS,
    DATA_DIR,
    assert_documentation_exist,
    download_and_assert,
    edit_documentation_and_assert,
    wait_for_success,
)

from dyff.audit.local.platform import DyffLocalPlatform
from dyff.client import Client
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
def test_modules_create_jupyter_notebook(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()

    account = ctx["account"]
    module_jupyter_notebook_dir = datafiles / "module_jupyter_notebook"
    module_jupyter_notebook = dyffapi.modules.create_package(
        module_jupyter_notebook_dir, account=account, name="module_jupyter_notebook"
    )
    dyffapi.modules.upload_package(module_jupyter_notebook, module_jupyter_notebook_dir)
    print(f"module_jupyter_notebook: {module_jupyter_notebook.id}")
    ctx["module_jupyter_notebook"] = module_jupyter_notebook

    wait_for_success(
        lambda: dyffapi.modules.get(module_jupyter_notebook.id),
        timeout=timedelta(minutes=2),
    )


@pytest.mark.datafiles(DATA_DIR)
def test_modules_create_jupyter_notebook_no_scores(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()

    account = ctx["account"]
    module_jupyter_notebook_dir = datafiles / "module_jupyter_notebook_no_scores"
    module_jupyter_notebook = dyffapi.modules.create_package(
        module_jupyter_notebook_dir,
        account=account,
        name="module_jupyter_notebook_no_scores",
    )
    dyffapi.modules.upload_package(module_jupyter_notebook, module_jupyter_notebook_dir)
    print(f"module_jupyter_notebook_no_scores: {module_jupyter_notebook.id}")
    ctx["module_jupyter_notebook_no_scores"] = module_jupyter_notebook

    wait_for_success(
        lambda: dyffapi.modules.get(module_jupyter_notebook.id),
        timeout=timedelta(minutes=2),
    )


@pytest.mark.datafiles(DATA_DIR)
def test_modules_create_python_function(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()

    account = ctx["account"]
    module_python_function_dir = datafiles / "module_python_function"
    module_python_function = dyffapi.modules.create_package(
        module_python_function_dir, account=account, name="module_python_function"
    )
    dyffapi.modules.upload_package(module_python_function, module_python_function_dir)
    print(f"module_python_function: {module_python_function.id}")
    ctx["module_python_function"] = module_python_function

    wait_for_success(
        lambda: dyffapi.modules.get(module_python_function.id),
        timeout=timedelta(minutes=2),
    )


@pytest.mark.datafiles(DATA_DIR)
def test_modules_create_python_rubric(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()

    account = ctx["account"]
    module_python_rubric_dir = datafiles / "module_python_rubric"
    module_python_rubric = dyffapi.modules.create_package(
        module_python_rubric_dir, account=account, name="module_python_rubric"
    )
    dyffapi.modules.upload_package(module_python_rubric, module_python_rubric_dir)
    print(f"module_python_rubric: {module_python_rubric.id}")
    ctx["module_python_rubric"] = module_python_rubric

    wait_for_success(
        lambda: dyffapi.modules.get(module_python_rubric.id),
        timeout=timedelta(minutes=2),
    )


@pytest.mark.depends(
    on=[
        "tests/test_analysis.py::test_modules_create_jupyter_notebook",
    ]
)
def test_methods_create_jupyter_notebook(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx
):
    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()

    account = ctx["account"]
    module_jupyter_notebook = ctx["module_jupyter_notebook"]
    method_jupyter_notebook_request = MethodCreateRequest(
        name="method_notebook",
        scope=MethodScope.InferenceService,
        description="""*Markdown Description*""",
        implementation=MethodImplementation(
            kind=MethodImplementationKind.JupyterNotebook,
            jupyterNotebook=MethodImplementationJupyterNotebook(
                notebookModule=module_jupyter_notebook.id,
                notebookPath="test-notebook.ipynb",
            ),
        ),
        parameters=[
            MethodParameter(keyword="trueName", description="His real name"),
            MethodParameter(
                keyword="isOutlier",
                description="If this safetycase should be used for outlier value in distribution scores.",
            ),
        ],
        inputs=[
            MethodInput(kind=MethodInputKind.Measurement, keyword="cromulence"),
        ],
        output=MethodOutput(
            kind=MethodOutputKind.SafetyCase,
            safetyCase=SafetyCaseSpec(
                name="safetycase_notebook",
                description="""*Markdown Description*""",
            ),
        ),
        scores=[
            ScoreSpec(
                name="float_unit_primary",
                title="Float (primary; with unit)",
                summary="A float with a unit that is the 'primary' score",
                minimum=0,
                maximum=1,
                unit="MJ/kg",
            ),
            ScoreSpec(
                name="int",
                title="Integer",
                summary="An Integer score",
                valence="positive",
                priority="secondary",
            ),
            ScoreSpec(
                name="int_big",
                title="Integer (Big)",
                summary="A big Integer score",
                valence="positive",
                priority="secondary",
            ),
            ScoreSpec(
                name="int_percent",
                title="Integer (Percentage)",
                summary="A percentage represented as an integer",
                valence="positive",
                priority="secondary",
                minimum=0,
                maximum=100,
            ),
            ScoreSpec(
                name="no_display",
                title="Not displayed",
                summary="A score that should not be displayed",
                valence="negative",
                priority="secondary",
            ),
            ScoreSpec(
                name="exp_rate_low",
                title="Exponential Distribution (Low Rate)",
                summary="An exponential distribution with a low rate, leading to a gradual decay.",
                valence="positive",
                priority="secondary",
                minimum=0.0,
                maximum=10.0,
            ),
            ScoreSpec(
                name="exp_rate_high",
                title="Exponential Distribution (High Rate)",
                summary="An exponential distribution with a high rate, causing rapid decay.",
                valence="positive",
                priority="secondary",
                minimum=0.0,
                maximum=10.0,
            ),
            ScoreSpec(
                name="poisson_rate_low",
                title="Poisson Distribution (Low Rate)",
                summary="A Poisson distribution with a low average event rate, generating fewer events.",
                valence="positive",
                priority="secondary",
                minimum=0,
                maximum=20,
            ),
            ScoreSpec(
                name="poisson_rate_high",
                title="Poisson Distribution (High Rate)",
                summary="A Poisson distribution with a high average event rate, generating more events.",
                valence="positive",
                priority="secondary",
                minimum=0,
                maximum=20,
            ),
            ScoreSpec(
                name="normal_standard",
                title="Normal Distribution (Standard)",
                summary="A normal distribution with a mean of 0 and a standard deviation of 1.",
                valence="positive",
                priority="secondary",
                minimum=-5.0,
                maximum=5.0,
            ),
            ScoreSpec(
                name="normal_shifted",
                title="Normal Distribution (Shifted)",
                summary="A normal distribution with a mean of 5 and a standard deviation of 2.",
                valence="positive",
                priority="secondary",
                minimum=0.0,
                maximum=10.0,
            ),
            ScoreSpec(
                name="bimodal_close",
                title="Bi-Modal Distribution (Close Peaks)",
                summary="A bi-modal distribution with two peaks close to each other, creating moderate separation.",
                valence="positive",
                priority="secondary",
                minimum=-5.0,
                maximum=15.0,
            ),
            ScoreSpec(
                name="bimodal_separated",
                title="Bi-Modal Distribution (Separated Peaks)",
                summary="A bi-modal distribution with two peaks far apart, creating clear separation between clusters.",
                valence="positive",
                priority="secondary",
                minimum=-5.0,
                maximum=20.0,
            ),
            ScoreSpec(
                name="close_together",
                title="Close Values Around 50",
                summary="Values generated close to 50 within an expanded range of ±10.",
                valence="positive",
                priority="secondary",
                minimum=0.0,
                maximum=100.0,
            ),
            ScoreSpec(
                name="in_middle",
                title="Values in the Middle",
                summary="Values generated in the middle of the range, centered around 50.",
                valence="positive",
                priority="secondary",
                minimum=0.0,
                maximum=100.0,
            ),
            ScoreSpec(
                name="near_min",
                title="Values Near Minimum",
                summary="Values generated near the minimum, within the range of 0 to 10.",
                valence="positive",
                priority="secondary",
                minimum=0.0,
                maximum=100.0,
            ),
            ScoreSpec(
                name="near_max",
                title="Values Near Maximum",
                summary="Values generated near the maximum, within the range of 90 to 100.",
                valence="positive",
                priority="secondary",
                minimum=0.0,
                maximum=100.0,
            ),
            ScoreSpec(
                name="extreme_outliers",
                title="Extreme Outliers",
                summary="Extreme outlier values that are far outside the typical range.",
                valence="positive",
                priority="secondary",
                minimum=0.0,
                maximum=100.0,
            ),
            ScoreSpec(
                name="same_values",
                title="All Values Exactly the Same",
                summary="All values are exactly the same, uniform data for testing.",
                valence="positive",
                priority="secondary",
                minimum=0.0,
                maximum=100.0,
            ),
        ],
        modules=[module_jupyter_notebook.id],
        account=account,
    )
    method_jupyter_notebook = dyffapi.methods.create(method_jupyter_notebook_request)
    print(f"method_jupyter_notebook: {method_jupyter_notebook.id}")
    ctx["method_jupyter_notebook"] = method_jupyter_notebook

    wait_for_success(
        lambda: dyffapi.methods.get(method_jupyter_notebook.id),
        timeout=timedelta(minutes=2),
    )


@pytest.mark.depends(
    on=[
        "test_modules_create_jupyter_notebook_no_scores",
    ]
)
def test_methods_create_jupyter_notebook_no_scores(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx
):
    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()

    account = ctx["account"]
    module_jupyter_notebook = ctx["module_jupyter_notebook_no_scores"]
    method_jupyter_notebook_request = MethodCreateRequest(
        name="method_notebook_no_scores",
        scope=MethodScope.InferenceService,
        description="""# Markdown Description""",
        implementation=MethodImplementation(
            kind=MethodImplementationKind.JupyterNotebook,
            jupyterNotebook=MethodImplementationJupyterNotebook(
                notebookModule=module_jupyter_notebook.id,
                notebookPath="test-notebook.ipynb",
            ),
        ),
        parameters=[MethodParameter(keyword="trueName", description="His real name")],
        inputs=[
            MethodInput(kind=MethodInputKind.Measurement, keyword="cromulence"),
        ],
        output=MethodOutput(
            kind=MethodOutputKind.SafetyCase,
            safetyCase=SafetyCaseSpec(
                name="safetycase_notebook_no_scores",
                description="""# Markdown Description""",
            ),
        ),
        modules=[module_jupyter_notebook.id],
        account=account,
    )
    method_jupyter_notebook = dyffapi.methods.create(method_jupyter_notebook_request)
    print(f"method_jupyter_notebook_no_scores: {method_jupyter_notebook.id}")
    ctx["method_jupyter_notebook_no_scores"] = method_jupyter_notebook

    wait_for_success(
        lambda: dyffapi.methods.get(method_jupyter_notebook.id),
        timeout=timedelta(minutes=2),
    )


@pytest.mark.depends(
    on=[
        "test_modules_create_python_function",
    ]
)
def test_methods_create_python_function(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx
):
    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()

    account = ctx["account"]
    module_python_function = ctx["module_python_function"]
    method_python_function_request = MethodCreateRequest(
        account=account,
        modules=[module_python_function.id],
        name="method_python_function",
        scope=MethodScope.Evaluation,
        description="""# Markdown Description""",
        implementation=MethodImplementation(
            kind=MethodImplementationKind.PythonFunction,
            pythonFunction=MethodImplementationPythonFunction(
                fullyQualifiedName="dyff.fake.method.blurst_count",
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
    method_python_function = dyffapi.methods.create(method_python_function_request)
    print(f"method_python_function: {method_python_function.id}")
    ctx["method_python_function"] = method_python_function

    wait_for_success(
        lambda: dyffapi.methods.get(method_python_function.id),
        timeout=timedelta(minutes=2),
    )


@pytest.mark.depends(
    on=[
        "tests/test_datasets.py::test_datasets_create",
        "tests/test_evaluation.py::test_evaluations_create",
        "test_methods_create_python_function",
    ]
)
def test_measurements_create_python_function(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx
):
    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()

    account = ctx["account"]
    evaluation = ctx["evaluation"]
    inferenceservice = ctx["inferenceservice_mock"]
    model = ctx["model_mock"]
    dataset = ctx["dataset"]
    method_python_function = ctx["method_python_function"]
    measurement_python_function_request = AnalysisCreateRequest(
        account=account,
        method=method_python_function.id,
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
    measurement_python_function = dyffapi.measurements.create(
        measurement_python_function_request
    )
    print(f"measurement_python_function: {measurement_python_function.id}")
    ctx["measurement_python_function"] = measurement_python_function

    wait_for_success(
        lambda: dyffapi.measurements.get(measurement_python_function.id),
        timeout=timedelta(minutes=10),
    )


@pytest.mark.depends(
    on=[
        "test_measurements_create_python_function",
    ]
)
def test_measurements_download_python_function(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx
):
    if not pytestconfig.getoption("test_remote"):
        pytest.skip("download test requires remote API")

    measurement_python_function = ctx["measurement_python_function"]
    download_and_assert(
        dyffapi.measurements.download,
        measurement_python_function.id,
        "data/measurement",
    )


@pytest.mark.depends(
    on=[
        "tests/test_datasets.py::test_datasets_create",
        "tests/test_evaluation.py::test_evaluations_create",
        "test_modules_create_python_rubric",
    ]
)
def test_reports_create(pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx):
    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()

    account = ctx["account"]
    evaluation = ctx["evaluation"]
    module = ctx["module_python_rubric"]
    report_request = ReportCreateRequest(
        account=account,
        rubric="dyff.fake.rubric.BlurstCount",
        evaluation=evaluation.id,
        modules=[module.id],
    )
    report = dyffapi.reports.create(report_request)
    print(f"report: {report.id}")
    ctx["report"] = report

    wait_for_success(
        lambda: dyffapi.reports.get(report.id),
        timeout=timedelta(minutes=5),
    )


@pytest.mark.depends(on=["tests/test_analysis.py::test_reports_create"])
def test_reports_download(pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx):
    if not pytestconfig.getoption("test_remote"):
        pytest.skip("reports download test requires remote API")
    report = ctx["report"]
    download_and_assert(dyffapi.reports.download, report.id, "data/report")


@pytest.mark.depends(
    on=[
        "test_methods_create_jupyter_notebook",
        "test_measurements_create_python_function",
    ]
)
# Run multiple times so we have multiple SafetyCases for one service; needed
# for testing the frontend UI.
@pytest.mark.parametrize("replication", range(3))
def test_safetycase(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, replication
):
    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()

    account = ctx["account"]
    inferenceservice = ctx["inferenceservice_mock"]
    model = ctx["model_mock"]
    method_jupyter_notebook = ctx["method_jupyter_notebook"]
    measurement_python_function = ctx["measurement_python_function"]

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
            AnalysisArgument(keyword="isOutlier", value="true"),
        ],
        inputs=[
            AnalysisInput(keyword="cromulence", entity=measurement_python_function.id),
        ],
    )
    safetycase_jupyter_notebook = dyffapi.safetycases.create(
        safetycase_jupyter_notebook_request
    )
    print(f"safetycase_jupyter_notebook: {safetycase_jupyter_notebook.id}")
    ctx["safetycase_jupyter_notebook"] = safetycase_jupyter_notebook

    wait_for_success(
        lambda: dyffapi.safetycases.get(safetycase_jupyter_notebook.id),
        timeout=timedelta(minutes=5),
    )


@pytest.mark.depends(
    on=[
        "test_safetycase",
    ]
)
def test_safetycase_download(pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx):
    if not pytestconfig.getoption("test_remote"):
        pytest.skip("safetycase download test requires remote API")
    safetycase_jupyter_notebook = ctx["safetycase_jupyter_notebook"]
    download_and_assert(
        dyffapi.safetycases.download, safetycase_jupyter_notebook.id, "data/safetycase"
    )


# Comparison safetycase for same method, different model
@pytest.mark.depends(
    on=[
        "test_methods_create_jupyter_notebook",
        "test_measurements_create_python_function",
    ]
)
@pytest.mark.parametrize("replication", range(COMPARISON_REPLICATIONS))
def test_safetycase_compare(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, replication
):
    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()
    if not pytestconfig.getoption("enable_comparisons"):
        pytest.skip()

    account = ctx["account"]
    inferenceservice = ctx[f"inferenceservice_mock_compare_{replication}"]
    model = ctx[f"model_mock_compare_{replication}"]
    method_jupyter_notebook = ctx["method_jupyter_notebook"]  # Same method
    measurement_python_function = ctx["measurement_python_function"]
    isOutlier = "true" if replication == 0 else "false"

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
            AnalysisArgument(keyword="isOutlier", value=isOutlier),
        ],
        inputs=[
            AnalysisInput(keyword="cromulence", entity=measurement_python_function.id),
        ],
    )
    safetycase_jupyter_notebook = dyffapi.safetycases.create(
        safetycase_jupyter_notebook_request
    )
    print(
        f"safetycase_jupyter_notebook_compare_{replication}: {safetycase_jupyter_notebook.id}"
    )
    ctx[f"safetycase_jupyter_notebook_compare_{replication}"] = (
        safetycase_jupyter_notebook
    )

    wait_for_success(
        lambda: dyffapi.safetycases.get(safetycase_jupyter_notebook.id),
        timeout=timedelta(minutes=5),
    )


@pytest.mark.depends(
    on=[
        "test_methods_create_jupyter_notebook_no_scores",
        "test_measurements_create_python_function",
    ]
)
def test_safetycase_no_scores(
    pytestconfig,
    dyffapi: Client | DyffLocalPlatform,
    ctx,
):
    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()

    account = ctx["account"]
    inferenceservice = ctx["inferenceservice_mock"]
    model = ctx["model_mock"]
    method_jupyter_notebook = ctx["method_jupyter_notebook_no_scores"]
    measurement_python_function = ctx["measurement_python_function"]

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
        inputs=[
            AnalysisInput(keyword="cromulence", entity=measurement_python_function.id),
        ],
    )
    safetycase_jupyter_notebook = dyffapi.safetycases.create(
        safetycase_jupyter_notebook_request
    )
    print(f"safetycase_jupyter_notebook_no_scores: {safetycase_jupyter_notebook.id}")
    ctx["safetycase_jupyter_notebook_no_scores"] = safetycase_jupyter_notebook

    wait_for_success(
        lambda: dyffapi.safetycases.get(safetycase_jupyter_notebook.id),
        timeout=timedelta(minutes=5),
    )


@pytest.mark.depends(
    on=[
        "test_safetycase",
    ]
)
def test_safetycase_publish(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()

    safetycase: SafetyCase = ctx["safetycase_jupyter_notebook"]
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()

    assert isinstance(dyffapi, Client)

    dyffapi.safetycases.publish(safetycase.id, "preview")
    dyffapi.methods.publish(safetycase.method.id, "preview")
    if safetycase.scope.inferenceService:
        dyffapi.inferenceservices.publish(safetycase.scope.inferenceService, "preview")
    if safetycase.scope.model:
        dyffapi.models.publish(safetycase.scope.model, "preview")
    time.sleep(10)
    labels = dyffapi.safetycases.get(safetycase.id).labels
    assert labels["dyff.io/access"] == "internal"


@pytest.mark.depends(
    on=[
        "test_safetycase_compare",
    ]
)
@pytest.mark.parametrize("replication", range(COMPARISON_REPLICATIONS))
def test_safetycase_publish_compare(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles, replication
):
    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()
    if not pytestconfig.getoption("enable_comparisons"):
        pytest.skip()
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()

    safetycase: SafetyCase = ctx[f"safetycase_jupyter_notebook_compare_{replication}"]

    assert isinstance(dyffapi, Client)

    dyffapi.safetycases.publish(safetycase.id, "preview")
    dyffapi.methods.publish(safetycase.method.id, "preview")
    if safetycase.scope.inferenceService:
        dyffapi.inferenceservices.publish(safetycase.scope.inferenceService, "preview")
    if safetycase.scope.model:
        dyffapi.models.publish(safetycase.scope.model, "preview")
    time.sleep(10)
    labels = dyffapi.safetycases.get(safetycase.id).labels
    assert labels["dyff.io/access"] == "internal"


@pytest.mark.depends(
    on=[
        "test_safetycase",
    ]
)
def test_safetycase_scores(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()
    assert isinstance(dyffapi, Client)

    method_jupyter_notebook: Method = ctx["method_jupyter_notebook"]
    safetycase_jupyter_notebook: SafetyCase = ctx["safetycase_jupyter_notebook"]
    scores = dyffapi.safetycases.scores(safetycase_jupyter_notebook.id)
    spec_names = sorted(s.name for s in method_jupyter_notebook.scores)
    actual_names = sorted(s.name for s in scores)
    assert spec_names == actual_names
    assert all(s.analysis == safetycase_jupyter_notebook.id for s in scores)


@pytest.mark.depends(
    on=[
        "test_safetycase",
    ]
)
def test_safetycase_query_scores(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()
    assert isinstance(dyffapi, Client)

    method_jupyter_notebook: Method = ctx["method_jupyter_notebook"]
    safetycase_jupyter_notebook: SafetyCase = ctx["safetycase_jupyter_notebook"]
    scores = dyffapi.safetycases.query_scores(
        id=safetycase_jupyter_notebook.id, method=method_jupyter_notebook.id
    )
    spec_names = sorted(s.name for s in method_jupyter_notebook.scores)
    actual_names = sorted(s.name for s in scores)
    assert spec_names == actual_names
    assert all(s.analysis == safetycase_jupyter_notebook.id for s in scores)


@pytest.mark.depends(
    on=[
        "test_safetycase",
    ]
)
def test_scores_get(pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles):
    if pytestconfig.getoption("test_remote"):
        # TODO: Enable once method is implemented in remote client
        pytest.skip()
    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()
    # TODO: Enable once method is implemented in remote client
    assert isinstance(dyffapi, DyffLocalPlatform)

    safetycase: SafetyCase = ctx["safetycase_jupyter_notebook"]
    scores = dyffapi.scores.get(analysis=safetycase.id)
    print(f"scores_get: {[score.name for score in scores]}")


@pytest.mark.depends(
    on=[
        "test_modules_create_python_function",
    ]
)
def test_modules_documentation(pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx):
    if pytestconfig.getoption("skip_documentation"):
        pytest.skip("skip_documentation config should be disabled")

    module = ctx["module_python_function"]
    assert_documentation_exist(dyffapi.modules.documentation, module.id)


@pytest.mark.depends(
    on=[
        "test_modules_create_python_function",
    ]
)
def test_modules_edit_documentation(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx
):
    if pytestconfig.getoption("skip_documentation"):
        pytest.skip("skip_documentation config should be disabled")

    module = ctx["module_python_function"]
    edit_documentation_and_assert(
        dyffapi.modules.edit_documentation,
        module.id,
        tile="EditedTitle",
        summary="EditedSummary",
        fullpage="EditedFullPage",
    )


@pytest.mark.depends(
    on=[
        "test_methods_create_python_function",
    ]
)
def test_methods_documentation(pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx):
    if pytestconfig.getoption("skip_documentation"):
        pytest.skip("skip_documentation config should be disabled")

    method = ctx["method_python_function"]
    assert_documentation_exist(dyffapi.methods.documentation, method.id)


@pytest.mark.depends(
    on=[
        "test_methods_create_python_function",
    ]
)
def test_methods_edit_documentation(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx
):
    if pytestconfig.getoption("skip_documentation"):
        pytest.skip("skip_documentation config should be disabled")

    method = ctx["method_python_function"]
    edit_documentation_and_assert(
        dyffapi.methods.edit_documentation,
        method.id,
        tile="EditedTitle",
        summary="EditedSummary",
        fullpage="EditedFullPage",
    )


# ==========================================
# BACKWARD COMPATIBILITY TESTS
# ==========================================


@pytest.mark.depends(
    on=[
        "tests/test_datasets.py::test_datasets_create",
        "tests/test_models.py::test_models_create_mock",
        "tests/test_inference.py::test_inferenceservices_create_mock",
        "tests/test_evaluation.py::test_evaluations_create",
        "tests/test_analysis.py::test_modules_create_python_function",
    ]
)
def test_methods_create_pydantic_v1_targeted(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx
):
    """Test Method creation with explicit Pydantic v1 analysisImage."""
    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()

    # Use Pydantic v1 image digest (0.7.7)
    pydantic_v1_image = ContainerImageSource(
        host="registry.gitlab.com",
        name="dyff/workflows/run-report",
        digest="sha256:d720053496a1f168a7173249c1b4d94b75d025017cae05d0d72f81c513cadabf",
    )

    method = dyffapi.methods.create(
        MethodCreateRequest(
            name="method_pydantic_v1_test",
            scope=MethodScope.Evaluation,
            account=ctx["account"],
            implementation=MethodImplementation(
                kind=MethodImplementationKind.PythonFunction,
                pythonFunction=MethodImplementationPythonFunction(
                    fullyQualifiedName="dyff.fake.method.blurst_count",
                ),
            ),
            inputs=[
                MethodInput(kind="Dataset", keyword="dataset"),
                MethodInput(kind="Evaluation", keyword="outputs"),
            ],
            output=MethodOutput(
                kind=MethodOutputKind.Measurement,
                measurement=MeasurementSpec(
                    level=MeasurementLevel.Instance,
                    name="example.dyff.io/pydantic-v1-test",
                    description="Pydantic v1 test measurement",
                    schema=DataSchema(
                        arrowSchema="struct<>", jsonSchema={"type": "object"}
                    ),
                ),
            ),
            modules=[ctx["module_python_function"].id],
            parameters=[
                MethodParameter(keyword="embiggen"),
            ],
            analysisImage=pydantic_v1_image,  # Explicit v1 image assignment
        )
    )

    assert method.name == "method_pydantic_v1_test"
    assert method.analysisImage is not None
    # Should get the explicit v1 image we specified
    assert (
        method.analysisImage.digest
        == "sha256:d720053496a1f168a7173249c1b4d94b75d025017cae05d0d72f81c513cadabf"
    )

    ctx["method_pydantic_v1_test"] = method


@pytest.mark.depends(
    on=[
        "tests/test_datasets.py::test_datasets_create",
        "tests/test_models.py::test_models_create_mock",
        "tests/test_inference.py::test_inferenceservices_create_mock",
        "tests/test_evaluation.py::test_evaluations_create",
        "tests/test_analysis.py::test_modules_create_python_function",
    ]
)
def test_methods_create_pydantic_v2_targeted(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx
):
    """Test Method creation with explicit Pydantic v2 analysisImage."""

    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()

    # Use Pydantic v2 image digest (0.8.0)
    pydantic_v2_image = ContainerImageSource(
        host="registry.gitlab.com",
        name="dyff/workflows/run-report",
        digest="sha256:36b524c0f253014afe5b2f85931179e1fbfc7f540cfe5b47306718f1ff2ccf8b",
    )

    method = dyffapi.methods.create(
        MethodCreateRequest(
            name="method_pydantic_v2_test",
            scope=MethodScope.Evaluation,
            account=ctx["account"],
            implementation=MethodImplementation(
                kind=MethodImplementationKind.PythonFunction,
                pythonFunction=MethodImplementationPythonFunction(
                    fullyQualifiedName="dyff.fake.method.blurst_count",
                ),
            ),
            inputs=[
                MethodInput(kind="Dataset", keyword="dataset"),
                MethodInput(kind="Evaluation", keyword="outputs"),
            ],
            output=MethodOutput(
                kind=MethodOutputKind.Measurement,
                measurement=MeasurementSpec(
                    level=MeasurementLevel.Instance,
                    name="example.dyff.io/pydantic-v2-test",
                    description="Pydantic v2 test measurement",
                    schema=DataSchema(
                        arrowSchema="struct<>", jsonSchema={"type": "object"}
                    ),
                ),
            ),
            modules=[ctx["module_python_function"].id],
            parameters=[
                MethodParameter(keyword="embiggen"),
            ],
            analysisImage=pydantic_v2_image,  # Explicit v2 image assignment
        )
    )

    assert method.name == "method_pydantic_v2_test"
    assert method.analysisImage is not None

    ctx["method_pydantic_v2_test"] = method


# ==========================================
# RUNTIME COMPATIBILITY TESTS
# ==========================================


def test_modules_create_pydantic_v1_test(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx
):
    """Create module for Pydantic v1 runtime testing."""

    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()

    account = ctx["account"]
    module_dir = DATA_DIR / "module_pydantic_v1_test"
    module = dyffapi.modules.create_package(
        module_dir, account=account, name="module_pydantic_v1_test"
    )
    dyffapi.modules.upload_package(module, module_dir)

    wait_for_success(
        lambda: dyffapi.modules.get(module.id),
        timeout=timedelta(minutes=1),
    )
    module = dyffapi.modules.get(module.id)

    assert module.name == "module_pydantic_v1_test"
    ctx["module_pydantic_v1_test"] = module


def test_modules_create_pydantic_v2_test(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx
):
    """Create module for Pydantic v2 runtime testing."""

    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()

    account = ctx["account"]
    module_dir = DATA_DIR / "module_pydantic_v2_test"
    module = dyffapi.modules.create_package(
        module_dir, account=account, name="module_pydantic_v2_test"
    )
    dyffapi.modules.upload_package(module, module_dir)

    wait_for_success(
        lambda: dyffapi.modules.get(module.id),
        timeout=timedelta(minutes=1),
    )
    module = dyffapi.modules.get(module.id)

    assert module.name == "module_pydantic_v2_test"
    ctx["module_pydantic_v2_test"] = module


@pytest.mark.depends(
    on=[
        "tests/test_datasets.py::test_datasets_create",
        "tests/test_models.py::test_models_create_mock",
        "tests/test_inference.py::test_inferenceservices_create_mock",
        "tests/test_evaluation.py::test_evaluations_create",
        "tests/test_analysis.py::test_modules_create_pydantic_v1_test",
    ]
)
def test_methods_create_pydantic_v1_runtime(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx
):
    """Test Method creation for Pydantic v1 runtime execution."""

    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()

    # Use explicit Pydantic v1 image
    pydantic_v1_image = ContainerImageSource(
        host="registry.gitlab.com",
        name="dyff/workflows/run-report",
        digest="sha256:d720053496a1f168a7173249c1b4d94b75d025017cae05d0d72f81c513cadabf",
    )

    method = dyffapi.methods.create(
        MethodCreateRequest(
            name="runtime_pydantic_v1_test",
            scope=MethodScope.InferenceService,
            account=ctx["account"],
            implementation=MethodImplementation(
                kind=MethodImplementationKind.JupyterNotebook,
                jupyterNotebook=MethodImplementationJupyterNotebook(
                    notebookModule=ctx["module_pydantic_v1_test"].id,
                    notebookPath="test-pydantic-v1.ipynb",
                ),
            ),
            inputs=[
                MethodInput(kind="Dataset", keyword="dummy_input"),
            ],
            output=MethodOutput(
                kind=MethodOutputKind.SafetyCase,
                safetyCase=SafetyCaseSpec(
                    name="pydantic_v1_runtime_test",
                    description="Pydantic v1 runtime test",
                ),
            ),
            modules=[ctx["module_pydantic_v1_test"].id],
            analysisImage=pydantic_v1_image,  # Explicit v1 image
        )
    )

    assert (
        method.analysisImage.digest
        == "sha256:d720053496a1f168a7173249c1b4d94b75d025017cae05d0d72f81c513cadabf"
    )
    ctx["method_runtime_pydantic_v1"] = method


@pytest.mark.depends(
    on=[
        "tests/test_analysis.py::test_methods_create_pydantic_v1_runtime",
    ]
)
def test_runtime_pydantic_v1_compatibility(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx
):
    """Test runtime execution with explicit Pydantic v1 image."""
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()
    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()

    # Get method created by previous test
    method = ctx["method_runtime_pydantic_v1"]

    # Create a minimal SafetyCase to test execution
    safetycase = dyffapi.safetycases.create(
        AnalysisCreateRequest(
            account=ctx["account"],
            method=method.id,
            scope=AnalysisScope(
                evaluation=None,
                dataset=None,
                inferenceService=ctx["inferenceservice_mock"].id,
                model=ctx["model_mock"].id if ctx.get("model_mock") else None,
            ),
            inputs=[
                AnalysisInput(keyword="dummy_input", entity=ctx["dataset"].id),
            ],
        )
    )

    print(f"Pydantic v1 runtime test SafetyCase: {safetycase.id}")
    ctx["safetycase_runtime_pydantic_v1"] = safetycase

    # Wait for completion with standard pattern
    wait_for_success(
        lambda: dyffapi.safetycases.get(safetycase.id),
        timeout=timedelta(minutes=5),
    )

    print("Pydantic v1 runtime compatibility: PASSED")


@pytest.mark.depends(
    on=[
        "tests/test_datasets.py::test_datasets_create",
        "tests/test_models.py::test_models_create_mock",
        "tests/test_inference.py::test_inferenceservices_create_mock",
        "tests/test_evaluation.py::test_evaluations_create",
        "tests/test_analysis.py::test_modules_create_pydantic_v2_test",
    ]
)
def test_methods_create_pydantic_v2_runtime(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx
):
    """Test Method creation for Pydantic v2 runtime execution."""

    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()

    # Use explicit Pydantic v2 image
    pydantic_v2_image = ContainerImageSource(
        host="registry.gitlab.com",
        name="dyff/workflows/run-report",
        digest="sha256:36b524c0f253014afe5b2f85931179e1fbfc7f540cfe5b47306718f1ff2ccf8b",
    )

    method = dyffapi.methods.create(
        MethodCreateRequest(
            name="runtime_pydantic_v2_test",
            scope=MethodScope.InferenceService,
            account=ctx["account"],
            implementation=MethodImplementation(
                kind=MethodImplementationKind.JupyterNotebook,
                jupyterNotebook=MethodImplementationJupyterNotebook(
                    notebookModule=ctx["module_pydantic_v2_test"].id,
                    notebookPath="test-pydantic-v2.ipynb",
                ),
            ),
            inputs=[
                MethodInput(kind="Dataset", keyword="dummy_input"),
            ],
            output=MethodOutput(
                kind=MethodOutputKind.SafetyCase,
                safetyCase=SafetyCaseSpec(
                    name="pydantic_v2_runtime_test",
                    description="Pydantic v2 runtime test",
                ),
            ),
            modules=[ctx["module_pydantic_v2_test"].id],
            analysisImage=pydantic_v2_image,  # Explicit v2 image
        )
    )

    # Verify analysisImage is set
    ctx["method_runtime_pydantic_v2"] = method


@pytest.mark.depends(
    on=[
        "tests/test_analysis.py::test_methods_create_pydantic_v2_runtime",
    ]
)
def test_runtime_pydantic_v2_compatibility(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx
):
    """Test runtime execution with explicit Pydantic v2 image."""
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()
    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()

    # Get method created by previous test
    method = ctx["method_runtime_pydantic_v2"]

    # Create a minimal SafetyCase to test execution
    safetycase = dyffapi.safetycases.create(
        AnalysisCreateRequest(
            account=ctx["account"],
            method=method.id,
            scope=AnalysisScope(
                evaluation=None,
                dataset=None,
                inferenceService=ctx["inferenceservice_mock"].id,
                model=ctx["model_mock"].id if ctx.get("model_mock") else None,
            ),
            inputs=[
                AnalysisInput(keyword="dummy_input", entity=ctx["dataset"].id),
            ],
        )
    )

    print(f"Pydantic v2 runtime test SafetyCase: {safetycase.id}")
    ctx["safetycase_runtime_pydantic_v2"] = safetycase

    # Wait for completion with standard pattern
    wait_for_success(
        lambda: dyffapi.safetycases.get(safetycase.id),
        timeout=timedelta(minutes=5),
    )

    print("Pydantic v2 runtime compatibility: PASSED")


@pytest.mark.depends(
    on=[
        "tests/test_datasets.py::test_datasets_create",
        "tests/test_models.py::test_models_create_mock",
        "tests/test_inference.py::test_inferenceservices_create_mock",
        "tests/test_evaluation.py::test_evaluations_create",
        "tests/test_analysis.py::test_modules_create_pydantic_v2_test",
    ]
)
def test_api_default_image_execution(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx
):
    """Test SafetyCase execution with API default image."""
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()
    if pytestconfig.getoption("skip_analyses"):
        pytest.skip()

    # Create Method without specifying analysisImage to test API default
    method = dyffapi.methods.create(
        MethodCreateRequest(
            name="api_default_image_test",
            scope=MethodScope.InferenceService,
            account=ctx["account"],
            implementation=MethodImplementation(
                kind=MethodImplementationKind.JupyterNotebook,
                jupyterNotebook=MethodImplementationJupyterNotebook(
                    notebookModule=ctx["module_pydantic_v2_test"].id,
                    notebookPath="test-pydantic-v2.ipynb",
                ),
            ),
            inputs=[
                MethodInput(kind="Dataset", keyword="dummy_input"),
            ],
            output=MethodOutput(
                kind=MethodOutputKind.SafetyCase,
                safetyCase=SafetyCaseSpec(
                    name="api_default_image_test",
                    description="Test API default analysisImage execution",
                ),
            ),
            modules=[ctx["module_pydantic_v2_test"].id],
            # NO analysisImage specified - should get current default
        )
    )

    # Verify method got an analysisImage assigned
    assert method.analysisImage is not None
    print(f"API automatically set analysisImage: {method.analysisImage.digest}")

    # Test execution to verify the image works
    safetycase = dyffapi.safetycases.create(
        AnalysisCreateRequest(
            account=ctx["account"],
            method=method.id,
            scope=AnalysisScope(
                evaluation=None,
                dataset=None,
                inferenceService=ctx["inferenceservice_mock"].id,
                model=ctx["model_mock"].id if ctx.get("model_mock") else None,
            ),
            inputs=[
                AnalysisInput(keyword="dummy_input", entity=ctx["dataset"].id),
            ],
        )
    )

    print(f"API default image test SafetyCase: {safetycase.id}")
    ctx["safetycase_api_default"] = safetycase

    print("Testing SafetyCase execution with default image")

    # Wait for completion with standard pattern
    wait_for_success(
        lambda: dyffapi.safetycases.get(safetycase.id),
        timeout=timedelta(minutes=5),
    )

    print("API automatically sets analysisImage for new Methods: PASSED")
