# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

# mypy: disable-error-code="import-untyped"
import uuid
from datetime import timedelta

import pytest
from conftest import (
    DATA_DIR,
    wait_for_completion,
    wait_for_success,
)

from dyff.audit.local.platform import DyffLocalPlatform
from dyff.client import Client
from dyff.schema.platform import *
from dyff.schema.requests import *


@pytest.mark.datafiles(DATA_DIR)
def test_artifacts_prepare(
    pytestconfig,
    dyffapi: Client | DyffLocalPlatform,
    ctx,
    datafiles,
):
    """This isn't a real test; it builds a Docker image that gets consumed in the other
    artifacts tests."""
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()
    if pytestconfig.getoption("skip_artifacts"):
        pytest.skip()

    import docker

    docker_client = docker.from_env()
    uniquifier = str(uuid.uuid4())
    image_tag = f"dyff-test/{uniquifier}:latest"
    image, _logs = docker_client.images.build(
        path=str(datafiles / "artifact"),
        tag=image_tag,
        buildargs={
            "DYFF_IMAGE_UNIQUIFIER": str(uuid.uuid4()),
        },
    )
    for line in _logs:
        print(line)
    ctx["image"] = image
    ctx["image_tag"] = image_tag


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "test_artifacts_prepare",
    ]
)
def test_artifacts_create(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()
    if pytestconfig.getoption("skip_artifacts"):
        pytest.skip()
    assert isinstance(dyffapi, Client)

    account = ctx["account"]
    request = ArtifactCreateRequest(
        account=account,
    )
    artifact = dyffapi.artifacts.create(request)
    print(f"artifact: {artifact.id}")
    ctx["artifact"] = artifact

    wait_for_completion(
        lambda: dyffapi.artifacts.get(artifact.id),
        timeout=timedelta(minutes=2),
    )


# If you get an error like this::
#
#     Error response from daemon: client version 1.22 is too old.
#     Minimum supported API version is 1.24, please upgrade your client to a newer version"
#
# it probably means that your version of ``skopeo`` is older than 1.14.2:
# https://github.com/containers/skopeo/issues/2202
@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "test_artifacts_create",
    ]
)
def test_artifacts_upload(
    pytestconfig,
    dyffapi: Client | DyffLocalPlatform,
    ctx,
    datafiles,
):
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()
    if pytestconfig.getoption("skip_artifacts"):
        pytest.skip()
    assert isinstance(dyffapi, Client)

    artifact: OCIArtifact = ctx["artifact"]
    image_tag = ctx["image_tag"]

    dyffapi.artifacts.push(artifact, source=f"docker-daemon:{image_tag}")


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "test_artifacts_upload",
    ]
)
def test_artifacts_finalize(
    pytestconfig,
    dyffapi: Client | DyffLocalPlatform,
    ctx,
    datafiles,
):
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()
    if pytestconfig.getoption("skip_artifacts"):
        pytest.skip()
    assert isinstance(dyffapi, Client)

    artifact: OCIArtifact = ctx["artifact"]
    dyffapi.artifacts.finalize(artifact.id)

    wait_for_success(
        lambda: dyffapi.artifacts.get(artifact.id),
        timeout=timedelta(minutes=2),
    )
