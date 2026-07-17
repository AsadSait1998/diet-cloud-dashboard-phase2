"""Upload All_Diets.csv to the private Azure Blob container used by the Function."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient, ContentSettings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default="data/All_Diets.csv")
    parser.add_argument("--container", default=os.getenv("DATA_CONTAINER_NAME", "datasets"))
    parser.add_argument("--blob", default=os.getenv("DATA_BLOB_NAME", "All_Diets.csv"))
    args = parser.parse_args()

    connection_string = os.getenv("DIET_STORAGE_CONNECTION_STRING", "").strip()
    if not connection_string:
        raise SystemExit("Set DIET_STORAGE_CONNECTION_STRING before running this script.")
    source = Path(args.file)
    if not source.is_file():
        raise SystemExit(f"Dataset not found: {source}")

    service = BlobServiceClient.from_connection_string(connection_string)
    try:
        service.create_container(args.container)
        print(f"Created private container: {args.container}")
    except ResourceExistsError:
        print(f"Container already exists: {args.container}")
    with source.open("rb") as stream:
        service.get_blob_client(args.container, args.blob).upload_blob(
            stream,
            overwrite=True,
            content_settings=ContentSettings(content_type="text/csv"),
        )
    print(f"Uploaded {source} as {args.container}/{args.blob}")


if __name__ == "__main__":
    main()

