# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

# mypy: disable-error-code="import-untyped"
from __future__ import annotations

import importlib.resources
import string
from typing import Literal, Optional

import pydantic

from dyff.schema.platform import DyffSchemaBaseModel, summary_maxlen

from . import templates


class Conclusion(DyffSchemaBaseModel):
    indicator: Literal["Hazard", "Information", "Question"] = pydantic.Field(
        default="Information",
        description="The kind of indicator icon to display in the conclusion.",
    )

    text: str = pydantic.Field(
        description="A short text description of the conclusion.", max_length=140
    )

    def _repr_html_(self) -> str:
        template_file = (
            importlib.resources.files(templates) / "Conclusion.template.html"
        )
        with template_file.open("r") as fin:
            template = string.Template(fin.read())

        return template.substitute(
            text=self.text,
            info_display="block" if self.indicator == "Information" else "none",
            question_display="block" if self.indicator == "Question" else "none",
            hazard_display="block" if self.indicator == "Hazard" else "none",
        )


class Score(DyffSchemaBaseModel):
    quantity: str = pydantic.Field(description="The string rendering of the quantity")

    text: str = pydantic.Field(
        description="A short text interpretation of the quantity.",
        max_length=summary_maxlen(),
    )

    unit: Optional[str] = pydantic.Field(
        default=None,
        description="The unit of measure, if applicable (e.g., 'meters', 'kJ/g')."
        " Use standard SI abbreviations where possible for better indexing.",
    )

    def _repr_html_(self) -> str:
        template_file = importlib.resources.files(templates) / "Score.template.html"
        with template_file.open("r") as fin:
            template = string.Template(fin.read())

        return template.substitute(
            quantity=self.quantity,
            text=self.text,
        )


class TitleCard:
    def __init__(
        self,
        *,
        headline: str,
        author: str,
        date: str,
        system_title: str,
        system_summary: str,
        usecase_title: str,
        usecase_summary: str,
        summary_phrase: str,
        summary_text: str,
    ):
        self._headline = headline
        self._author = author
        self._date = date
        self._system_title = system_title
        self._system_summary = system_summary
        self._usecase_title = usecase_title
        self._usecase_summary = usecase_summary
        self._summary_phrase = summary_phrase
        self._summary_text = summary_text

    @property
    def headline(self) -> str:
        return self._headline

    @property
    def author(self) -> str:
        return self._author

    @property
    def date(self) -> str:
        return self._date

    @property
    def system_title(self) -> str:
        return self._system_title

    @property
    def system_summary(self) -> str:
        return self._system_summary

    @property
    def usecase_title(self) -> str:
        return self._usecase_title

    @property
    def usecase_summary(self) -> str:
        return self._usecase_summary

    @property
    def summary_phrase(self) -> str:
        return self._summary_phrase

    @property
    def summary_text(self) -> str:
        return self._summary_text

    def _repr_html_(self) -> str:
        template_file = importlib.resources.files(templates) / "TitleCard.template.html"
        with template_file.open("r") as fin:
            template = string.Template(fin.read())

        return template.substitute(
            headline=self._headline,
            author=self._author,
            date=self._date,
            system_title=self._system_title,
            system_summary=self._system_summary,
            usecase_title=self._usecase_title,
            usecase_summary=self._usecase_summary,
            summary_phrase=self._summary_phrase,
            summary_text=self._summary_text,
        )
