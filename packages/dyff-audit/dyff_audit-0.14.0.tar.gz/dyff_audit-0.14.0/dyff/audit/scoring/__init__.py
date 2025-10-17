# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0
"""Rubrics for scoring the output of inference services."""

from . import classification, text
from .base import Rubric

__all__ = ["Rubric", "classification", "text"]
