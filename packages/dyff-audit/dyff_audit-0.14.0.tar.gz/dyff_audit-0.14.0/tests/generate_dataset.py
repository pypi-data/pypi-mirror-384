# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

import random

import pyarrow
import pydantic

from dyff.schema.dataset import Item, arrow


class Text(Item):
    text: str = pydantic.Field(description="Text data")


def main():
    num_rows = 10_000
    words_per_row = 10
    batch_size = 100
    arrow_schema = arrow.arrow_schema(Text)

    with open("tests/words.txt", "r") as fin:
        words = fin.readlines()

    def g():
        batch = []
        for i in range(num_rows):
            text = " ".join(random.choices(words, k=words_per_row))
            batch.append(Text(_index_=i, text=text).model_dump(mode="python"))
            if len(batch) == batch_size:
                yield pyarrow.RecordBatch.from_pylist(batch, schema=arrow_schema)
                batch = []
        if batch:
            yield pyarrow.RecordBatch.from_pylist(batch, schema=arrow_schema)

    arrow.write_dataset(
        g(), output_path="tests/data/dataset", feature_schema=arrow_schema
    )


if __name__ == "__main__":
    main()
