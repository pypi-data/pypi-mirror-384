# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0
"""Rubrics related to supervised classification."""

# mypy: disable-error-code="import-untyped"
from __future__ import annotations

import logging
from typing import Any, Iterable, List

import pyarrow
import pydantic

from dyff.schema.dataset import ReplicatedItem
from dyff.schema.dataset.arrow import arrow_schema, schema_function

from .base import Rubric


def top_k(prediction: Any | List[Any], truth: Any, *, k: int) -> int:
    """Return ``1`` if any of the first ``k`` elements of ``prediction`` are equal to
    ``truth``, and ``0`` otherwise.

    :param prediction: Either a list of predicted labels in descending order of
      "score", or a single predicted label. For a single label, all values
      of ``k`` are equivalent to ``k = 1``.
    :type prediction: Any or List(Any)
    :param truth: The true label.
    :type truth: Any
    :param k: The number of predictions to consider.
    :type k: int
    :return: ``1`` if one of the top ``k`` predictions was correct, ``0`` otherwise.
    :rtype: int
    """
    if k < 1:
        raise ValueError("'k' must be >= 1")
    if isinstance(prediction, list):
        last = min(k, len(prediction))
        return int(truth in prediction[:last])
    else:
        return truth == prediction


class TopKAccuracyScoredItem(ReplicatedItem):
    """Placeholder."""

    top1: bool = pydantic.Field(
        ...,
        description="0-1 indicator of whether the top-1 prediction was correct.",
    )
    top5: bool = pydantic.Field(
        ...,
        description="0-1 indicator of whether any of the top-5 predictions were correct.",
    )


class TopKAccuracy(Rubric):
    """Computes top-1 and top-5 accuracy for classification tasks."""

    def __init__(self):
        self._ks = [1, 5]

    def _build_labels_dict(self, labels_dataset):
        labels = {}
        for b in labels_dataset.to_batches(columns=["_index_", "label"]):
            df = b.to_pandas()
            for index, label in zip(df["_index_"], df["label"]):
                labels[index] = label
        return labels

    @property
    def name(self) -> str:
        return "classification.TopKAccuracy"

    @property
    @schema_function(arrow_schema(TopKAccuracyScoredItem))
    def schema(self) -> pyarrow.Schema:
        """The PyArrow schema of the output of applying the Rubric.

        There is one row per input instance. A prediction is scored as correct if
        ``prediction == truth``. For top-5 accuracy, the instance is correct if
        any of the top-5 predictions was correct.
        """

    def apply(
        self, task_data: pyarrow.datasets.Dataset, predictions: pyarrow.datasets.Dataset
    ) -> Iterable[pyarrow.RecordBatch]:
        labels_dict = self._build_labels_dict(task_data)
        processed = []
        for b in predictions.to_batches(
            columns=["_index_", "_replication_", "responses"]
        ):
            batch = []
            for item in b.to_pylist():
                index = item["_index_"]
                replication = item["_replication_"]
                responses = item["responses"]
                truth = labels_dict[index]
                scored_item = TopKAccuracyScoredItem(
                    _index_=index,
                    _replication_=replication,
                    top1=bool(top_k(responses, truth, k=1)),
                    top5=bool(top_k(responses, truth, k=5)),
                )
                batch.append(scored_item.dict())
                processed.append(index)
                if len(processed) % 100000 == 0:
                    logging.info(f"processed {len(processed)} items")
            yield pyarrow.RecordBatch.from_pylist(batch, schema=self.schema)
        logging.info(f"final: {len(processed)} items; {len(set(processed))} unique")


__all__ = [
    "TopKAccuracy",
    "TopKAccuracyScoredItem",
    "top_k",
]
