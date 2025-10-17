# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

# mypy: disable-error-code="import-untyped"
import sys
from typing import Iterable

import pyarrow
import pydantic

from dyff.audit.scoring import Rubric
from dyff.schema.base import int32
from dyff.schema.dataset import ReplicatedItem
from dyff.schema.dataset.arrow import arrow_schema, schema_function


class BlurstCountScoredItem(ReplicatedItem):
    blurstCount: int32() = pydantic.Field(  # type: ignore
        description="Number of times the word 'blurst' is used in the response"
    )


class BlurstCount(Rubric):
    @property
    def name(self) -> str:
        return "dyff.fake.rubric.BlurstCount"

    @property
    @schema_function(arrow_schema(BlurstCountScoredItem))
    def schema(self) -> pyarrow.Schema:
        """The PyArrow schema of the output of applying the Rubric."""

    def apply(
        self, task_data: pyarrow.dataset.Dataset, predictions: pyarrow.dataset.Dataset
    ) -> Iterable[pyarrow.RecordBatch]:
        print("stdout message")
        print("stderr message", file=sys.stderr)

        for b in predictions.to_batches(
            columns=["_index_", "_replication_", "responses"]
        ):
            batch = []
            for item in b.to_pylist():
                index = item["_index_"]
                replication = item["_replication_"]
                text = item["responses"][0]["text"]
                words = [w.lower() for w in text.split()]
                count = words.count("blurst")
                batch.append(
                    BlurstCountScoredItem(
                        _index_=index, _replication_=replication, blurstCount=count
                    ).dict()
                )
            yield pyarrow.RecordBatch.from_pylist(batch, schema=self.schema)


class RaiseError(Rubric):
    @property
    def name(self) -> str:
        return "dyff.fake.rubric.RaiseError"

    @property
    @schema_function(arrow_schema(BlurstCountScoredItem))
    def schema(self) -> pyarrow.Schema:
        """The PyArrow schema of the output of applying the Rubric."""

    def apply(
        self, task_data: pyarrow.dataset.Dataset, predictions: pyarrow.dataset.Dataset
    ) -> Iterable[pyarrow.RecordBatch]:
        print("stdout message")
        print("stderr message", file=sys.stderr)
        raise RuntimeError("deliberate error")
