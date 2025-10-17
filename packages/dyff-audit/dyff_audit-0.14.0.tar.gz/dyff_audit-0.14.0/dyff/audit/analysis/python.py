# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

from dyff.schema.dataset import arrow
from dyff.schema.platform import (
    MeasurementLevel,
    MethodImplementationKind,
    MethodOutputKind,
)

from .. import dynamic_import
from ..analysis import AnalysisContext
from ..scoring import Rubric


def run_python_function():
    ctx = AnalysisContext()
    implementation = ctx.analysis.method.implementation
    if (
        implementation.kind != MethodImplementationKind.PythonFunction
        or implementation.pythonFunction is None
    ):
        raise ValueError("expected method.implementation as PythonFunction")
    output = ctx.analysis.method.output
    if output.kind != MethodOutputKind.Measurement or output.measurement is None:
        raise ValueError("expected method.output as Measurement")

    function = dynamic_import.symbol(implementation.pythonFunction.fullyQualifiedName)
    input_data = {i: ctx.open_input_dataset(i) for i in ctx.inputs}
    output_generator = function(ctx.arguments, **input_data)
    output_schema = arrow.decode_schema(output.measurement.schema_.arrowSchema)

    # TODO: We're not doing anything with the DataViews yet

    arrow.write_dataset(
        output_generator,
        output_path=ctx.output_path,
        feature_schema=output_schema,
    )


def run_python_rubric():
    ctx = AnalysisContext()
    implementation = ctx.analysis.method.implementation
    if (
        implementation.kind != MethodImplementationKind.PythonRubric
        or implementation.pythonRubric is None
    ):
        raise ValueError("expected method implemented as PythonRubric")
    output = ctx.analysis.method.output
    if output.kind != MethodOutputKind.Measurement or output.measurement is None:
        raise ValueError("expected method.output as Measurement")
    if output.measurement.level != MeasurementLevel.Instance:
        raise ValueError("expected measurement.level == Instance")
    if ctx.arguments:
        raise ValueError("Rubrics do not accept arguments")

    fqn = implementation.pythonRubric.fullyQualifiedName
    try:
        rubric = dynamic_import.instantiate(fqn)
    except ImportError:
        # Backwards compatibility
        rubric = dynamic_import.instantiate(f"dyff.audit.scoring.{fqn}")
    if not isinstance(rubric, Rubric):
        raise ValueError(f"{fqn} is not a Rubric subclass")
    output_schema = arrow.decode_schema(output.measurement.schema_.arrowSchema)

    task_data = ctx.open_input_dataset("task_data")
    predictions = ctx.open_input_dataset("predictions")

    # TODO: We're not doing anything with the DataViews yet

    arrow.write_dataset(
        rubric.apply(task_data, predictions),
        output_path=str(ctx.output_path),
        feature_schema=output_schema,
    )
