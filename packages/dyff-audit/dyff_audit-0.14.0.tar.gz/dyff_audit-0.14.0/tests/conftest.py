# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import httpx
import pytest
import requests

from dyff.audit.local.platform import DyffLocalPlatform
from dyff.client import Client, HttpResponseError, Timeout
from dyff.client.errors import HTTPError
from dyff.schema import commands, ids
from dyff.schema.platform import (
    is_status_failure,
    is_status_success,
    is_status_terminal,
)
from dyff.schema.v0.r1.requests import DocumentationEditRequest

DATA_DIR = Path(__file__).parent.resolve() / "data"
COMPARISON_REPLICATIONS = 5


def validate_api_environment():
    """Validate API endpoint and token for remote testing."""
    api_endpoint = os.getenv("DYFF_API_ENDPOINT")
    api_token = os.getenv("DYFF_API_TOKEN")

    if not api_endpoint:
        raise RuntimeError(
            "DYFF_API_ENDPOINT required for remote testing "
            "(e.g., https://api.dyff.local/v0)"
        )

    if not api_token:
        raise RuntimeError(
            "DYFF_API_TOKEN required. Generate with: "
            "kubectl exec -n dyff <dyff-api-pod> -- python3 -m dyff.api.mgmt "
            "tokens create -t account -i <account-id> --role Admin"
        )

    # Test connectivity
    insecure = os.getenv("DYFF_API_INSECURE") == "1"
    health_url = api_endpoint.replace("/v0", "") + "/health"

    try:
        response = requests.get(
            health_url,
            headers={"Authorization": f"Bearer {api_token}"},
            timeout=10,
            verify=not insecure,
        )
        response.raise_for_status()
        print(f"✓ API connection successful to {api_endpoint}")
    except requests.RequestException as e:
        raise RuntimeError(f"API connection failed: {e}")


def pytest_addoption(parser):
    parser.addoption("--storage_root", action="store", default=None)
    parser.addoption("--test_remote", action="store_true", default=False)
    parser.addoption("--api_endpoint", action="store", default=None)
    parser.addoption("--api_token", action="store", default=None)
    parser.addoption("--api_insecure", action="store_true", default=False)
    parser.addoption("--skip_workflows", action="store_true", default=False)
    parser.addoption("--skip_inference_mocks", action="store_true", default=False)
    parser.addoption("--skip_analyses", action="store_true", default=False)
    parser.addoption("--skip_artifacts", action="store_true", default=False)
    parser.addoption("--skip_challenges", action="store_true", default=False)
    parser.addoption("--skip_documentation", action="store_true", default=False)
    parser.addoption("--skip_families", action="store_true", default=False)
    parser.addoption("--skip_huggingface", action="store_true", default=False)
    parser.addoption("--skip_errors", action="store_true", default=False)
    parser.addoption("--enable_flaky", action="store_true", default=False)
    parser.addoption("--enable_fuse", action="store_true", default=False)
    parser.addoption("--enable_vllm", action="store_true", default=False)
    parser.addoption("--enable_vllm_multinode", action="store_true", default=False)
    parser.addoption("--enable_comparisons", action="store_true", default=False)


def _create_client(pytestconfig, *, timeout: Optional[Timeout] = None) -> Client:
    endpoint = pytestconfig.getoption("api_endpoint") or os.environ["DYFF_API_ENDPOINT"]
    token = pytestconfig.getoption("api_token") or os.environ["DYFF_API_TOKEN"]
    insecure = (
        pytestconfig.getoption("api_insecure")
        or os.environ.get("DYFF_API_INSECURE") == "1"
    )
    return Client(api_key=token, endpoint=endpoint, insecure=insecure, timeout=timeout)


@pytest.fixture(scope="session", autouse=True)
def validate_test_environment(pytestconfig):
    """Validate test environment before running any tests."""
    if pytestconfig.getoption("test_remote"):
        validate_api_environment()


@pytest.fixture(scope="session")
def dyffapi(
    pytestconfig, tmp_path_factory, validate_test_environment
) -> Client | DyffLocalPlatform:
    """Provides either a remote Client or a local DyffLocalPlatform."""
    if pytestconfig.getoption("test_remote"):
        return _create_client(pytestconfig)
    storage_root = pytestconfig.getoption("storage_root") or os.getenv(
        "DYFF_AUDIT_LOCAL_STORAGE_ROOT"
    )
    if storage_root:
        return DyffLocalPlatform(Path(storage_root).resolve())
    return DyffLocalPlatform(tmp_path_factory.mktemp("dyff"))


@pytest.fixture(scope="session")
def ctx(pytestconfig) -> dict[str, Any]:
    """Shared context for passing IDs between tests."""
    context: dict[str, Any] = {}
    if pytestconfig.getoption("test_remote"):
        context["account"] = "test"
    else:
        account = ids.generate_entity_id()
        context["account"] = account
        # pre-create a dummy inference service so later tests depending on it can skip or use it
        from dyff.schema.platform import DyffModelWithID

        context["inferenceservice"] = DyffModelWithID(
            id=ids.generate_entity_id(), account=account
        )
    return context


@pytest.fixture(scope="session", autouse=True)
def cleanup(pytestconfig, dyffapi, ctx, request):
    """Ensure any sessions opened are cleaned up at the end."""

    def terminate():
        # This will delete any recorded inference sessions by ID
        for key in list(ctx):
            if key.startswith("inferencesession"):
                try:
                    dyffapi.inferencesessions.delete(ctx[key].id)
                except Exception:
                    pass

    request.addfinalizer(terminate)


def wait_for_ready(
    dyffapi: Client | DyffLocalPlatform, session_id: str, *, timeout: timedelta
):
    then = datetime.now(timezone.utc)
    while (datetime.now(timezone.utc) - then) < timeout:
        if dyffapi.inferencesessions.ready(session_id):
            return
        time.sleep(10)
    raise AssertionError("timeout")


def wait_for_terminal_status(get_entity_fn, *, timeout: timedelta) -> str:
    then = datetime.now(timezone.utc)
    while (datetime.now(timezone.utc) - then) < timeout:
        try:
            status = get_entity_fn().status
            if is_status_terminal(status):
                return status
        except HTTPError as ex:
            if ex.status != 404:
                raise
        except HttpResponseError as ex:
            if ex.status_code != 404:
                raise
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code != 404:
                raise
        time.sleep(10)
    raise AssertionError("timeout")


def wait_for_success(get_entity_fn, *, timeout: timedelta):
    then = datetime.now(timezone.utc)
    while (datetime.now(timezone.utc) - then) < timeout:
        try:
            status = get_entity_fn().status
            if is_status_success(status):
                return
            elif is_status_failure(status):
                raise AssertionError(f"failure status: {status}")
        except HTTPError as ex:
            if ex.status != 404:
                raise
        except HttpResponseError as ex:
            if ex.status_code != 404:
                raise
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code != 404:
                raise
        time.sleep(10)
    raise AssertionError("timeout")


def wait_for_completion(get_entity_fn, *, timeout: timedelta):
    then = datetime.now(timezone.utc)
    while (datetime.now(timezone.utc) - then) < timeout:
        try:
            return get_entity_fn()
        except HTTPError as ex:
            if ex.status != 404:
                raise
        except HttpResponseError as ex:
            if ex.status_code != 404:
                raise
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code != 404:
                raise
        time.sleep(10)
    raise AssertionError("timeout")


def download_and_assert(download_func, download_id, download_dir):
    with tempfile.TemporaryDirectory() as tmp:
        download_path = Path(tmp) / download_dir
        download_func(download_id, download_path)
        assert download_path.exists(), "Download directory was not created"
        assert any(download_path.iterdir()), "No files were downloaded"


def assert_documentation_exist(get_doc_func, resource_id):
    documentation = wait_for_completion(
        lambda: get_doc_func(resource_id),
        timeout=timedelta(minutes=2),
    )
    assert documentation is not None


def edit_documentation_and_assert(edit_doc_func, resource_id, **kwargs):
    edited_title = kwargs.get("title", "EditedTitle")
    edited_summary = kwargs.get("summary", "EditedSummary")
    edited_fullpage = kwargs.get("fullPage", "EditedFullPage")

    documentation_post_edit = wait_for_completion(
        lambda: edit_doc_func(
            resource_id,
            DocumentationEditRequest(
                documentation=commands.EditEntityDocumentationPatch(
                    title=edited_title,
                    summary=edited_summary,
                    fullPage=edited_fullpage,
                ),
            ),
        ),
        timeout=timedelta(minutes=2),
    )

    assert documentation_post_edit.title == edited_title
    assert documentation_post_edit.summary == edited_summary
    assert documentation_post_edit.fullPage == edited_fullpage
