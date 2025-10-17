# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

import os
import sys
import tempfile
from pathlib import Path

from dyff.client import Client


def main():
    endpoint = os.environ.get("DYFF_API_ENDPOINT")
    token = os.environ["DYFF_API_TOKEN"]
    insecure = os.environ.get("DYFF_API_INSECURE") == "1"
    dyffapi = Client(api_key=token, endpoint=endpoint, insecure=insecure)

    dataset_id = sys.argv[1]

    with tempfile.TemporaryDirectory() as tmp:
        dyffapi.datasets.download(dataset_id, Path(tmp) / "data")


if __name__ == "__main__":
    main()
