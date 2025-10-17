# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

import os
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

import urllib3

from dyff.client import Client, HttpResponseError
from dyff.schema.platform import *
from dyff.schema.requests import *

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class bcolors:
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


ctx = dict()


def create_dyff_client():
    api_key = os.environ.get("DYFF_API_KEY")
    endpoint = os.environ.get("DYFF_API_ENDPOINT")

    if not api_key or not endpoint:
        raise ValueError(
            "DYFF_API_KEY and DYFF_API_ENDPOINT environment variables must be set"
        )

    return Client(api_key=api_key, endpoint=endpoint, insecure=True, timeout=30)


def wait_for_success(get_entity_fn, *, timeout: timedelta):
    return  # Don't need to wait, can queue
    then = datetime.now(timezone.utc)
    while (datetime.now(timezone.utc) - then) < timeout:
        try:
            status = get_entity_fn().status
            if is_status_success(status):
                return
            elif is_status_failure(status):
                raise AssertionError(f"failure status: {status}")
        except HttpResponseError as ex:
            if ex.status_code != 404:
                raise
        time.sleep(1)
    raise AssertionError("timeout")


# Use existing method
def create_new_model_score(client: Client, num_replicas: int):
    for replication in range(num_replicas):
        try:
            print(
                f"Creating {bcolors.UNDERLINE}Model{bcolors.ENDC} ",
                end="",
            )

            model_request = ModelCreateRequest(
                name=f"mock-model-compare-{replication}",
                account="test",
                artifact=ModelArtifact(
                    kind=ModelArtifactKind.Mock,
                ),
                storage=ModelStorage(
                    medium=ModelStorageMedium.Mock,
                ),
                source=ModelSource(
                    kind=ModelSourceKinds.Mock,
                ),
                resources=ModelResources(storage="0"),
            )
            model = client.models.create(model_request)

            print(
                f"{model.id} | Publishing... ",
                end="",
            )
            wait_for_success(
                lambda: client.models.get(model.id),
                timeout=timedelta(minutes=2),
            )
            client.models.publish(model.id, "preview")
            print(f"{bcolors.OKGREEN}Success{bcolors.ENDC}")

            try:
                print(
                    f"Creating {bcolors.UNDERLINE}Inf Svc{bcolors.ENDC} ",
                    end="",
                )
                service_request = InferenceServiceCreateRequest(
                    account=ctx["account"],
                    name=f"mock-llm-svc-compare-{replication}",
                    model=model.id,
                    runner=InferenceServiceRunner(
                        kind=InferenceServiceRunnerKind.MOCK,
                        resources=ModelResources(
                            storage="1Gi",
                            memory="2Gi",
                        ),
                    ),
                    interface=InferenceInterface(
                        endpoint="generate",
                        outputSchema=DataSchema.make_output_schema(
                            DyffDataSchema(
                                components=["text.Text"],
                            ),
                        ),
                        inputPipeline=[
                            SchemaAdapter(
                                kind="TransformJSON",
                                configuration={"prompt": "$.text"},
                            ),
                        ],
                        outputPipeline=[
                            SchemaAdapter(
                                kind="ExplodeCollections",
                                configuration={"collections": ["text"]},
                            ),
                        ],
                    ),
                )
                inferenceservice = client.inferenceservices.create(service_request)

                print(
                    f"{inferenceservice.id} | Publishing... ",
                    end="",
                )
                wait_for_success(
                    lambda: client.inferenceservices.get(inferenceservice.id),
                    timeout=timedelta(minutes=2),
                )
                client.inferenceservices.publish(inferenceservice.id, "preview")
                print(f"{bcolors.OKGREEN}Success{bcolors.ENDC}")

                try:
                    print(
                        f"Creating {bcolors.UNDERLINE}Safety Case{bcolors.ENDC} ",
                        end="",
                    )
                    safetycase_jupyter_notebook_request = AnalysisCreateRequest(
                        account=ctx["account"],
                        method=ctx["method"],
                        scope=AnalysisScope(
                            evaluation=None,
                            dataset=None,
                            inferenceService=inferenceservice.id,
                            model=model.id,
                        ),
                        arguments=[
                            AnalysisArgument(
                                keyword="trueName", value="Hans Sprungfeld"
                            ),
                            AnalysisArgument(
                                keyword="isOutlier",
                                value=("true" if replication == 0 else "false"),
                            ),
                        ],
                        inputs=[
                            AnalysisInput(
                                keyword="cromulence", entity=ctx["measurement"]
                            ),
                        ],
                    )
                    safetycase = client.safetycases.create(
                        safetycase_jupyter_notebook_request
                    )
                    print(
                        f"{safetycase.id} | Publishing... ",
                        end="",
                    )
                    wait_for_success(
                        lambda: client.safetycases.get(safetycase.id),
                        timeout=timedelta(minutes=2),
                    )
                    client.safetycases.publish(safetycase.id, "preview")
                    print(f"{bcolors.OKGREEN}Success{bcolors.ENDC}")

                except Exception as e:
                    print(
                        f"{bcolors.FAIL}Failed{bcolors.ENDC}\nSafety Case failed to create: {e}"
                    )
                    break
            except Exception as e:
                print(
                    f"{bcolors.FAIL}Failed{bcolors.ENDC}\nService failed to create: {e}"
                )
                break
        except Exception as e:
            print(f"{bcolors.FAIL}Failed{bcolors.ENDC}\nModel failed to create: {e}")
            break


def create_score_method(client: Client):

    try:
        account = ctx["account"]
        module_jupyter_notebook_dir = Path(
            Path(__file__).parent.resolve(), "data", "module_jupyter_notebook"
        )
        print("Creating jupyter notebook module ", end="")
        module_jupyter_notebook = client.modules.create_package(
            module_jupyter_notebook_dir,
            account=account,
            name="module_jupyter_notebook",
        )
        client.modules.upload_package(
            module_jupyter_notebook, module_jupyter_notebook_dir
        )
        print(f"module_jupyter_notebook: {module_jupyter_notebook.id}")

    except Exception as e:
        print(f"Failed to create jupyter module: {e}")
        return

    try:
        method_jupyter_notebook_request = MethodCreateRequest(
            name="method_notebook_scores",
            scope=MethodScope.InferenceService,
            description="""*Distribution Score Notebook Method*""",
            implementation=MethodImplementation(
                kind=MethodImplementationKind.JupyterNotebook,
                jupyterNotebook=MethodImplementationJupyterNotebook(
                    notebookModule=module_jupyter_notebook.id,
                    notebookPath="test-notebook.ipynb",
                ),
            ),
            parameters=[
                MethodParameter(keyword="trueName", description="His real name")
            ],
            inputs=[
                MethodInput(kind=MethodInputKind.Measurement, keyword="cromulence"),
            ],
            output=MethodOutput(
                kind=MethodOutputKind.SafetyCase,
                safetyCase=SafetyCaseSpec(
                    name="safetycase_notebook",
                    description="""*Markdown Description*""",
                ),
            ),
            scores=[
                ScoreSpec(
                    name="float_unit_primary",
                    title="Float (primary; with unit)",
                    summary="A float with a unit that is the 'primary' score",
                    minimum=0,
                    maximum=1,
                    unit="MJ/kg",
                    priority="primary",
                    valence="positive",
                ),
                ScoreSpec(
                    name="int",
                    title="Integer",
                    summary="An Integer score",
                    valence="positive",
                    priority="secondary",
                ),
                ScoreSpec(
                    name="int_big",
                    title="Integer (Big)",
                    summary="A big Integer score",
                    valence="positive",
                    priority="secondary",
                ),
                ScoreSpec(
                    name="int_percent",
                    title="Integer (Percentage)",
                    summary="A percentage represented as an integer",
                    valence="positive",
                    priority="secondary",
                    minimum=0,
                    maximum=100,
                ),
                ScoreSpec(
                    name="no_display",
                    title="Not displayed",
                    summary="A score that should not be displayed",
                    valence="negative",
                    priority="secondary",
                ),
                ScoreSpec(
                    name="exp_rate_low",
                    title="Exponential Distribution (Low Rate)",
                    summary="An exponential distribution with a low rate, leading to a gradual decay.",
                    valence="positive",
                    priority="secondary",
                    minimum=0,
                    maximum=10,
                ),
                ScoreSpec(
                    name="exp_rate_high",
                    title="Exponential Distribution (High Rate)",
                    summary="An exponential distribution with a high rate, causing rapid decay.",
                    valence="positive",
                    priority="secondary",
                    minimum=0,
                    maximum=10,
                ),
                ScoreSpec(
                    name="poisson_rate_low",
                    title="Poisson Distribution (Low Rate)",
                    summary="A Poisson distribution with a low average event rate, generating fewer events.",
                    valence="positive",
                    priority="secondary",
                    minimum=0,
                    maximum=20,
                ),
                ScoreSpec(
                    name="poisson_rate_high",
                    title="Poisson Distribution (High Rate)",
                    summary="A Poisson distribution with a high average event rate, generating more events.",
                    valence="positive",
                    priority="secondary",
                    minimum=0,
                    maximum=20,
                ),
                ScoreSpec(
                    name="normal_standard",
                    title="Normal Distribution (Standard)",
                    summary="A normal distribution with a mean of 0 and a standard deviation of 1.",
                    valence="positive",
                    priority="secondary",
                    minimum=-5,
                    maximum=5,
                ),
                ScoreSpec(
                    name="normal_shifted",
                    title="Normal Distribution (Shifted)",
                    summary="A normal distribution with a mean of 5 and a standard deviation of 2.",
                    valence="positive",
                    priority="secondary",
                    minimum=0,
                    maximum=10,
                ),
                ScoreSpec(
                    name="bimodal_close",
                    title="Bi-Modal Distribution (Close Peaks)",
                    summary="A bi-modal distribution with two peaks close to each other, creating moderate separation.",
                    valence="positive",
                    priority="secondary",
                    minimum=-5,
                    maximum=15,
                ),
                ScoreSpec(
                    name="bimodal_separated",
                    title="Bi-Modal Distribution (Separated Peaks)",
                    summary="A bi-modal distribution with two peaks far apart, creating clear separation between clusters.",
                    valence="positive",
                    priority="secondary",
                    minimum=-5,
                    maximum=20,
                ),
                ScoreSpec(
                    name="close_together",
                    title="Close Values Around 50",
                    summary="Values generated close to 50 within an expanded range of ±10.",
                    valence="positive",
                    priority="secondary",
                    minimum=0,
                    maximum=100,
                ),
                ScoreSpec(
                    name="in_middle",
                    title="Values in the Middle",
                    summary="Values generated in the middle of the range, centered around 50.",
                    valence="positive",
                    priority="secondary",
                    minimum=0,
                    maximum=100,
                ),
                ScoreSpec(
                    name="near_min",
                    title="Values Near Minimum",
                    summary="Values generated near the minimum, within the range of 0 to 10.",
                    valence="positive",
                    priority="secondary",
                    minimum=0,
                    maximum=100,
                ),
                ScoreSpec(
                    name="near_max",
                    title="Values Near Maximum",
                    summary="Values generated near the maximum, within the range of 90 to 100.",
                    valence="positive",
                    priority="secondary",
                    minimum=0,
                    maximum=100,
                ),
                ScoreSpec(
                    name="extreme_outliers",
                    title="Extreme Outliers",
                    summary="Extreme outlier values that are far outside the typical range.",
                    valence="positive",
                    priority="secondary",
                    minimum=0,
                    maximum=100,
                ),
                ScoreSpec(
                    name="same_values",
                    title="All Values Exactly the Same",
                    summary="All values are exactly the same, uniform data for testing.",
                    valence="positive",
                    priority="secondary",
                    minimum=0,
                    maximum=100,
                ),
            ],
            modules=[module_jupyter_notebook.id],
            account=account,
        )
        method_jupyter_notebook = client.methods.create(method_jupyter_notebook_request)
        client.methods.publish(method_jupyter_notebook.id, "preview")

        print(f"Created method {method_jupyter_notebook.id}")
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Full stack trace: {tb}")
        print(f"${bcolors.FAIL}Failed to create method {e}{bcolors.ENDC}")


# Main function to execute the script
def main():
    try:
        client = create_dyff_client()
        choice = input(
            "1. Create a new method\n2. Create model/svc and safety case\n> "
        )
        if choice == "1":
            create_score_method(client)
        elif choice == "2":
            num_replicas = int(input("# Instances\n> "))
            ctx["account"] = input("Account ID\n> ")
            ctx["dataset"] = input("Dataset ID\n> ")
            ctx["measurement"] = input("Measurement ID\n> ")
            ctx["method"] = input("Method ID\n> ")
            create_new_model_score(client, num_replicas)
        else:
            print("Bad option")

    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
