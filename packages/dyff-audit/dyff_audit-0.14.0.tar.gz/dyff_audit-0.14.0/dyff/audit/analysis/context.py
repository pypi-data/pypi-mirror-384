# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

# mypy: disable-error-code="import-untyped"
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any, Literal, Optional, Union

import pyarrow
import pydantic
import ruamel.yaml
from IPython.display import display as ipy_display

from dyff.schema import ids
from dyff.schema.dataset import arrow
from dyff.schema.platform import (
    Analysis,
    Documentation,
    DyffSchemaBaseModel,
    InferenceService,
    Method,
    Model,
    ScoreData,
    ScoreMetadata,
    ScoreMetadataRefs,
)

from .. import components
from .._internal import timestamp, upcast


def _decode_data(data: str) -> Any:
    return json.loads(base64.b64decode(data))


def _analysis_from_yaml(analysis_yaml: dict) -> Analysis:
    if "spec" in analysis_yaml:
        analysis_yaml = analysis_yaml["spec"]

    if (analysis_data := analysis_yaml.get("data")) is not None:
        for item in analysis_data:
            if item["key"] == "analysis":
                return upcast(Analysis, _decode_data(item["value"]))

    analysis_yaml = analysis_yaml.copy()
    analysis_yaml["method"].setdefault("id", ids.null_id())
    analysis_yaml["method"].setdefault("account", ids.null_id())
    return upcast(Analysis, analysis_yaml)


def _id_from_yaml(analysis_yaml: dict) -> str:
    return analysis_yaml["spec"]["id"]


def id_from_config_file(analysis_config_file: Union[Path, str]) -> str:
    """Parses an analysis config file and returns the analysis ID."""
    yaml = ruamel.yaml.YAML()
    with open(analysis_config_file, "r") as fin:
        analysis_yaml = yaml.load(fin)
    return _id_from_yaml(analysis_yaml)


class SystemInformation(DyffSchemaBaseModel):
    spec: Union[Model, InferenceService] = pydantic.Field(
        description="The specification of the system entity. This is a Model"
        " if the system is backed by a model, otherwise an InferenceService."
    )
    documentation: Documentation = pydantic.Field(
        description="The documentation associated with the system entity."
    )

    class Config:
        # Allow extra fields for backward compatibility with custom analysis image feature
        extra = pydantic.Extra.ignore


class UseCaseInformation(DyffSchemaBaseModel):
    spec: Method = pydantic.Field(
        description="The specification of the use case entity."
    )
    documentation: Documentation = pydantic.Field(
        description="The documentation associated with the system entity."
    )

    class Config:
        # Allow extra fields for backward compatibility with custom analysis image feature
        extra = pydantic.Extra.ignore


class Scores(DyffSchemaBaseModel):
    scores: list[ScoreData] = pydantic.Field(
        default_factory=list, description="The list of score data"
    )

    class Config:
        # Allow extra fields for backward compatibility with custom analysis image feature
        extra = pydantic.Extra.ignore


class AnalysisContext:
    """AnalysisContext is Dyff's mechanism for making input data available to user-
    authored analysis Methods.

    When the Method is implemented in a framework such as Jupyter that does not support
    "arguments", the implementation accesses its inputs by instantiating an
    AnalysisContext. The AnalysisContext gets its configuration information from
    environment variables. The runners for analyses implemented in other ways also use
    AnalysisContext under the hood.
    """

    def __init__(
        self,
        *,
        analysis_config_file: Union[Path, str, None] = None,
        local_storage_root: Union[Path, str, None] = None,
        analysis: Optional[Analysis] = None,
        id: Optional[str] = None,
        allow_override_from_environment: bool = False,
    ):
        """When running an analysis on the Dyff Platform, the platform provides the
        ``analysis_config_file`` and the ``local_storage_root`` arguments via the
        environment variables ``DYFF_AUDIT_ANALYSIS_CONFIG_FILE`` and
        ``DYFF_AUDIT_LOCAL_STORAGE_ROOT``.

        .. note::

            If you are creating an ``AnalysisContext`` instance in code that
            will run on the Dyff Platform, you must call the constructor
            with **no arguments**, e.g., ``ctx = AnalysisContext()``.

        :keyword analysis_config_file: The path to a YAML-format specification of
            an Analysis. If not specified, it is read from the
            ``DYFF_AUDIT_ANALYSIS_CONFIG_FILE`` environment variable.
        :keyword local_storage_root: The root directory for local storage of
            entity data. If not specified, it is read from the
            ``DYFF_AUDIT_LOCAL_STORAGE_ROOT`` environment variable.
        :keyword analysis: You can also specify the analysis as an Analysis
            instance. If you do, you must also specify the ``id``. This is mainly
            useful for debugging.
        :keyword id: The ID of the analysis, which is needed when instantiating
            from an Analysis instance, because Analysis doesn't have an ``.id``
            field.
        :keyword allow_override_from_environment: If ``True``, environment
            variables will override values in the config file. By default, the
            config file has precedence.
        """
        if id is not None and analysis is not None:
            if analysis_config_file is not None:
                raise ValueError(
                    "'(id, analysis)' and 'analysis_config_file' are mutually exclusive"
                )
            self._id = id
            self._analysis = analysis
        else:
            if allow_override_from_environment:
                analysis_config_file = (
                    os.environ.get("DYFF_AUDIT_ANALYSIS_CONFIG_FILE")
                    or analysis_config_file
                )
            else:
                analysis_config_file = analysis_config_file or os.environ.get(
                    "DYFF_AUDIT_ANALYSIS_CONFIG_FILE"
                )
            if analysis_config_file is None:
                raise ValueError(
                    "Must provide '(id, analysis)' or 'analysis_config_file'"
                    " or set DYFF_AUDIT_ANALYSIS_CONFIG_FILE environment variable"
                )
            if id is not None or analysis is not None:
                raise ValueError(
                    "'(id, analysis)' and 'analysis_config_file' are mutually exclusive"
                )

            yaml = ruamel.yaml.YAML()
            with open(analysis_config_file, "r") as fin:
                analysis_yaml = yaml.load(fin)
            self._id = _id_from_yaml(analysis_yaml)
            self._analysis = _analysis_from_yaml(analysis_yaml)

        if allow_override_from_environment:
            local_storage_root = (
                os.environ.get("DYFF_AUDIT_LOCAL_STORAGE_ROOT") or local_storage_root
            )
        else:
            local_storage_root = local_storage_root or os.environ.get(
                "DYFF_AUDIT_LOCAL_STORAGE_ROOT"
            )
        if local_storage_root is None:
            raise ValueError(
                "Must provide local_storage_root"
                " or set DYFF_AUDIT_LOCAL_STORAGE_ROOT environment variable."
            )
        self._local_storage_root = Path(local_storage_root)
        if not self._local_storage_root.is_absolute():
            raise ValueError("local_storage_root must be an absolute path")

        self._parameters = {p.keyword: p for p in self.analysis.method.parameters}
        self._arguments = {a.keyword: a.value for a in self.analysis.arguments}
        self._inputs = {i.keyword: i.entity for i in self.analysis.inputs}
        self._input_kinds = {i.keyword: i.kind for i in self.analysis.method.inputs}
        self._input_paths = {
            e.keyword: str(self._local_storage_root / e.entity)
            for e in self.analysis.inputs
        }

        self._analysis_data = {
            e.key: _decode_data(e.value) for e in self._analysis.data
        }

        system_data = self._analysis_data.get("system")
        self._system_information = (
            SystemInformation(**system_data) if system_data else None
        )

        usecase_data = self._analysis_data.get("usecase")
        self._usecase_information = (
            UseCaseInformation(**usecase_data) if usecase_data else None
        )

    @property
    def id(self) -> str:
        """The ID of the current analysis."""
        return self._id

    @property
    def analysis(self) -> Analysis:
        """The spec for the current analysis."""
        return self._analysis

    @property
    def local_storage_root(self) -> Path:
        """The root path where subdirectories containing artifacts for individual Dyff
        resources will be created on the local file system."""
        return self._local_storage_root

    @property
    def output_path(self) -> Path:
        """The path where output artifacts are stored on the local file system."""
        return self._local_storage_root / self._id

    @property
    def arguments(self) -> dict[str, str]:
        """The arguments passed to the analysis."""
        return self._arguments.copy()

    @property
    def inputs(self) -> list[str]:
        """The names of all of the input datasets passed to the analysis."""
        return list(self._inputs.keys())

    def get_argument(self, keyword: str) -> str:
        """Get the value of an argument passed to the analysis.

        :param keyword: The keyword specified for the argument in the Method spec
        """
        return self._arguments[keyword]

    def open_input_dataset(self, keyword: str) -> pyarrow.dataset.Dataset:
        """Open a dataset provided as input to the analysis.

        :param keyword: The keyword specified for the input in the Method spec
        """
        entity = self._inputs[keyword]
        path = self._local_storage_root / entity
        return arrow.open_dataset(str(path))

    @property
    def system(self) -> Optional[SystemInformation]:
        """Information about the system under test.

        Currently, this is populated only for the SafetyCase workflow.
        """
        return self._system_information

    @property
    def usecase(self) -> Optional[UseCaseInformation]:
        """Information about the use case being tested.

        Currently, this is populated only for the SafetyCase workflow.

        .. deprecated:: 0.10.2

            "usecase" is a deprecated alias for "Method"; this name will
            change in a future release.
        """
        return self._usecase_information

    def Conclusion(
        self,
        *,
        text: str,
        indicator: Literal["Information", "Question", "Hazard"] = "Information",
    ) -> None:
        """Display a :py:class:`~dyff.audit.components.Conclusion` widget at the current
        position in the Jupyter notebook.

        :keyword text: The text to display.
        :keyword indicator: The icon to display.
        """
        component = components.Conclusion(indicator=indicator, text=text)
        ipy_display(component)

    def Score(
        self,
        *,
        quantity: float,
        text: str,
        output: Optional[str] = None,
        display: bool = True,
        format: Optional[str] = None,
        unit: Optional[str] = None,
    ) -> None:
        """Display a :py:class:`~dyff.audit.components.Score` widget at the current
        position in the Jupyter notebook.

        If ``output`` is given, the score will be saved in the Dyff datastore
        under the specified name. The name must match the name of a score
        declared in the Method spec. In this case, ``format`` and ``unit`` take
        the value specific in the spec, and overriding this value is an error.

        :keyword quantity: The measured value of the score.
        :keyword text: A text description of what the score means.
        :keyword output: If given, it must match the name of a score declared
            in the Method spec. The score quantity will be saved in the Dyff
            datastore under that name.
        :keyword display: If False, do not display the score widget in the
            Jupyter notebook (but still output the score if ``output`` is given).
        :keyword format: A Python format string used to render the quantity as
            a string. It *must* use the key ``quantity``, and it *may* use the
            key ``unit``, e.g. ``"{quantity} {unit}"``.
        :keyword unit: A string representation of the unit of measurement, e.g.,
            ``"MJ/kg"``, ``"%"``, etc. Prefer SI units when applicable.
        """
        quantity_string: Optional[str] = None

        if output:
            for spec in self.analysis.method.scores:
                if spec.name == output:
                    break
            else:
                raise ValueError(
                    f"No score declared with name '{output}'; see Method {self.analysis.method.id}"
                )
            if format is not None or unit is not None:
                raise ValueError("Cannot override 'format' or 'unit' from score spec")
            format = spec.format
            unit = spec.unit
            quantity_string = spec.quantity_string(quantity)

            score = ScoreData(
                analysis=self.id,
                metadata=ScoreMetadata(
                    refs=ScoreMetadataRefs(
                        method=self.analysis.method.id,
                        **self.analysis.scope.dict(),
                    )
                ),
                quantity=quantity,
                quantityString=quantity_string,
                text=text,
                **spec.dict(),
            )

            meta_dir = self.output_path / ".dyff"
            meta_dir.mkdir(parents=True, exist_ok=True)
            try:
                scores_data: Scores = Scores.parse_file(meta_dir / "scores.json")
            except FileNotFoundError:
                scores_data = Scores()

            for existing_score in scores_data.scores:
                if existing_score.name == output:
                    raise ValueError(f"Already specified: score '{output}'")

            scores_data.scores.append(score)
            with open(meta_dir / "scores.json", "w") as fout:
                fout.write(scores_data.json())

        if display:
            if format is None:
                raise ValueError(
                    "must specifiy 'format' for Scores with no ScoreSpec declared"
                )
            if quantity_string is None:
                quantity_string = ScoreData.format_quantity(format, quantity, unit=unit)
            kwargs = dict(quantity=quantity_string, text=text)
            # We want None to mean "unspecified" so that we get the defaults
            if unit is not None:
                kwargs["unit"] = unit
            component = components.Score.parse_obj(kwargs)
            ipy_display(component)

    def TitleCard(
        self,
        *,
        headline: str,
        author: str,
        summary_phrase: str,
        summary_text: str,
        system_title: str | None = None,
        system_summary: str | None = None,
        usecase_title: str | None = None,
        usecase_summary: str | None = None,
    ) -> None:
        """Display a :py:class:`~dyff.audit.components.TitleCard` widget at the current
        position in the Jupyter notebook.

        Normally, this should be the first output in the notebook.

        :keyword headline: The headline text for the notebook.
        :keyword author: Description of the author(s) of the notebook.
        :keyword summary_phrase: A "sub-heading" for the summary information.
        :keyword summary_text: A text summary of the notebook.
        :keyword system_title: The "title" of the system-under-test. When running on
            the Dyff platform, this defaults to the title given in the system's
            documentation.
        :keyword system_summary: A "summary" of the system-under-test. When running on
            the Dyff platform, this defaults to the summary given in the
            system's documentation.
        :keyword usecase_title: The "title" of the Method being run. When running on
            the Dyff platform, this defaults to the title given in the Method's
            documentation.

            .. deprecated:: 0.10.2

                "usecase" is a deprecated alias for "Method"; this name will
                change in a future release.

        :keyword usecase_summary: A "summary" of the Method being run. When running on
            the Dyff platform, this defaults to the summary given in the
            Methods's documentation.

            .. deprecated:: 0.10.2

                "usecase" is a deprecated alias for "Method"; this name will
                change in a future release.
        """

        def from_context(name: str, path: str) -> str:
            keys = path.split(".")
            d = self._analysis_data
            try:
                for k in keys:
                    d = d[k]
                if d is None or not isinstance(d, str):
                    raise ValueError()
                return d
            except Exception:
                raise ValueError(
                    f"Must set {name} because {path} is not present in analysis context."
                )

        if system_title is None:
            system_title = from_context("system_title", "system.documentation.title")
        if system_summary is None:
            system_summary = from_context(
                "system_summary", "system.documentation.summary"
            )
        if usecase_title is None:
            usecase_title = from_context("usecase_title", "usecase.documentation.title")
        if usecase_summary is None:
            usecase_summary = from_context(
                "usecase_summary", "usecase.documentation.summary"
            )

        if (date := self._analysis_data.get("date")) is not None:
            # Validate the date
            date = timestamp.dt_to_str(timestamp.parse(date))
        else:
            date = timestamp.now_str()

        component = components.TitleCard(
            headline=headline,
            author=author,
            date=date,
            system_title=system_title,
            system_summary=system_summary,
            usecase_title=usecase_title,
            usecase_summary=usecase_summary,
            summary_phrase=summary_phrase,
            summary_text=summary_text,
        )
        ipy_display(component)


__all__ = [
    "AnalysisContext",
    "Scores",
    "id_from_config_file",
]
