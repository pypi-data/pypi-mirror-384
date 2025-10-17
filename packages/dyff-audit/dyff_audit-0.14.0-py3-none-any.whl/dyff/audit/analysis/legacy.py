# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

# mypy: disable-error-code="import-untyped"
import sys
from typing import Optional

from dyff.schema.dataset import arrow

from .. import dynamic_import
from ..scoring import Rubric


def run_python_rubric(
    *,
    rubric: str,
    dataset_path: str,
    evaluation_path: str,
    output_path: str,
    modules: Optional[list[str]] = None,
):
    # Add extension modules to import path
    if modules:
        for module in modules:
            sys.path.append(module)

    try:
        rubric = dynamic_import.instantiate(rubric)
    except ImportError:
        # Backwards compatibility
        rubric = dynamic_import.instantiate(f"dyff.audit.scoring.{rubric}")
    if not isinstance(rubric, Rubric):
        raise ValueError(f"{rubric} is not a Rubric subclass")

    task_data = arrow.open_dataset(dataset_path)
    outputs_data = arrow.open_dataset(evaluation_path)

    # TODO: We're not doing anything with the DataViews yet

    arrow.write_dataset(
        rubric.apply(task_data, outputs_data),
        output_path=output_path,
        feature_schema=rubric.schema,
    )
