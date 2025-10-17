# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

# mypy: disable-error-code="import-untyped"
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Optional

import pyarrow

from dyff.client import Client
from dyff.schema import ids
from dyff.schema.dataset import arrow
from dyff.schema.platform import InferenceSession

from .scoring import Rubric


def local_evaluation(
    client: Client,
    session: InferenceSession,
    *,
    input_dataset_path: Path | str,
    output_dataset_path: Path | str,
    replications: int = 1,
    id: Optional[str] = None,
) -> str:
    """Emulate an Evaluation workflow by feeding data from a local Arrow dataset to an
    InferenceSession running on the Dyff platform.

    .. deprecated:: 0.3.3

        Use :py:class:`~dyff.audit.local.DyffLocalPlatform` to get similar functionality

    The output dataset will have the same schema as the outputs from an
    Evaluation run on the platform, including fields added by the platform
    -- ``_index_``, ``_replication_``, etc.

    The input dataset must be compatible with the canonical Dyff Platform
    dataset schema for the appropriate inference task.

    :param client: A Dyff API client with permission to call the
        ``inferencesessions.token()`` and ``inferencesessions.client()``
        endpoints on the given ``InferenceSession``.
    :type client: dyff.client.Client
    :param session: A record describing a running ``InferenceSession``.
    :type session: dyff.schema.platform.InferenceSession
    :keyword input_dataset_path: The root directory of an Arrow dataset on
        the local filesystem.
    :type input_dataset_path: Path | str
    :keyword output_dataset_path: The directory where the Arrow output dataset
        should be created. A subdirectory named with the ID of the simulated
        evaluation will be created.
    :type output_dataset_path: Path | str
    :keyword replications: The number of replications to run. Equivalent to the
        ``EvaluationCreateRequest.replications`` parameter.
    :type replications: int
    :keyword id: If specified, use this ID for the evaluation. Otherwise,
        generate a new ID.
    :type id: str
    :returns: An ID for the simulated evaluation, either the ID provided as
        an argument, or a newly-generated one. This will not correspond to
        an entity in the Dyff datastore, but it can be used to derive the IDs
        of replications in the output dataset.
    :rtype: str
    """
    session_token = client.inferencesessions.token(session.id)
    interface = session.inferenceService.interface
    inference_client = client.inferencesessions.client(
        session.id, session_token, interface=interface
    )
    evaluation_id = id or ids.generate_entity_id()
    replication_ids = [
        ids.replication_id(evaluation_id, i) for i in range(replications)
    ]
    feature_schema = arrow.decode_schema(interface.outputSchema.arrowSchema)
    partition_schema = arrow.subset_schema(feature_schema, ["_replication_"])

    def output_generator() -> Iterable[pyarrow.RecordBatch]:
        input_dataset = arrow.open_dataset(str(input_dataset_path))
        for input_batch in input_dataset.to_batches():
            output_batch: list[dict[str, Any]] = []
            for item in input_batch.to_pylist():
                index = item["_index_"]
                for replication in replication_ids:
                    responses = inference_client.infer(item)
                    for i, response in enumerate(responses):
                        response["_response_index_"] = i
                    response_record = {
                        "_replication_": replication,
                        "_index_": index,
                        "responses": responses,
                    }
                    output_batch.append(response_record)
            yield pyarrow.RecordBatch.from_pylist(output_batch, schema=feature_schema)  # type: ignore

    evaluation_output_path = Path(output_dataset_path) / evaluation_id
    evaluation_output_path.mkdir()
    arrow.write_dataset(
        output_generator(),
        output_path=str(evaluation_output_path),
        feature_schema=feature_schema,
        partition_schema=partition_schema,
    )

    return evaluation_id


def local_report(
    rubric: Rubric,
    *,
    input_dataset_path: Path | str,
    output_dataset_path: Path | str,
    report_dataset_path: Path | str,
):
    """Emulate a Report workflow on local data.

    .. deprecated:: 0.3.3

        Use :py:class:`~dyff.audit.local.DyffLocalPlatform` to get similar functionality

    You will need the Arrow datasets of inputs and outputs to an Evaluation
    workflow. You can emulate an Evaluation locally with ``local_evaluation()``.

    :param rubric: The Rubric to apply.
    :type rubric: dyff.audit.scoring.Rubric
    :keyword input_dataset_path: The root directory of the Arrow dataset
        containing the inputs to an evaluation.
    :type input_dataset_path: Path | str
    :keyword output_dataset_path: The root directory of the Arrow dataset
        containing the outputs of the evaluation.
    :type output_dataset_path: Path | str
    :keyword report_dataset_path: The directory where the Arrow dataset of
        report outputs should be created. A subdirectory named with the ID of
        the simulated report will be created.
    :type report_dataset_path: Path | str
    :returns: An ID for the simulated report. This will not correspond to
        an entity in the Dyff datastore.
    :rtype: str
    """

    def output_generator() -> Iterable[pyarrow.RecordBatch]:
        input_dataset = arrow.open_dataset(str(input_dataset_path))
        output_dataset = arrow.open_dataset(str(output_dataset_path))
        yield from rubric.apply(input_dataset, output_dataset)

    report_id = ids.generate_entity_id()
    report_output_path = Path(report_dataset_path) / report_id
    report_output_path.mkdir()
    arrow.write_dataset(
        output_generator(),
        output_path=str(report_output_path),
        feature_schema=rubric.schema,
    )

    return report_id


__all__ = [
    "local_evaluation",
    "local_report",
]
