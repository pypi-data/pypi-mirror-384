# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

ARG CONTAINER_PROXY
FROM ${CONTAINER_PROXY}python:3.12-slim-bookworm AS build

# Install git for setuptools-scm version detection
RUN apt-get update && apt-get install -y --no-install-recommends git=1:2.39* && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE="1" \
    PYTHONUNBUFFERED="1"

WORKDIR /build/

# hadolint ignore=DL3013,DL3042
RUN python3 -m pip install --upgrade uv

COPY requirements.txt ./

RUN uv pip install --system -r requirements.txt


ARG CONTAINER_PROXY
FROM ${CONTAINER_PROXY}python:3.12-slim-bookworm

# Setting DYFF_IMAGE_UNIQUIFIER to a unique value will ensure that the built
# image has a different digest from previously-built images. We use this to
# ensure that Dyff isn't caching the whole image when testing registry
# functionality.
ARG DYFF_IMAGE_UNIQUIFIER=""
ENV DYFF_IMAGE_UNIQUIFIER=${DYFF_IMAGE_UNIQUIFIER}

COPY --from=build /usr/local/ /usr/local/

ENV PYTHONDONTWRITEBYTECODE="1" \
    PYTHONUNBUFFERED="1"

WORKDIR /dyff/
COPY artifact.py ./

ENTRYPOINT ["uvicorn", "artifact:app", "--proxy-headers", "--host", "0.0.0.0"]
