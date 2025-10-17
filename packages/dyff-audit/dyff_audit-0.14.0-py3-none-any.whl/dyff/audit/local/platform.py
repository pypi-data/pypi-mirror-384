# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

# mypy: disable-error-code="import-untyped"
from __future__ import annotations

import base64
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generic, Optional, Type, TypeVar, Union

import ruamel.yaml

from dyff.client import Client, HttpResponseError, _apigroups
from dyff.client._apigroups import SchemaObject, _parse_schema_object
from dyff.schema import ids
from dyff.schema.adapters import Adapter, create_pipeline
from dyff.schema.dataset import arrow, binary
from dyff.schema.platform import (
    Analysis,
    AnalysisData,
    Artifact,
    ContainerImageSource,
    DataSchema,
    Dataset,
    Digest,
    Documentation,
    DyffEntity,
    DyffSchemaBaseModel,
    Entities,
    EntityStatus,
    Evaluation,
    ForeignInferenceService,
    ForeignMethod,
    ForeignModel,
    InferenceInterface,
    InferenceService,
    InferenceSession,
    InferenceSessionAndToken,
    InferenceSessionSpec,
    Measurement,
    Method,
    Model,
    Module,
    Report,
    Resources,
    SafetyCase,
    Score,
)
from dyff.schema.requests import (
    AnalysisCreateRequest,
    DatasetCreateRequest,
    DocumentationEditRequest,
    EvaluationCreateRequest,
    InferenceSessionCreateRequest,
    MethodCreateRequest,
    ModelCreateRequest,
    ModuleCreateRequest,
    ReportCreateRequest,
)

from .. import dynamic_import
from .._internal import fqn, upcast
from ..analysis import run_analysis, run_report
from ..workflows import local_evaluation
from . import mocks

_EntityT = TypeVar(
    "_EntityT",
    Dataset,
    Evaluation,
    InferenceService,
    InferenceSession,
    Measurement,
    Method,
    Model,
    Module,
    Report,
    SafetyCase,
)
_EntityOpsT = TypeVar(
    "_EntityOpsT",
    _apigroups._Datasets,
    _apigroups._Evaluations,
    _apigroups._InferenceServices,
    _apigroups._InferenceSessions,
    _apigroups._Measurements,
    _apigroups._Methods,
    _apigroups._Models,
    _apigroups._Modules,
    _apigroups._Reports,
    _apigroups._SafetyCases,
)


def _namespaced_id(e: DyffEntity) -> str:
    return f"{Resources.for_kind(Entities(e.kind)).value}/{e.id}"


class _Common(Generic[_EntityT, _EntityOpsT]):
    def __init__(
        self,
        platform: DyffLocalPlatform,
        *,
        entity_kind: Entities,
        entity_type: Type[_EntityT],
        remote_ops: Optional[_EntityOpsT],
    ):
        self._platform = platform
        self._entity_kind = entity_kind
        self._entity_type: Type[_EntityT] = entity_type
        self._remote_ops: Optional[_EntityOpsT] = remote_ops

    def get(self, id: str) -> Optional[_EntityT]:
        """Get the database record associated with an entity."""
        filename = f".{self._entity_kind.value.lower()}.json"
        try:
            file = self._platform.entity_path(id) / filename
            return self._entity_type.parse_file(file)
        except FileNotFoundError:
            return None

    def delete(self, id: str) -> None:
        """Set the entity's status to ``"Deleted"``."""
        entity = self.get(id)
        if entity is None:
            raise HttpResponseError(id, status_code=404)
        entity.status = EntityStatus.deleted
        self._platform._commit(entity)

    def fetch(self, id: str) -> _EntityT:
        """Fetch an entity and all associated artifacts from the remote Dyff instance
        associated with the remote client that was provided to the ``DyffLocalPlatform``
        constructor."""
        if not self._remote_ops:
            raise AssertionError(".fetch() requires a remote client")
        entity = self._remote_ops.get(id)
        if entity is None:
            raise KeyError(f"no remote entity with ID {id}")
        if isinstance(self._remote_ops, _apigroups._ArtifactsMixin):
            self._remote_ops.download(id, self._platform.entity_path(id))
        self._platform._commit(entity)
        return entity  # type: ignore

    def purge(self, id: str) -> None:
        """Remove an entity and all associated artifacts from local storage."""
        entity = self.get(id)
        if entity is None:
            return
        shutil.rmtree(self._platform.entity_path(id))


class _DocumentationMixin:
    _platform: "DyffLocalPlatform"

    def documentation(self, id: str) -> Documentation:
        """Get the documentation associated with an entity."""
        return self._platform.documentation.get(id)

    def edit_documentation(
        self, id: str, edit_request: SchemaObject[DocumentationEditRequest]
    ) -> Documentation:
        """Edit the documentation associated with an entity."""
        return self._platform.documentation.edit(id, edit_request)


class _Datasets(_Common[Dataset, _apigroups._Datasets], _DocumentationMixin):
    def __init__(self, platform: DyffLocalPlatform):
        super().__init__(
            platform,
            entity_kind=Entities.Dataset,
            entity_type=Dataset,
            remote_ops=platform.remote.datasets if platform.remote else None,
        )

    def create(self, request: SchemaObject[DatasetCreateRequest]) -> Dataset:
        """Create a new entity.

        :param request: The entity create request specification.
        :return: A full entity spec with its .id and other system properties set
        """
        id = ids.generate_entity_id()
        request = _parse_schema_object(DatasetCreateRequest, request)
        dataset_dict = request.dict()
        dataset_dict["id"] = id
        dataset_dict["account"] = self._platform.account
        dataset_dict["status"] = EntityStatus.ready
        dataset_dict["creationTime"] = datetime.now(timezone.utc)
        dataset = Dataset.parse_obj(dataset_dict)

        cache_dir = self._platform.entity_path(id)
        cache_dir.mkdir()
        with open(cache_dir / ".dataset.json", "w") as fout:
            fout.write(dataset.json())
        return dataset

    def create_arrow_dataset(
        self, dataset_directory: str, *, account: str, name: str
    ) -> Dataset:
        """Create a Dataset resource describing an existing Arrow dataset.

        Internally, constructs a ``DatasetCreateRequest`` using information
        obtained from the Arrow dataset, then calls ``create()`` with the
        constructed request.

        Typical usage::

            dataset = client.datasets.create_arrow_dataset(dataset_directory, ...)
            client.datasets.upload_arrow_dataset(dataset, dataset_directory)

        :param dataset_directory: The root directory of the Arrow dataset.
        :type dataset_directory: str
        :keyword account: The account that will own the Dataset resource.
        :type account: str
        :keyword name: The name of the Dataset resource.
        :type name: str
        :returns: The complete Dataset resource.
        :rtype: Dataset
        """
        dataset_path = Path(dataset_directory)
        ds = arrow.open_dataset(str(dataset_path))
        file_paths = list(ds.files)  # type: ignore[attr-defined]
        artifact_paths = [
            str(Path(file_path).relative_to(dataset_path)) for file_path in file_paths
        ]
        artifacts = [
            Artifact(
                kind="parquet",
                path=artifact_path,
                digest=Digest(
                    md5=binary.encode(binary.file_digest("md5", file_path)),
                ),
            )
            for file_path, artifact_path in zip(file_paths, artifact_paths)
        ]
        schema = DataSchema(
            arrowSchema=arrow.encode_schema(ds.schema),
        )
        request = DatasetCreateRequest(
            account=account,
            name=name,
            artifacts=artifacts,
            schema=schema,
        )
        return self.create(request)

    def upload_arrow_dataset(self, dataset: Dataset, dataset_directory: str) -> None:
        """Uploads the data files in an existing Arrow dataset for which a Dataset
        resource has already been created.

        Typical usage::

            dataset = client.datasets.create_arrow_dataset(dataset_directory, ...)
            client.datasets.upload_arrow_dataset(dataset, dataset_directory)

        :param dataset: The Dataset resource for the Arrow dataset.
        :type dataset: Dataset
        :param dataset_directory: The root directory of the Arrow dataset.
        :type dataset_directory: str
        """
        if any(artifact.digest.md5 is None for artifact in dataset.artifacts):
            raise ValueError("artifact.digest.md5 must be set for all artifacts")
        for artifact in dataset.artifacts:
            assert artifact.digest.md5 is not None
            file_path = Path(dataset_directory) / artifact.path
            cache_path = self._platform.storage_root / dataset.id / artifact.path
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "rb") as fin:
                with open(cache_path, "wb") as fout:
                    fout.write(fin.read())


class _Evaluations(_Common[Evaluation, _apigroups._Evaluations], _DocumentationMixin):
    def __init__(self, platform: DyffLocalPlatform):
        super().__init__(
            platform,
            entity_kind=Entities.Evaluation,
            entity_type=Evaluation,
            remote_ops=platform.remote.evaluations if platform.remote else None,
        )

    def create(self, request: SchemaObject[EvaluationCreateRequest]) -> Evaluation:
        """Create a new entity.

        :param request: The entity create request specification.
        :return: A full entity spec with its .id and other system properties set
        """
        id = ids.generate_entity_id()
        request = _parse_schema_object(EvaluationCreateRequest, request)
        dataset = self._platform.datasets.get(request.dataset)
        if dataset is None:
            raise HttpResponseError(f"datasets/{request.dataset}", status_code=404)

        evaluation_dict: dict[str, Any] = {}
        evaluation_dict["id"] = id
        evaluation_dict["account"] = request.account
        evaluation_dict["dataset"] = request.dataset
        evaluation_dict["replications"] = request.replications

        if request.inferenceSessionReference is not None:
            session = self._platform.inferencesessions.get(
                request.inferenceSessionReference
            )
            if session is None:
                raise HttpResponseError(
                    f"inferencesessions/{request.inferenceSessionReference}",
                    status_code=404,
                )
            token = self._platform.inferencesessions.token(session.id)
            evaluation_dict["inferenceSessionReference"] = (
                request.inferenceSessionReference
            )
        elif request.inferenceSession is not None:
            service_id = request.inferenceSession.inferenceService
            session_request = InferenceSessionCreateRequest(
                account=request.account, inferenceService=service_id
            )
            session_and_token = self._platform.inferencesessions.create(session_request)
            session = session_and_token.inferencesession
            token = session_and_token.token
        else:
            raise ValueError(
                "must specify one of {inferenceSession, inferenceSessionReference}"
            )

        evaluation_dict["inferenceSession"] = upcast(
            InferenceSessionSpec, session.dict()
        ).dict()
        evaluation_dict["creationTime"] = datetime.now(timezone.utc)
        # TODO: Actually check success / failure
        evaluation_dict["status"] = EntityStatus.complete
        evaluation = Evaluation.parse_obj(evaluation_dict)

        cache_dir = self._platform.entity_path(evaluation.id)
        cache_dir.mkdir()
        with open(cache_dir / ".evaluation.json", "w") as fout:
            fout.write(evaluation.json())

        inference_client = self._platform.inferencesessions.client(
            session.id, token, interface=session.inferenceService.interface
        )
        session.inferenceService.interface.outputSchema.arrowSchema

        input_dataset = arrow.open_dataset(str(self._platform.entity_path(dataset.id)))

        output_generator = inference_client.run_evaluation(
            input_dataset,
            replications=request.replications,
            id=evaluation.id,
        )
        arrow.write_dataset(
            output_generator,
            output_path=str(self._platform.entity_path(evaluation.id)),
            feature_schema=arrow.decode_schema(
                session.inferenceService.interface.outputSchema.arrowSchema
            ),
        )

        return evaluation

    def import_data(
        self,
        dataset_directory: Path | str,
        *,
        id: Optional[str] = None,
        evaluation_request: Optional[EvaluationCreateRequest] = None,
    ) -> Evaluation:
        """Imports existing data into the local cache under a newly-generated ID. Useful
        when you already have evaluation data and you want to make it available to other
        workflows using the local platform.

        :param dataset_directory: The root directory of the Arrow dataset.
        :type dataset_directory: str
        :returns: The ID of the imported data in the local platform.
        :rtype: str
        """
        dataset_path = Path(dataset_directory)
        ds = arrow.open_dataset(str(dataset_path))
        file_paths = list(ds.files)  # type: ignore[attr-defined]

        replications = set()
        for row in ds.to_table().to_pylist():
            replications.add(row["_replication_"])

        evaluation_dict: dict[str, Any] = {}
        evaluation_dict["id"] = id or ids.generate_entity_id()
        evaluation_dict["account"] = (
            evaluation_request and evaluation_request.account
        ) or ids.null_id()
        evaluation_dict["dataset"] = (
            evaluation_request and evaluation_request.dataset
        ) or ids.null_id()
        evaluation_dict["replications"] = len(replications)

        if evaluation_request and evaluation_request.inferenceSession:
            service_id = evaluation_request.inferenceSession.inferenceService
        else:
            service_id = ids.null_id()
        session_spec = InferenceSessionSpec(
            inferenceService=ForeignInferenceService(
                id=service_id,
                name="",
                account=ids.null_id(),
                interface=InferenceInterface(
                    endpoint="",
                    outputSchema=DataSchema(arrowSchema=arrow.encode_schema(ds.schema)),
                ),
            )
        )
        evaluation_dict["inferenceSession"] = session_spec.dict()
        evaluation_dict["creationTime"] = datetime.now(timezone.utc)
        # TODO: actually check success / failure
        evaluation_dict["status"] = EntityStatus.complete
        evaluation = Evaluation.parse_obj(evaluation_dict)

        cache_dir = self._platform.entity_path(evaluation.id)
        cache_dir.mkdir()
        with open(cache_dir / ".evaluation.json", "w") as fout:
            fout.write(evaluation.json())

        artifact_paths = [
            str(Path(file_path).relative_to(dataset_path)) for file_path in file_paths
        ]
        artifacts = [
            Artifact(
                kind="parquet",
                path=artifact_path,
                digest=Digest(
                    md5=binary.encode(binary.file_digest("md5", file_path)),
                ),
            )
            for file_path, artifact_path in zip(file_paths, artifact_paths)
        ]
        for artifact in artifacts:
            assert artifact.digest.md5 is not None
            file_path = Path(dataset_directory) / artifact.path
            cache_path = self._platform.entity_path(evaluation.id) / artifact.path
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "rb") as fin:
                with open(cache_path, "wb") as fout:
                    fout.write(fin.read())

        return evaluation

    def local_evaluation(self, *, dataset: str, inferencesession: str) -> str:
        """Emulate an Evaluation workflow by feeding data from a local Dataset to an
        InferenceSession running on the Dyff platform.

        The output dataset will have the same schema as the outputs from an
        Evaluation run on the platform, including fields added by the platform
        -- ``_index_``, ``_replication_``, etc.

        The input dataset must be compatible with the canonical Dyff Platform
        dataset schema for the appropriate inference task.

        :param dataset: The ID of a ``Dataset`` in *local storage*.
        :type dataset: str
        :param inferencesession: The ID of an ``InferenceSession`` that is
            *already running* on the *remote Dyff instance*.
        :type inferencesession: ID
        :returns: An ID for the evaluation. This will not correspond to
            an entity in the the local or remote datastores, but it can be used
            to derive the IDs of replications in the output dataset.
        :rtype: str
        """
        client = self._platform._require_client()
        session = client.inferencesessions.get(inferencesession)
        id = ids.generate_entity_id()
        return local_evaluation(
            client,
            session,
            input_dataset_path=self._platform.entity_path(dataset),
            # workflows.local_evaluation() creates an /id subdirectory for the output
            output_dataset_path=self._platform.storage_root,
            id=id,
        )


class _InferenceServices(
    _Common[InferenceService, _apigroups._InferenceServices], _DocumentationMixin
):
    def __init__(self, platform: DyffLocalPlatform):
        super().__init__(
            platform,
            entity_kind=Entities.InferenceService,
            entity_type=InferenceService,
            remote_ops=platform.remote.inferenceservices if platform.remote else None,
        )

    def create_mock(
        self,
        mock_type: Type[mocks.InferenceServiceMock],
        *,
        account: str,
        id: Optional[str] = None,
        model: Optional[str] = None,
    ) -> InferenceService:
        """Create an InferenceService that uses a mock-up backend.

        The ``mock_type`` can be anything that implements the
        :py:class:`~dyff.audit.local.mocks.InferenceServiceMock` interface
        and is importable locally; you can implement and use your own
        mock services.

        :param mock_type: The type of the mock service implementation.
        :keyword account: The account that should own the InferenceService.
        :keyword id: Will be generated if not given.
        :keyword model: The ID of a model to associate with the service. Since
            this is a mock service, usually the model will also be a mock-up
            (i.e., the ``model.source.kind`` field will be
            :py:attr:`~dyff.schema.platform.ModelSourceKinds.Mock`).
        :return: A full entity spec with its .id and other system properties set
        """
        id = id or ids.generate_entity_id()
        model_spec = self._platform.models.get(model) if model else None

        mock = mock_type()
        service = InferenceService(
            account=account,
            id=id,
            name=".".join(fqn(mock_type)),
            model=upcast(ForeignModel, model_spec.dict()) if model_spec else None,
            interface=mock.interface,
            status=EntityStatus.ready,
            creationTime=datetime.now(timezone.utc),
        )
        self._platform._commit(service)

        return service


class _InferenceSessions(_Common[InferenceSession, _apigroups._InferenceSessions]):
    def __init__(self, platform: DyffLocalPlatform):
        super().__init__(
            platform,
            entity_kind=Entities.InferenceSession,
            entity_type=InferenceSession,
            remote_ops=platform.remote.inferencesessions if platform.remote else None,
        )

    def create(
        self, request: SchemaObject[InferenceSessionCreateRequest]
    ) -> InferenceSessionAndToken:
        """Create a new entity.

        :param request: The entity create request specification.
        :return: A full entity spec with its .id and other system properties set
        """
        request = _parse_schema_object(InferenceSessionCreateRequest, request)
        id = ids.generate_entity_id()

        service = self._platform.inferenceservices.get(request.inferenceService)
        if service is None:
            raise HttpResponseError(
                f"inferenceservices/{request.inferenceService}", status_code=404
            )

        session = InferenceSession(
            account=request.account,
            id=id,
            inferenceService=upcast(ForeignInferenceService, service.dict()),
            status=EntityStatus.admitted,
            creationTime=datetime.now(timezone.utc),
        )

        cache_dir = self._platform.entity_path(id)
        cache_dir.mkdir()
        with open(cache_dir / ".inferencesession.json", "w") as fout:
            fout.write(session.json())

        return InferenceSessionAndToken(inferencesession=session, token="dummy-token")

    def ready(self, id: str) -> bool:
        """Returns True if the session is ready to receive inference requests.

        :param id: The session ID
        :return: True if the session is ready to receive inference requests.
        """
        try:
            session = self.get(id)
            if session is None:
                raise HttpResponseError(f"inferencesessions/{id}", status_code=404)
            return session.status == EntityStatus.admitted
        except:
            return False

    def token(self, id: str, expires: Optional[datetime] = None) -> str:
        """Get an auth token allowing inference calls to the session.

        The local platform does not implement authorization, so this will be a "dummy"
        token.
        """
        return "dummy-token"

    def infer(
        self, id: str, endpoint: str, request: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Make an inference call to a mock-up inference session.

        :param id: The session ID
        :param endpoint: The endpoint to call
        :param request: The input data for inference
        :return: The inference output
        """
        session = self.get(id)
        if session is None:
            raise HttpResponseError(f"inferencesessions/{id}", status_code=404)
        mock: mocks.InferenceServiceMock = dynamic_import.instantiate(
            session.inferenceService.name
        )
        return mock.infer(endpoint, request)

    def client(
        self,
        session_id: str,
        token: str,
        *,
        interface: Optional[InferenceInterface] = None,
        endpoint: Optional[str] = None,
        input_adapter: Optional[Adapter] = None,
        output_adapter: Optional[Adapter] = None,
    ) -> mocks.InferenceSessionClientMock:
        """Create a mock-up inference session client.

        The token should be one returned either from
        ``inferencesessions.create()`` or from
        ``inferencesessions.token(session_id)``.

        The inference endpoint in the session must also be specified, either
        directly through the ``endpoint`` argument or by specifying an
        ``interface``. Specifying ``interface`` will also use the input and
        output adapters from the interface. You can also specify these
        separately in the ``input_adapter`` and ``output_adapter``. The
        non-``interface`` arguments override the corresponding values in
        ``interface`` if both are specified.

        :param session_id: The inference session to connect to
        :param token: An access token with permission to run inference against
            the session. The token is ignored because the local platform does
            not implement authorization.
        :param interface: The interface to the session. Either ``interface``
            or ``endpoint`` must be specified.
        :param endpoint: The inference endpoint in the session to call. Either
            ``endpoint`` or ``interface`` must be specified.
        :param input_adapter: Optional input adapter, applied to the input
            before sending it to the session. Will override the input adapter
            from ``interface`` if both are specified.
        :param output_adapter: Optional output adapter, applied to the output
            of the session before returning to the client. Will override the
            output adapter from ``interface`` if both are specified.
        :return: An mock-up inference client that makes inference calls to
            the specified session.
        """
        if interface is not None:
            inference_endpoint = endpoint or interface.endpoint
            if input_adapter is None:
                if interface.inputPipeline is not None:
                    input_adapter = create_pipeline(interface.inputPipeline)
            if output_adapter is None:
                if interface.outputPipeline is not None:
                    output_adapter = create_pipeline(interface.outputPipeline)

        session = self.get(session_id)
        if session is None:
            raise HttpResponseError(f"inferencesessions/{session_id}", status_code=404)
        service: mocks.InferenceServiceMock = dynamic_import.instantiate(
            session.inferenceService.name
        )
        return mocks.InferenceSessionClientMock(
            service,
            inference_endpoint=inference_endpoint,
            input_adapter=input_adapter,
            output_adapter=output_adapter,
        )


class _Measurements(_Common[Measurement, _apigroups._Measurements]):
    def __init__(self, platform: DyffLocalPlatform):
        super().__init__(
            platform,
            entity_kind=Entities.Measurement,
            entity_type=Measurement,
            remote_ops=platform.remote.measurements if platform.remote else None,
        )

    def create(self, request: SchemaObject[AnalysisCreateRequest]) -> Measurement:
        """Create a new entity.

        :param request: The entity create request specification.
        :return: A full entity spec with its .id and other system properties set
        """
        request = _parse_schema_object(AnalysisCreateRequest, request)
        id = ids.generate_entity_id()

        method_id = request.method
        method = self._platform.methods.get(method_id)
        if method is None:
            raise HttpResponseError(f"methods/{method_id}", status_code=404)

        # Create an entity representing the output of the Analysis
        measurement_spec = method.output.measurement
        if measurement_spec is None:
            raise ValueError("Method spec violates constraints")

        measurement = Measurement(
            account=request.account,
            id=id,
            creationTime=datetime.now(timezone.utc),
            status=EntityStatus.admitted,
            scope=request.scope,
            method=upcast(ForeignMethod, method.dict()),
            arguments=request.arguments,
            inputs=request.inputs,
            **measurement_spec.dict(),
        )
        self._platform._commit(measurement)

        analysis = upcast(Analysis, measurement.dict())
        # This fixes some things that YAML can't parse (like Enums)
        analysis_dict = json.loads(analysis.json())
        analysis_dict["id"] = id
        # Code expects a full k8s manifest
        # TODO: Should only pass the 'spec' part in the first place from
        # dyff-operator, but that requires figuring out how to manipulate YAML in Go
        analysis_dict = {"spec": analysis_dict}
        config_file = self._platform.entity_path(measurement.id) / ".analysis.yaml"
        yaml = ruamel.yaml.YAML()
        with open(config_file, "w") as fout:
            yaml.dump(analysis_dict, fout)

        try:
            run_analysis(
                method,
                storage_root=self._platform.storage_root,
                config_file=config_file,
            )
            measurement.status = EntityStatus.complete
        except Exception:
            measurement.status = EntityStatus.failed
        self._platform._commit(measurement)

        return measurement


class _Methods(_Common[Method, _apigroups._Methods], _DocumentationMixin):
    def __init__(self, platform: DyffLocalPlatform):
        super().__init__(
            platform,
            entity_kind=Entities.Method,
            entity_type=Method,
            remote_ops=platform.remote.methods if platform.remote else None,
        )

    def create(self, request: SchemaObject[MethodCreateRequest]) -> Method:
        """Create a new entity.

        :param request: The entity create request specification.
        :return: A full entity spec with its .id and other system properties set
        """
        request = _parse_schema_object(MethodCreateRequest, request)
        id = ids.generate_entity_id()
        method_dict = request.dict()
        method_dict["id"] = id
        method_dict["account"] = self._platform.account
        method_dict["status"] = EntityStatus.ready
        method_dict["creationTime"] = datetime.now(timezone.utc)

        # Set default analysis image if not provided (matches dyff-api logic)
        if not method_dict.get("analysisImage"):
            # Check environment variable first, fall back to specific version with digest
            default_image_ref = os.getenv(
                "DYFF_API_DEFAULT_ANALYSIS_IMAGE",
                # 0.8.0 - includes schema tolerance fixes for custom analysis image feature
                "registry.gitlab.com/dyff/workflows/run-report@sha256:36b524c0f253014afe5b2f85931179e1fbfc7f540cfe5b47306718f1ff2ccf8b",
            )
            # Parse image reference into ContainerImageSource
            if "@" in default_image_ref:
                host_and_name, digest = default_image_ref.split("@", 1)
                if "/" in host_and_name:
                    parts = host_and_name.split("/", 1)
                    host = parts[0]
                    name = parts[1]
                else:
                    host = ""
                    name = host_and_name
                method_dict["analysisImage"] = ContainerImageSource(
                    host=host, name=name, digest=digest
                )

        method = Method.parse_obj(method_dict)

        self._platform._commit(method)
        return method


class _Models(_Common[Model, _apigroups._Models], _DocumentationMixin):
    def __init__(self, platform: DyffLocalPlatform):
        super().__init__(
            platform,
            entity_kind=Entities.Model,
            entity_type=Model,
            remote_ops=platform.remote.models if platform.remote else None,
        )

    def create(self, request: SchemaObject[ModelCreateRequest]) -> Model:
        """Create a new entity.

        :param request: The entity create request specification.
        :return: A full entity spec with its .id and other system properties set
        """
        request = _parse_schema_object(ModelCreateRequest, request)
        id = ids.generate_entity_id()
        model_dict = request.dict()
        model_dict["id"] = id
        model_dict["account"] = self._platform.account
        model_dict["status"] = EntityStatus.ready
        model_dict["creationTime"] = datetime.now(timezone.utc)
        model = Model.parse_obj(model_dict)

        self._platform._commit(model)
        return model


class _Modules(_Common[Module, _apigroups._Modules], _DocumentationMixin):
    def __init__(self, platform: DyffLocalPlatform):
        super().__init__(
            platform,
            entity_kind=Entities.Module,
            entity_type=Module,
            remote_ops=platform.remote.modules if platform.remote else None,
        )

    def create(self, request: SchemaObject[ModuleCreateRequest]) -> Module:
        """Create a new entity.

        :param request: The entity create request specification.
        :return: A full entity spec with its .id and other system properties set
        """
        request = _parse_schema_object(ModuleCreateRequest, request)
        id = ids.generate_entity_id()
        module_dict = request.dict()
        module_dict["id"] = id
        module_dict["account"] = self._platform.account
        module_dict["status"] = EntityStatus.ready
        module_dict["creationTime"] = datetime.now(timezone.utc)
        module = Module.parse_obj(module_dict)

        cache_dir = self._platform.entity_path(id)
        cache_dir.mkdir()
        with open(cache_dir / ".module.json", "w") as fout:
            fout.write(module.json())
        return module

    def create_package(
        self, package_directory: str, *, account: str, name: str
    ) -> Module:
        """Create a Module resource describing a package structured as a directory tree.

        Internally, constructs a ``ModuleCreateRequest`` using information
        obtained from the directory tree, then calls ``create()`` with the
        constructed request.

        Typical usage::

            module = client.modules.create_package(package_directory, ...)
            client.modules.upload_package(module, package_directory)

        :param package_directory: The root directory of the package.
        :type package_directory: str
        :keyword account: The account that will own the Module resource.
        :type account: str
        :keyword name: The name of the Module resource.
        :type name: str
        :returns: The complete Module resource.
        :rtype: Module
        """
        package_root = Path(package_directory)
        file_paths = [path for path in package_root.rglob("*") if path.is_file()]
        if not file_paths:
            raise ValueError(f"package_directory is empty: {package_directory}")
        artifact_paths = [
            str(Path(file_path).relative_to(package_root)) for file_path in file_paths
        ]
        artifacts = [
            Artifact(
                # FIXME: Is this a useful thing to do? It's redundant with
                # information in 'path'. Maybe it should just be 'code' or
                # something generic.
                kind="".join(file_path.suffixes),
                path=artifact_path,
                digest=Digest(
                    md5=binary.encode(binary.file_digest("md5", str(file_path))),
                ),
            )
            for file_path, artifact_path in zip(file_paths, artifact_paths)
        ]
        request = ModuleCreateRequest(
            account=account,
            name=name,
            artifacts=artifacts,
        )
        return self.create(request)

    def upload_package(self, module: Module, package_directory: str) -> None:
        """Uploads the files in a package directory for which a Module resource has
        already been created.

        Typical usage::

            module = client.modules.create_package(package_directory, ...)
            client.modules.upload_package(module, package_directory)

        :param module: The Module resource for the package.
        :type module: Module
        :param package_directory: The root directory of the package.
        :type package_directory: str
        """
        if any(artifact.digest.md5 is None for artifact in module.artifacts):
            raise ValueError("artifact.digest.md5 must be set for all artifacts")
        for artifact in module.artifacts:
            assert artifact.digest.md5 is not None
            file_path = Path(package_directory) / artifact.path
            cache_path = self._platform.storage_root / module.id / artifact.path
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "rb") as fin:
                with open(cache_path, "wb") as fout:
                    fout.write(fin.read())


class _Reports(_Common[Report, _apigroups._Reports], _DocumentationMixin):
    def __init__(self, platform: DyffLocalPlatform):
        super().__init__(
            platform,
            entity_kind=Entities.Report,
            entity_type=Report,
            remote_ops=platform.remote.reports if platform.remote else None,
        )

    def create(self, request: SchemaObject[ReportCreateRequest]) -> Report:
        """Create a new entity.

        :param request: The entity create request specification.
        :return: A full entity spec with its .id and other system properties set
        """
        request = _parse_schema_object(ReportCreateRequest, request)
        id = ids.generate_entity_id()
        report_dict = request.dict()
        report_dict["id"] = id
        report_dict["account"] = self._platform.account
        report_dict["status"] = EntityStatus.admitted
        report_dict["creationTime"] = datetime.now(timezone.utc)

        evaluation = self._platform.evaluations.get(request.evaluation)
        if evaluation is None:
            raise HttpResponseError(
                f"evaluations/{request.evaluation}", status_code=404
            )
        report_dict["dataset"] = evaluation.dataset
        report_dict["inferenceService"] = (
            evaluation.inferenceSession.inferenceService.id
        )

        report = Report.parse_obj(report_dict)
        self._platform._commit(report)

        try:
            run_report(report, storage_root=self._platform.storage_root)
            report.status = EntityStatus.complete
        except Exception:
            report.status = EntityStatus.failed
        self._platform._commit(report)

        return report


class _SafetyCases(_Common[SafetyCase, _apigroups._SafetyCases], _DocumentationMixin):
    def __init__(self, platform: DyffLocalPlatform):
        super().__init__(
            platform,
            entity_kind=Entities.SafetyCase,
            entity_type=SafetyCase,
            remote_ops=platform.remote.safetycases if platform.remote else None,
        )

    def create(self, request: SchemaObject[AnalysisCreateRequest]) -> SafetyCase:
        """Create a new entity.

        :param request: The entity create request specification.
        :return: A full entity spec with its .id and other system properties set
        """
        request = _parse_schema_object(AnalysisCreateRequest, request)
        id = ids.generate_entity_id()

        method_id = request.method
        method = self._platform.methods.get(method_id)
        if method is None:
            raise HttpResponseError(f"methods/{method_id}", status_code=404)

        # Create an entity representing the output of the Analysis
        safetycase_spec = method.output.safetyCase
        if safetycase_spec is None:
            raise ValueError("Method spec violates constraints")

        # Populate additional context data
        def get_system() -> InferenceService | Model:
            if request.scope.inferenceService is None:
                raise ValueError("Must specify at least request.scope.inferenceService")
            service = self._platform.inferenceservices.get(
                request.scope.inferenceService
            )
            if service is None:
                raise HttpResponseError(
                    f"inferenceservices/{request.scope.inferenceService}",
                    status_code=404,
                )
            if service.model is not None:
                model = self._platform.models.get(service.model.id)
                if model is None:
                    raise HttpResponseError(
                        f"models/{service.model.id}",
                        status_code=404,
                    )
                return model
            else:
                return service

        system = get_system()

        # TODO: Placeholders
        system_documentation = Documentation(
            title=_namespaced_id(system),
            summary="This is the summary text for System Placeholder.",
            entity=system.id,
        )
        usecase_documentation = Documentation(
            title=_namespaced_id(method),
            summary="This is the summary text for Use Case Placeholder.",
            entity=method.id,
        )

        class SystemData(DyffSchemaBaseModel):
            spec: Union[Model, InferenceService]
            documentation: Documentation

        class UseCaseData(DyffSchemaBaseModel):
            spec: Method
            documentation: Documentation

        system_data = SystemData(spec=system, documentation=system_documentation)
        usecase_data = UseCaseData(spec=method, documentation=usecase_documentation)

        def encode(data: DyffSchemaBaseModel) -> str:
            return base64.b64encode(data.json().encode()).decode()

        safetycase = SafetyCase(
            account=request.account,
            id=id,
            creationTime=datetime.now(timezone.utc),
            status=EntityStatus.admitted,
            scope=request.scope,
            method=upcast(ForeignMethod, method.dict()),
            arguments=request.arguments,
            inputs=request.inputs,
            data=[
                AnalysisData(
                    key="system",
                    value=encode(system_data),
                ),
                AnalysisData(
                    key="usecase",
                    value=encode(usecase_data),
                ),
            ],
            # This covers: .name, .description
            **safetycase_spec.dict(),
        )
        self._platform._commit(safetycase)

        analysis = upcast(Analysis, safetycase.dict())
        # This fixes some things that YAML can't parse (like Enums)
        analysis_dict = json.loads(analysis.json())
        analysis_dict["id"] = id
        # Code expects a full k8s manifest
        # TODO: Should only pass the 'spec' part in the first place from
        # dyff-operator, but that requires figuring out how to manipulate YAML in Go
        analysis_dict = {"spec": analysis_dict}
        config_file = self._platform.entity_path(safetycase.id) / ".analysis.yaml"
        yaml = ruamel.yaml.YAML()
        with open(config_file, "w") as fout:
            yaml.dump(analysis_dict, fout)

        # This mimics the platform behavior of re-trying failed analyses in
        # case the error was due to a transient cloud platform issue. We don't
        # expect errors to be transient when running locally, but it's necessary
        # for testing certain regressions (e.g., [DYFF-577]).
        # FIXME: Magic number
        for _retry in range(2):
            try:
                run_analysis(
                    method,
                    storage_root=self._platform.storage_root,
                    config_file=config_file,
                )
                safetycase.status = EntityStatus.complete
                break
            except Exception:
                safetycase.status = EntityStatus.failed
        self._platform._commit(safetycase)

        # Populate the .id field of the scores
        try:
            file = self._platform.entity_path(safetycase.id) / ".dyff" / "scores.json"
            with open(file, "r") as fin:
                scores_obj = json.load(fin)
        except FileNotFoundError:
            pass
        else:
            for score_data in scores_obj["scores"]:
                score_data["kind"] = Entities.Score.value
                score_data["id"] = ids.namespaced_id(
                    score_data["analysis"], score_data["name"]
                )
            with open(file, "w") as fout:
                json.dump(scores_obj, fout)

        return safetycase


class _Documentation:
    def __init__(self, platform: DyffLocalPlatform):
        self._platform = platform

    def get(self, id: str) -> Documentation:
        """Get the documentation associated with an entity."""
        try:
            file = self._platform.entity_path(id) / ".documentation.json"
            return Documentation.parse_file(file)
        except FileNotFoundError:
            return Documentation()

    def edit(
        self, id: str, edit_request: SchemaObject[DocumentationEditRequest]
    ) -> Documentation:
        """Edit the documentation associated with an entity."""
        edit_request = _parse_schema_object(DocumentationEditRequest, edit_request)
        doc = self.get(id)
        if edit_request.documentation.title is not None:
            doc.title = edit_request.documentation.title
        if edit_request.documentation.summary is not None:
            doc.summary = edit_request.documentation.summary
        if edit_request.documentation.fullPage is not None:
            doc.fullPage = edit_request.documentation.fullPage

        cache_dir = self._platform.entity_path(id)
        cache_dir.mkdir(exist_ok=True)
        with open(cache_dir / ".documentation.json", "w") as fout:
            fout.write(doc.json())
        return doc


class _Scores:
    def __init__(self, platform: DyffLocalPlatform):
        self._platform = platform

    def get(self, *, analysis: str) -> list[Score]:
        """Get all the scores output by the given analysis."""
        try:
            file = self._platform.entity_path(analysis) / ".dyff" / "scores.json"
            with open(file, "r") as fin:
                scores_obj = json.load(fin)
            return [Score.parse_obj(score) for score in scores_obj["scores"]]
        except FileNotFoundError:
            return []


class DyffLocalPlatform:
    """Emulates a subset of Dyff Platform operations locally.

    This class is intended to aid in local development and debugging of code
    and data that will run on the Dyff Platform. The inferface mirrors that of
    ``dyff.client.Client`` and should have similar behavior.

    Entities created on the local platform are stored in a local cache. You can
    optionally provide a ``dyff.client.Client`` instance, in which case you can
    use the ``.fetch()`` functions to download an entity and all associated
    artifacts to local storage.
    """

    def __init__(
        self,
        storage_root: Path | str = "dyff-outputs",
        *,
        remote_client: Optional[Client] = None,
    ):
        self._storage_root = Path(storage_root).resolve()
        self._client = remote_client

        self._datasets = _Datasets(self)
        self._evaluations = _Evaluations(self)
        self._inferenceservices = _InferenceServices(self)
        self._inferencesessions = _InferenceSessions(self)
        self._measurements = _Measurements(self)
        self._methods = _Methods(self)
        self._models = _Models(self)
        self._modules = _Modules(self)
        self._reports = _Reports(self)
        self._safetycases = _SafetyCases(self)
        self._scores = _Scores(self)
        self._documentation = _Documentation(self)

        self._storage_root.mkdir(exist_ok=True)

    def _require_client(self) -> Client:
        if not self._client:
            raise ValueError("remote client not available")
        return self._client

    @property
    def datasets(self) -> _Datasets:
        """Operations on :class:`~dyff.schema.platform.Dataset` entities."""
        return self._datasets

    @property
    def evaluations(self) -> _Evaluations:
        """Operations on :class:`~dyff.schema.platform.Evaluation` entities."""
        return self._evaluations

    @property
    def inferenceservices(self) -> _InferenceServices:
        """Operations on :class:`~dyff.schema.platform.InferenceService` entities."""
        return self._inferenceservices

    @property
    def inferencesessions(self) -> _InferenceSessions:
        """Operations on :class:`~dyff.schema.platform.InferenceSession` entities."""
        return self._inferencesessions

    @property
    def measurements(self) -> _Measurements:
        """Operations on :class:`~dyff.schema.platform.Measurement` entities."""
        return self._measurements

    @property
    def methods(self) -> _Methods:
        """Operations on :class:`~dyff.schema.platform.Method` entities."""
        return self._methods

    @property
    def models(self) -> _Models:
        """Operations on :class:`~dyff.schema.platform.Model` entities."""
        return self._models

    @property
    def modules(self) -> _Modules:
        """Operations on :class:`~dyff.schema.platform.Module` entities."""
        return self._modules

    @property
    def reports(self) -> _Reports:
        """Operations on :class:`~dyff.schema.platform.Report` entities."""
        return self._reports

    @property
    def safetycases(self) -> _SafetyCases:
        """Operations on :class:`~dyff.schema.platform.SafetyCase` entities."""
        return self._safetycases

    @property
    def scores(self) -> _Scores:
        """Operations on :class:`~dyff.schema.platform.Score` entities."""
        return self._scores

    @property
    def documentation(self) -> _Documentation:
        """Operations on :class:`~dyff.schema.platform.Documentation` entities."""
        return self._documentation

    @property
    def remote(self) -> Client | None:
        """The remote client instance."""
        return self._client

    @property
    def storage_root(self) -> Path:
        """The root of the local storage directory tree."""
        return self._storage_root

    @property
    def account(self) -> str:
        """A dummy local account name."""
        return "local"

    def entity_path(self, id: str) -> Path:
        """Returns the path to the local directory that stores information about the
        entity with the given ID."""
        return self.storage_root / id

    def link_entity(self, package: Path, id: Optional[str] = None) -> str:
        """Creates a symlink in the local storage tree pointing to a directory on the
        file system. You can either provide an ID or let the platform generate one.
        Returns the assigned ID.

        This can be used to create an "editable" package so that you can refer to the
        package at a stable ID while still changing the contents of the files in it.

        :param package: The path to the directory to symlink to.
        :param id: If provided, becomes the ID of the linked package in the platform.
            Otherwise, a new ID is generated.
        :return: The ID of the linked entity.
        """
        package = package.resolve()
        id = id or ids.generate_entity_id()
        cache_path = self.storage_root / id
        if not cache_path.exists():
            cache_path.symlink_to(package)
        elif cache_path.is_symlink():
            target = cache_path.resolve()
            if target != package:
                raise ValueError(f"{id} -> {target}: conflict")
        else:
            raise ValueError(f"{cache_path} exists and is not a symlink")
        return id

    def _commit(self, entity: DyffEntity) -> None:
        cache_dir = self.entity_path(entity.id)
        cache_dir.mkdir(exist_ok=True)
        filename = f".{entity.kind.lower()}.json"
        with open(cache_dir / filename, "w") as fout:
            fout.write(entity.json())
