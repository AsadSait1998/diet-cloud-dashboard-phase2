"""Load the Diets CSV from Azure Blob Storage, with a local-file development mode."""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from typing import Any

from analysis_service import clean_csv_bytes


_CACHE: dict[str, Any] = {"rows": None, "source": None, "loaded_at": 0.0}
_CACHE_LOCK = threading.Lock()


def _cache_ttl_seconds() -> int:
    try:
        return max(0, min(int(os.getenv("CACHE_TTL_SECONDS", "300")), 3600))
    except ValueError:
        return 300


def _download_csv() -> tuple[bytes, dict[str, str]]:
    local_path = os.getenv("DIET_DATASET_PATH", "").strip()
    if local_path:
        path = Path(local_path)
        if not path.exists():
            raise FileNotFoundError(f"DIET_DATASET_PATH does not exist: {path}")
        return path.read_bytes(), {
            "storage": "local file (development only)",
            "path": str(path),
        }

    connection_string = (
        os.getenv("DIET_STORAGE_CONNECTION_STRING")
        or os.getenv("AzureWebJobsStorage")
        or ""
    ).strip()
    if not connection_string:
        raise RuntimeError(
            "Set DIET_STORAGE_CONNECTION_STRING (or AzureWebJobsStorage) in Function App settings."
        )

    container_name = os.getenv("DATA_CONTAINER_NAME", "datasets")
    blob_name = os.getenv("DATA_BLOB_NAME", "All_Diets.csv")

    from azure.storage.blob import BlobServiceClient

    service = BlobServiceClient.from_connection_string(connection_string)
    blob = service.get_blob_client(container=container_name, blob=blob_name)
    return blob.download_blob(max_concurrency=2).readall(), {
        "storage": "Azure Blob Storage",
        "container": container_name,
        "blob": blob_name,
    }


def get_clean_rows(*, force_refresh: bool = False) -> tuple[list[dict[str, Any]], dict[str, str], bool]:
    """Return cleaned rows, source metadata, and whether the source was reloaded."""

    now = time.monotonic()
    if (
        not force_refresh
        and _CACHE["rows"] is not None
        and now - float(_CACHE["loaded_at"]) < _cache_ttl_seconds()
    ):
        return _CACHE["rows"], _CACHE["source"], False

    with _CACHE_LOCK:
        now = time.monotonic()
        if (
            not force_refresh
            and _CACHE["rows"] is not None
            and now - float(_CACHE["loaded_at"]) < _cache_ttl_seconds()
        ):
            return _CACHE["rows"], _CACHE["source"], False

        raw_csv, source = _download_csv()
        rows = clean_csv_bytes(raw_csv)
        _CACHE.update({"rows": rows, "source": source, "loaded_at": time.monotonic()})
        return rows, source, True

