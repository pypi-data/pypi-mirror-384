# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

# mypy: disable-error-code="import-untyped"
import time
from datetime import timedelta

import pytest
from conftest import (  # type: ignore[import-not-found]
    DATA_DIR,
    assert_documentation_exist,
    edit_documentation_and_assert,
    wait_for_success,
)

from dyff.audit.local.platform import DyffLocalPlatform
from dyff.client import Client
from dyff.schema import commands, ids
from dyff.schema.platform import (
    Challenge,
    ChallengeContent,
    ChallengeContentPage,
    ChallengeTaskExecutionEnvironment,
    ChallengeTaskExecutionEnvironmentChoices,
    ChallengeTaskRules,
    TeamAffiliation,
    TeamMember,
)
from dyff.schema.requests import (
    ChallengeContentEditRequest,
    ChallengeCreateRequest,
    ChallengeTaskCreateRequest,
    ChallengeTeamCreateRequest,
)


@pytest.mark.datafiles(DATA_DIR)
def test_challenges_create(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if pytestconfig.getoption("skip_challenges"):
        pytest.skip()
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()
    assert isinstance(dyffapi, Client)

    account: str = ctx["account"]

    challenge = dyffapi.challenges.create(
        ChallengeCreateRequest(
            account=account,
            content=ChallengeContent(page=ChallengeContentPage(summary="summary")),
        )
    )

    print(f"challenge: {challenge.id}")
    ctx["challenge"] = challenge

    wait_for_success(
        lambda: dyffapi.challenges.get(challenge.id),
        timeout=timedelta(minutes=2),
    )


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "test_challenges_create",
    ]
)
def test_challenges_edit_content(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if pytestconfig.getoption("skip_challenges"):
        pytest.skip()
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()
    assert isinstance(dyffapi, Client)

    challenge: Challenge = ctx["challenge"]

    dyffapi.challenges.edit_content(
        challenge.id,
        ChallengeContentEditRequest(
            content=commands.ChallengeContentPatch(
                page=commands.ChallengeContentPagePatch(summary="", body="body")
            )
        ),
    )

    time.sleep(10)

    updated = dyffapi.challenges.get(challenge.id)
    assert updated.content.page.title == "Untitled Challenge"
    assert updated.content.page.summary == ""
    assert updated.content.page.body == "body"


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "test_challenges_create",
    ]
)
def test_challenges_create_task(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if pytestconfig.getoption("skip_challenges"):
        pytest.skip()
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()
    assert isinstance(dyffapi, Client)

    account: str = ctx["account"]
    challenge: Challenge = ctx["challenge"]
    request = ChallengeTaskCreateRequest(
        account=account,
        challenge=challenge.id,
        name="test",
        assessment=ids.null_id(),  # FIXME: This should be xref to a Pipeline
        rules=ChallengeTaskRules(
            executionEnvironment=ChallengeTaskExecutionEnvironmentChoices(
                choices={
                    "default": ChallengeTaskExecutionEnvironment(
                        cpu="1",
                        memory="1Gi",
                    )
                },
            )
        ),
    )
    task = dyffapi.challenges.create_task(challenge.id, request)

    print(f"challengetask: {task.id}")
    ctx["challengetask"] = task

    time.sleep(10)
    stored_task = dyffapi.challenges.get(challenge.id).tasks[task.id]
    assert stored_task == task


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "test_challenges_create",
    ]
)
def test_challenges_create_team(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if pytestconfig.getoption("skip_challenges"):
        pytest.skip()
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()
    assert isinstance(dyffapi, Client)

    account: str = ctx["account"]
    challenge: Challenge = ctx["challenge"]
    request = ChallengeTeamCreateRequest(
        account=account,
        members={
            "rusty": TeamMember(
                name="Rusty Shackleford",
                isCorrespondingMember=True,
                affiliations=["dales_dead_bug"],
            )
        },
        affiliations={
            "dales_dead_bug": TeamAffiliation(
                name="Dale's Dead Bug",
            )
        },
    )
    team = dyffapi.challenges.create_team(challenge.id, request)

    print(f"team: {team.id}")
    ctx["team"] = team

    time.sleep(10)
    stored_team = dyffapi.teams.get(team.id)
    assert stored_team.members == team.members
    assert stored_team.affiliations == team.affiliations


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.depends(
    on=[
        "test_challenges_create_team",
    ]
)
def test_challenges_list_teams(
    pytestconfig, dyffapi: Client | DyffLocalPlatform, ctx, datafiles
):
    if pytestconfig.getoption("skip_challenges"):
        pytest.skip()
    if not pytestconfig.getoption("test_remote"):
        pytest.skip()
    assert isinstance(dyffapi, Client)

    account: str = ctx["account"]
    challenge: Challenge = ctx["challenge"]

    # teams = dyffapi.teams.query(challenge=challenge.id)
    teams = dyffapi.challenges.teams(challenge.id)
    assert len(teams) == 1
