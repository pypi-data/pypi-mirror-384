# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

# mypy: disable-error-code="import-untyped"
from typing import Iterable

import pyarrow
import pyarrow.dataset
import pydantic

from dyff.schema.base import int32
from dyff.schema.dataset import ReplicatedItem
from dyff.schema.dataset.arrow import arrow_schema, schema_function

from .base import Rubric


class LikeCountScoredItem(ReplicatedItem):
    likeCount: int32() = pydantic.Field(  # type: ignore
        description="Number of times the word 'like' is used in the response"
    )


class LikeCount(Rubric):
    """Counts how many times the word 'like' is used in the output text."""

    @property
    def name(self) -> str:
        return "example.LikeCount"

    @property
    @schema_function(arrow_schema(LikeCountScoredItem))
    def schema(self) -> pyarrow.Schema:
        """The PyArrow schema of the output of applying the Rubric."""

    def apply(
        self, task_data: pyarrow.dataset.Dataset, predictions: pyarrow.dataset.Dataset
    ) -> Iterable[pyarrow.RecordBatch]:
        for b in predictions.to_batches(
            columns=["_index_", "_replication_", "responses"]
        ):
            batch = []
            for item in b.to_pylist():
                index = item["_index_"]
                replication = item["_replication_"]
                text = item["responses"][0]["text"]
                words = [w.lower() for w in text.split()]
                count = words.count("like")
                batch.append(
                    LikeCountScoredItem(
                        _index_=index, _replication_=replication, likeCount=count
                    ).dict()
                )
            yield pyarrow.RecordBatch.from_pylist(batch, schema=self.schema)
