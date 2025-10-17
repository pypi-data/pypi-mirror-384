# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

from typing import List

from dyff.schema.dataset.text import TaggedSpan


def token_tags_to_spans(
    text: str, tokens: List[str], tags: List[str]
) -> List[TaggedSpan]:
    """Computes the list of TaggedSpans corresponding to the tagged tokens in the
    text."""
    spans: List[TaggedSpan] = []
    i = 0
    start = None
    end = None
    current_tag = None

    def finish_span():
        nonlocal spans, start, end, current_tag

        if current_tag is not None:
            spans.append(TaggedSpan(start=start, end=end, tag=current_tag))
        start = None
        end = None
        current_tag = None

    for token_index, token in enumerate(tokens):
        tag = tags[token_index]
        if tag == "O":
            finish_span()
        elif tag.startswith("B-"):
            finish_span()
            current_tag = tag[2:]
        elif tag.startswith("I-"):
            assert tag[2:] == current_tag

        while text[i] != token[0]:
            i += 1
        if start is None:
            start = i
        for c in token:
            assert text[i] == c
            i += 1
        end = i
    finish_span()

    return spans


def visualize_spans(text: str, spans: List[TaggedSpan], *, width: int = 80):
    """Print lines of text with lines representing NER spans aligned underneath.

    Example output::

      My name is Alice and I live in Alaska.
                 PPPPP               LLLLLL
    """
    start = 0
    next_span = 0
    while start < len(text):
        span_text: List[str] = []
        end = min(start + 80, len(text))
        print(text[start:end])
        s = start
        while next_span < len(spans):
            span = spans[next_span]
            span_start = max(span.start, start)
            span_end = min(span.end, end)
            if span_start < end:
                span_text.extend("." * (span_start - s))
                span_text.extend(span.tag[0] * (span_end - span_start))
            s = span_end
            if span.end >= end:
                break
            next_span += 1
        if len(span_text) < width:
            span_text.extend("." * ((end - start) - len(span_text)))
        print("".join(span_text))
        start += width


__all__ = [
    "token_tags_to_spans",
    "visualize_spans",
]
