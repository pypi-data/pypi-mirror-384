# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0
"""Base class for Metrics."""

# mypy: disable-error-code="import-untyped"
from __future__ import annotations

import abc

import pandas
import pyarrow


class Metric(abc.ABC):
    """A Metric is an operation that can be applied to a set of inference-level scores
    to produce an aggregate summary of performance."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """The "semi-qualified" type name of the Metric.

        The result should be
        such that ``f"alignmentlabs.audit.metrics.{self.name}"`` is the
        fully-qualified name of the type.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def schema(self) -> pyarrow.Schema:
        """The PyArrow schema of the output of applying the Metric."""
        raise NotImplementedError

    @abc.abstractmethod
    def __call__(self, scores: pandas.DataFrame) -> pandas.DataFrame:
        """Compute the metric."""
        raise NotImplementedError
