# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

# mypy: disable-error-code="import-untyped"
import abc
import random
import re
from typing import Any, Iterable, Optional

import pyarrow
import pydantic

from dyff.schema import ids
from dyff.schema.adapters import Adapter
from dyff.schema.dataset import arrow
from dyff.schema.dataset.text import Text
from dyff.schema.platform import DataSchema, DyffSchemaBaseModel, InferenceInterface


class InferenceServiceMock(abc.ABC):
    @property
    @abc.abstractmethod
    def schema(self) -> DataSchema:
        """The schema of the inference outputs."""
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def interface(self) -> InferenceInterface:
        """The inference interface spec."""
        raise NotImplementedError()

    @abc.abstractmethod
    def infer(self, endpoint: str, request: dict[str, Any]) -> list[dict[str, Any]]:
        """Make an inference on ``request`` using the specified simulated ``endpoint``.

        :param endpoint: The simulated HTTP endpoint to call.
        :param request: The inference input request.
        :returns: The inference output.
        """
        raise NotImplementedError()


class InferenceSessionClientMock:
    """A client used for making inference requests to a running
    :class:`~dyff.schema.platform.InferenceSession` backed by an
    :class:`InferenceServiceMock`.

    Emulates the interface of :py:class:`dyff.client.InferenceSessionClient`.

    .. note::

        Do not instantiate this class. Create an instance using
        :meth:`inferencesessions.client() <dyff.audit.local.platform._InferenceSessions.client>`.
    """

    def __init__(
        self,
        service: InferenceServiceMock,
        *,
        inference_endpoint: str,
        input_adapter: Optional[Adapter] = None,
        output_adapter: Optional[Adapter] = None,
    ):
        self._service = service
        self._inference_endpoint = inference_endpoint
        self._input_adapter = input_adapter
        self._output_adapter = output_adapter

    def infer(self, body: dict[str, Any]) -> list[dict[str, Any]]:
        """Make an inference request.

        The input and output are arbitrary JSON objects. The required format depends on
        the endpoint and input/output adapters specified when creating the inference
        client.

        :param body: A JSON object containing the inference input.
        :returns: A JSON object containing the inference output.
        """

        def once(x):
            if isinstance(x, list):
                yield from x
            else:
                yield x

        adapted_input = once(body)
        if self._input_adapter is not None:
            adapted_input = self._input_adapter(adapted_input)

        request_body = None
        for i, x in enumerate(adapted_input):
            if i > 0:
                raise ValueError("adapted input should contain exactly one element")
            request_body = x
        if request_body is None:
            raise ValueError("adapted input should contain exactly one element")

        json_response = self._service.infer(
            self._service.interface.endpoint, request_body
        )
        adapted_response = once(json_response)
        if self._output_adapter is not None:
            adapted_response = self._output_adapter(adapted_response)
        return list(adapted_response)

    def run_evaluation(
        self,
        input_dataset: pyarrow.dataset.Dataset,
        *,
        id: str,
        replications: int = 1,
    ) -> Iterable[pyarrow.RecordBatch]:
        """Run inference on an entire Arrow dataset, yielding a dataset of outputs.

        :param input_dataset: An Arrow dataset containing input instances. :keyword id:
            An "id" for the evaluation; needed to generate replication IDs. :keyword
            replications: The number of replications to run.
        :returns: The inference outputs, as a stream of batches.
        """
        interface = self._service.interface
        replication_ids = [ids.replication_id(id, i) for i in range(replications)]
        feature_schema = arrow.decode_schema(interface.outputSchema.arrowSchema)

        def output_generator() -> Iterable[pyarrow.RecordBatch]:
            for input_batch in input_dataset.to_batches():
                output_batch: list[dict[str, Any]] = []
                for item in input_batch.to_pylist():
                    index = item["_index_"]
                    for replication in replication_ids:
                        responses = self.infer(item)

                        for i, response in enumerate(responses):
                            response["_response_index_"] = i
                        response_record = {
                            "_replication_": replication,
                            "_index_": index,
                            "responses": responses,
                        }
                        output_batch.append(response_record)
                yield pyarrow.RecordBatch.from_pylist(  # type: ignore[attr-defined]
                    output_batch, schema=feature_schema
                )

        yield from output_generator()


class TextCompletionOutputSchema(DyffSchemaBaseModel):
    text: list[str] = pydantic.Field(
        default_factory=list, description="Text completions"
    )


class TextCompletion(InferenceServiceMock):
    """Simulates a "text completion" service.

    Endpoints:

        ``generate``
            Appends additional "generated" text to the input. Expects the input
            to have a field called ``"text"`` containing a ``str``.
    """

    def __init__(self):
        self._schema = DataSchema.make_output_schema(Text)
        self._num_responses = 2

    @property
    def schema(self) -> DataSchema:
        return self._schema

    @property
    def interface(self) -> InferenceInterface:
        return InferenceInterface(endpoint="generate", outputSchema=self.schema)

    def infer(self, endpoint: str, request: dict[str, Any]) -> list[dict[str, Any]]:
        if endpoint != "generate":
            raise ValueError(f"unknown endpoint '{endpoint}'")
        return self.generate(request)

    def generate(self, x: dict[str, Any]) -> list[dict[str, Any]]:
        text = x["text"]

        responses = []
        for i in range(self._num_responses):
            c = random.randrange(5)
            if c == 0:
                response = " I'm sorry, Dave. I'm afraid I can't do that."
            elif c == 1:
                response = " All work and no play makes Jack a dull boy."
            elif c == 2:
                prompt_words: list[str] = re.split(r"\s", text.strip())
                if len(prompt_words) > 0 and random.randrange(2):
                    n = min(len(prompt_words), 3)
                    echo = " ".join(w.upper() for w in prompt_words[-n:])
                    response = f" You should write a book, Fry! People need to know about the {echo}."
                else:
                    response = "POETIC IMAGE #35 NOT FOUND."

            elif c == 3:
                response = " it was the worst of times."
            else:
                response = " it was the blurst of times."
            responses.append(response)
        return [{"text": text + response} for response in responses]
