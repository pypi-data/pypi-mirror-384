# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

import os
from pathlib import Path

from dyff.client import Client


def main():
    account = "test"
    endpoint = os.environ.get("DYFF_API_ENDPOINT")
    token = os.environ["DYFF_API_TOKEN"]
    insecure = os.environ.get("DYFF_API_INSECURE") == "1"
    dyffapi = Client(api_key=token, endpoint=endpoint, insecure=insecure)

    dataset_dir = Path("tests") / "data" / "dataset"
    dataset = dyffapi.datasets.create_arrow_dataset(
        dataset_dir, account=account, name="dataset"
    )
    dyffapi.datasets.upload_arrow_dataset(dataset, dataset_dir)
    print(f"dataset: {dataset.id}")


if __name__ == "__main__":
    main()
