# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0
"""Metrics related to text processing tasks."""

# mypy: disable-error-code="import-untyped"
import pandas
import pyarrow
import pydantic

from dyff.schema.base import DyffSchemaBaseModel, int32
from dyff.schema.dataset.arrow import arrow_schema, schema_function

from ..scoring.text import MatchCriterion, MatchResult
from .base import Metric


def f1_score(df: pandas.DataFrame) -> pandas.Series:
    """F1 score is the harmonic mean of precision and recall.

    :param df: Must contain columns ``precision`` and ``recall``.
    :type df: pandas.DataFrame
    """
    return (2 * df["precision"] * df["recall"]) / (df["precision"] + df["recall"])


class ExtendedPrecisionRecallScore(DyffSchemaBaseModel):
    MatchCriterion: str = pydantic.Field(
        description=":class:`MatchCriterion <dyff.audit.scoring.text.MatchCriterion>` applicable to this record.",
    )
    MatchResultCorrect: int32() = pydantic.Field(
        alias="MatchResult.correct", description="Count of ``correct`` matches."
    )
    MatchResultIncorrect: int32() = pydantic.Field(
        alias="MatchResult.incorrect",
        description="Count of ``incorrect`` matches.",
    )
    MatchResultPartial: int32() = pydantic.Field(
        alias="MatchResult.partial", description="Count of ``partial`` matches."
    )
    MatchResultMissing: int32() = pydantic.Field(
        alias="MatchResult.missing", description="Count of ``missing`` matches."
    )
    MatchResultSpurious: int32() = pydantic.Field(
        alias="MatchResult.spurious", description="Count of ``spurious`` matches."
    )
    possible: int32() = pydantic.Field(description='Number of "possible" matches.')
    actual: int32() = pydantic.Field(description='Number of "actual" matches.')
    precision: float = pydantic.Field(description="Precision score.")
    recall: float = pydantic.Field(description="Recall score.")
    f1_score: float = pydantic.Field(description="F1 score.")


class ExtendedPrecisionRecall(Metric):
    """Compute precision and recall for the extended set of text span matching criteria
    defined in ``dyff.audit.scoring.text``."""

    @property
    def name(self) -> str:
        return "text.ExtendedPrecisionRecall"

    @property
    @schema_function(arrow_schema(ExtendedPrecisionRecallScore))
    def schema(self) -> pyarrow.Schema:
        """The PyArrow schema of the output of applying the Metric."""

    def __call__(self, text_span_matches: pandas.DataFrame) -> pandas.DataFrame:
        def possible(df):
            return sum(
                [
                    df[str(MatchResult.correct)],
                    df[str(MatchResult.incorrect)],
                    df[str(MatchResult.partial)],
                    df[str(MatchResult.missing)],
                ]
            )

        def actual(df):
            return sum(
                [
                    df[str(MatchResult.correct)],
                    df[str(MatchResult.incorrect)],
                    df[str(MatchResult.partial)],
                    df[str(MatchResult.spurious)],
                ]
            )

        def precision(row):
            if row["MatchCriterion"] in [MatchCriterion.strict, MatchCriterion.exact]:
                return row[str(MatchResult.correct)] / row["actual"]
            else:
                return (
                    row[str(MatchResult.correct)] + 0.5 * row[str(MatchResult.partial)]
                ) / row["actual"]

        def recall(row):
            if row["MatchCriterion"] in [MatchCriterion.strict, MatchCriterion.exact]:
                return row[str(MatchResult.correct)] / row["possible"]
            else:
                return (
                    row[str(MatchResult.correct)] + 0.5 * row[str(MatchResult.partial)]
                ) / row["possible"]

        keep_columns = ["MatchCriterion"] + [str(r) for r in MatchResult]
        sums = (
            text_span_matches.filter(keep_columns)
            .groupby("MatchCriterion")
            .sum()
            .reset_index()
        )
        sums["possible"] = possible(sums)
        sums["actual"] = actual(sums)
        sums["precision"] = sums.apply(precision, axis=1)
        sums["recall"] = sums.apply(recall, axis=1)
        sums["f1_score"] = f1_score(sums)
        return sums
