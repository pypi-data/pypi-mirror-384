# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

# mypy: disable-error-code="import-untyped"
import sys
from typing import Iterable

import pyarrow
import pydantic

from dyff.schema.base import int32
from dyff.schema.dataset import ReplicatedItem
from dyff.schema.dataset.arrow import arrow_schema


class BlurstCountScoredItem(ReplicatedItem):
    blurstCount: int32() = pydantic.Field(  # type: ignore
        description="Number of times the word 'blurst' is used in the response."
    )
    cromulent: int32() = pydantic.Field(  # type: ignore
        description="Whether the text is cromulent."
    )
    embiggen: str = pydantic.Field(description="Which man to embiggen.")


def blurst_count(
    args: dict[str, str],
    *,
    dataset: pyarrow.dataset.Dataset,
    outputs: pyarrow.dataset.Dataset,
) -> Iterable[pyarrow.RecordBatch]:
    print("stdout message")
    print("stderr message", file=sys.stderr)

    embiggen_arg = args["embiggen"]
    schema = arrow_schema(BlurstCountScoredItem)

    cromulence = {}
    for b in dataset.to_batches(columns=["_index_", "text"]):
        for item in b.to_pylist():
            cromulent = 1 if item["text"].startswith("It was the best of times,") else 0
            cromulence[item["_index_"]] = cromulent

    for b in outputs.to_batches(columns=["_index_", "_replication_", "responses"]):
        batch = []
        for item in b.to_pylist():
            index = item["_index_"]
            replication = item["_replication_"]
            text = item["responses"][0]["text"]
            words = [w.lower() for w in text.split()]
            count = words.count("blurst")
            batch.append(
                BlurstCountScoredItem(
                    _index_=index,
                    _replication_=replication,
                    blurstCount=count,
                    cromulent=cromulence[index],
                    embiggen=embiggen_arg,
                ).dict()
            )
        yield pyarrow.RecordBatch.from_pylist(batch, schema=schema)  # type: ignore[attr-defined]


def raise_error(
    args: dict[str, str],
    *,
    dataset: pyarrow.dataset.Dataset,
    outputs: pyarrow.dataset.Dataset,
) -> Iterable[pyarrow.RecordBatch]:
    print("stdout message")
    print("stderr message", file=sys.stderr)
    raise RuntimeError("deliberate error")
