# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

import json
from pathlib import Path

import fastapi

app = fastapi.FastAPI(
    title="Test Artifact",
    redoc_url=None,
)


@app.post(
    f"/v1/completions",
    tags=["openai"],
    summary="[OpenAI] Emulate the /v1/completions API",
    response_description="The text completion response",
)
async def v1_completions(request: fastapi.Request):
    body = await request.json()

    # FIXME: The legacy .artifactsVolume data access strategy mounts things
    # at a *subdirectory* of mountPath that depends on the ID of the mounted
    # resource. For the sake of letting tests pass, we search for the files
    # under the mount instead of assuming an absolute path.
    question = None
    answer = None
    for p in Path("/dyff/mnt/volume").rglob("*.json"):
        if p.name == "q1.json":
            with open(p, "r") as fin:
                question = json.load(fin)
        if p.name == "answer.json":
            with open(p, "r") as fin:
                answer = json.load(fin)
    if question is None or answer is None:
        raise RuntimeError("question and answer not mounted")

    text = f"{question['question']}: {answer['answer']}"

    response_json = {
        "id": "cmpl-uqkvlQyYK7bGYrRHQ0eXlWi7",
        "object": "text_completion",
        "created": 1589478378,
        "model": "dyff-artifacts-test",
        "system_fingerprint": "fp_44709d6fcb",
        "choices": [
            {
                "text": text,
                "index": 0,
                "logprobs": None,
                "finish_reason": "length",
            }
        ],
        "usage": {"prompt_tokens": 5, "completion_tokens": 7, "total_tokens": 12},
    }

    try:
        body["model"]  # exercise input schema
        body["prompt"]  # exercise input schema
        return fastapi.responses.JSONResponse(content=response_json)
    except:
        raise fastapi.HTTPException(
            fastapi.status.HTTP_400_BAD_REQUEST,
            detail="see request schema: https://platform.openai.com/docs/api-reference/completions/create",
        )
