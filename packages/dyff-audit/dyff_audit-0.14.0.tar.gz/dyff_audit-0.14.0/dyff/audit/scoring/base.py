# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0
"""Base class for Rubrics."""

# mypy: disable-error-code="import-untyped"
from __future__ import annotations

import abc
from typing import Iterable

import pyarrow


class Rubric(abc.ABC):
    """A Rubric is a mechanism for producing inference-level performance scores for the
    output of an inference service on a given inference task."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """The "semi-qualified" type name of the Rubric.

        The result should be
        such that ``f"alignmentlabs.audit.scoring.{self.name}"`` is the
        fully-qualified name of the type.
        """
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def schema(self) -> pyarrow.Schema:
        """The PyArrow schema of the output of applying the Rubric."""
        raise NotImplementedError()

    @abc.abstractmethod
    def apply(
        self, task_data: pyarrow.datasets.Dataset, predictions: pyarrow.datasets.Dataset
    ) -> Iterable[pyarrow.RecordBatch]:
        """Create a generator that yields batches of scored inferences."""
        raise NotImplementedError()
