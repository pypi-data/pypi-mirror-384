# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0
"""Rubrics related to text processing tasks."""

# mypy: disable-error-code="import-untyped"
from __future__ import annotations

import enum
import logging
from typing import Any, Dict, Iterable, List

import pyarrow
import pydantic

from dyff.schema.base import int32
from dyff.schema.dataset import ReplicatedItem
from dyff.schema.dataset.arrow import arrow_schema, schema_function

from .base import Rubric


class MatchCriterion(str, enum.Enum):
    """The match criteria defined by the SemEval2013 evaluation standard.

    See :class:`MatchResult` for the possible results of matching.

    .. seealso::

      https://www.davidsbatista.net/blog/2018/05/09/Named_Entity_Evaluation/
    """

    #: The prediction is ``correct`` if ``[start, end)`` match exactly and the
    #: tag is correct. Otherwise, the prediction is ``incorrect``.
    strict = "strict"

    #: Tag is ignored. The prediction is ``correct`` if ``[start, end)`` match
    #: exactly. Otherwise, the prediction is ``incorrect``.
    exact = "exact"

    #: Tag is ignored. Partial overlap is scored as ``partial``, exact overlap
    #: is scored as ``correct``, no overlap is scored as ``incorrect``.
    partial = "partial"

    #: Partial overlap is scored as either ``correct`` or ``incorrect`` based on
    #: the predicted tag. No overlap is scored as ``incorrect``.
    type = "type"


class MatchResult(str, enum.Enum):
    """The possible results of a text span matching comparison as defined by the MUC-5
    evaluation standard.

    Note that the semantics of these results depend on which
    :class:`MatchCriterion` is being applied.

    .. seealso::

      https://www.davidsbatista.net/blog/2018/05/09/Named_Entity_Evaluation/
    """

    #: The prediction overlapped with a true entity and was correct.
    correct = "correct"

    #: The prediction overlapped with a true entity but was incorrect.
    incorrect = "incorrect"

    #: The prediction overlapped a true entity partially but not exactly.
    #: Applies to ``MatchCriterion.partial`` only.
    partial = "partial"

    #: A ground-truth entity did not overlap with any predicted entity.
    missing = "missing"

    #: A predicted entity did not overlap with any ground-truth entity.
    spurious = "spurious"


def match_spans(
    predictions: List[Dict[str, Any]], truths: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Compute matching results for ground-truth and predicted text spans using the
    extended set of matching criteria defined by the SemEval2013 and MUC-5 evaluation
    standards.

    :param predictions: List of predicted spans
    :param truths: List of ground-truth spans
    :return: A two-level dictionary containing match counts, like:
        ``{MatchCriterion: {MatchResult: Count}}``

    .. seealso::

      * https://www.davidsbatista.net/blog/2018/05/09/Named_Entity_Evaluation/
      * https://github.com/davidsbatista/NER-Evaluation
      * https://aclanthology.org/S13-2056.pdf
      * https://aclanthology.org/M93-1007.pdf
    """
    truths = list(sorted(truths, key=lambda span: span["start"]))
    predictions = list(sorted(predictions, key=lambda span: span["start"]))
    ti = 0
    intersected_truths = set()
    results = []

    for p, prediction in enumerate(predictions):
        logging.debug(prediction)
        spurious = True
        for t in range(ti, len(truths)):
            truth = truths[t]
            logging.debug(f"\t{truth}")
            if prediction["end"] < truth["start"]:
                logging.debug("\t\tprediction < truth")
                # ....TTTT
                # PPPP....
                break  # All remaining 'truths' come after 'prediction'
            elif truth["end"] < prediction["start"]:
                logging.debug("\t\ttruth < prediction")
                # TTTT....
                # ....PPPP
                ti = t + 1  # This 'truth' and all previous will never overlap again
            elif (
                prediction["start"] < truth["end"]
                and truth["start"] < prediction["end"]
            ):
                # Intersection
                spurious = False
                intersected_truths.add(t)
                correct_tag = (
                    MatchResult.correct
                    if truth["tag"] == prediction["tag"]
                    else MatchResult.incorrect
                )

                if (
                    truth["start"] == prediction["start"]
                    and truth["end"] == prediction["end"]
                ):
                    logging.debug("\t\texact")
                    # Exact overlap
                    # ..TTTT..
                    # ..PPPP..
                    for criterion in MatchCriterion:
                        row = {
                            "MatchCriterion": criterion,
                            "prediction": p,
                            "truth": t,
                            **{str(r): 0 for r in MatchResult},
                        }
                        if criterion in [MatchCriterion.strict, MatchCriterion.type]:
                            row[str(correct_tag)] = 1
                        else:
                            row[str(MatchResult.correct)] = 1
                        results.append(row)
                else:
                    logging.debug("\t\tpartial")
                    # Partial overlap
                    for criterion in MatchCriterion:
                        row = {
                            "MatchCriterion": criterion,
                            "prediction": p,
                            "truth": t,
                            **{str(r): 0 for r in MatchResult},
                        }
                        if criterion in [MatchCriterion.strict, MatchCriterion.exact]:
                            row[str(MatchResult.incorrect)] = 1
                        elif criterion == MatchResult.partial:
                            row[str(MatchResult.partial)] = 1
                        else:
                            row[str(correct_tag)] = 1
                        results.append(row)
        if spurious:
            logging.debug("\tspurious")
            for criterion in MatchCriterion:
                row = {
                    "MatchCriterion": criterion,
                    "prediction": p,
                    "truth": None,
                    **{str(r): 0 for r in MatchResult},
                }
                row[str(MatchResult.spurious)] = 1
                results.append(row)

    missing = set(range(len(truths))) - intersected_truths
    for criterion in MatchCriterion:
        for t, truth in enumerate(truths):
            if t in missing:
                row = {
                    "MatchCriterion": criterion,
                    "prediction": None,
                    "truth": t,
                    **{str(r): 0 for r in MatchResult},
                }
                row[str(MatchResult.missing)] = 1
                results.append(row)

    return results


class TextSpanMatchesScoredItem(ReplicatedItem):
    MatchCriterion: str = pydantic.Field(
        description=":class:`MatchCriterion` applicable to this record."
    )
    prediction: int32() = pydantic.Field(  # type: ignore
        description="Index of the relevant predicted span within the current instance.",
    )
    truth: int32() = pydantic.Field(  # type: ignore
        description="Index of the relevant ground truth span within the current instance.",
    )
    MatchResultCorrect: bool = pydantic.Field(
        alias="MatchResult.correct",
        description="Indicator of whether the match is ``correct``.",
    )
    MatchResultIncorrect: bool = pydantic.Field(
        alias="MatchResult.incorrect",
        description="Indicator of whether the match is ``incorrect``.",
    )
    MatchResultPartial: bool = pydantic.Field(
        alias="MatchResult.partial",
        description="Indicator of whether the match is ``partial``.",
    )
    MatchResultMissing: bool = pydantic.Field(
        alias="MatchResult.missing",
        description="Indicator of whether the match is ``missing``.",
    )
    MatchResultSpurious: bool = pydantic.Field(
        alias="MatchResult.spurious",
        description="Indicator of whether the match is ``spurious``.",
    )


class TextSpanMatches(Rubric):
    """Computes matches between predicted and ground-truth text spans according to each
    criterion in ``MatchCriterion``."""

    def _build_truth_dict(self, truth_dataset):
        truth = {}
        for b in truth_dataset.to_batches(columns=["_index_", "spans"]):
            for item in b.to_pylist():
                truth[item["_index_"]] = item["spans"]
        return truth

    @property
    def name(self) -> str:
        return "text.TextSpanMatches"

    @property
    @schema_function(arrow_schema(TextSpanMatchesScoredItem))
    def schema(self) -> pyarrow.Schema:
        """The PyArrow schema of the output of applying the Rubric.

        There may be 0 or more rows for each input instance (same ``_index_``).
        Each row indicates which predicted span within that instance overlapped
        with which ground truth span, and how that overlap was scored. For example,
        if the 1st predicted span overlapped with the 2nd ground truth span, then
        there will be a row with ``prediction = 1`` and ``truth = 2``. Spans are
        0-indexed in increasing order of their ``.start`` field. A ``spurious``
        match will have a value for ``prediction`` but not for ``truth``, and a
        ``missing`` match will have a value for ``truth`` but not for
        ``prediction``. Instances for which there are no predicted spans and no
        ground truth spans will not appear in the results.
        """

    def apply(
        self, task_data: pyarrow.datasets.Dataset, predictions: pyarrow.datasets.Dataset
    ) -> Iterable[pyarrow.RecordBatch]:
        truth_dict = self._build_truth_dict(task_data)
        processed = []
        for b in predictions.to_batches(
            columns=["_index_", "_replication_", "responses"]
        ):
            batch = []
            for item in b.to_pylist():
                index = item["_index_"]
                replication = item["_replication_"]
                predicted_spans = item["responses"][0]["spans"]
                truth_spans = truth_dict[index]
                results = match_spans(predicted_spans, truth_spans)
                for result in results:
                    batch.append(
                        {"_index_": index, "_replication_": replication, **result}
                    )
                processed.append(index)
            yield pyarrow.RecordBatch.from_pylist(batch, schema=self.schema)


__all__ = [
    "MatchCriterion",
    "MatchResult",
    "TextSpanMatches",
    "TextSpanMatchesScoredItem",
    "match_spans",
]


def _test():
    import json  # pylint: disable=import-outside-toplevel

    logging.set_verbosity(logging.DEBUG)

    # "Alice Washington and Bob Washington live in Washington National Forest with Wilma Washington"
    #  012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012
    #  0         1         2         3         4         5         6         7         8         9
    truth = [
        {"start": 0, "end": 16, "tag": "PER"},
        {"start": 21, "end": 35, "tag": "PER"},
        {"start": 44, "end": 70, "tag": "LOC"},
        {"start": 76, "end": 92, "tag": "PER"},
    ]

    predictions = [
        {"start": 0, "end": 5, "tag": "PER"},
        {"start": 6, "end": 16, "tag": "ORG"},
        {"start": 36, "end": 40, "tag": "PER"},
        {"start": 21, "end": 35, "tag": "PER"},
        {"start": 21, "end": 35, "tag": "LOC"},
        {"start": 76, "end": 81, "tag": "PER"},
    ]

    print(json.dumps(match_spans(predictions, truth), indent=2))


if __name__ == "__main__":
    _test()
