"""Azure Functions v2 HTTP API for the Diet Cloud Dashboard."""

from __future__ import annotations

import json
import logging
import os
import time
import uuid

import azure.functions as func

from analysis_service import build_dashboard_payload
from data_source import get_clean_rows


app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


def _query_list(value: str | None) -> list[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()][:20]


def _truthy(value: str | None) -> bool:
    return (value or "").strip().casefold() in {"1", "true", "yes", "on"}


def _cors_headers(req: func.HttpRequest) -> dict[str, str]:
    configured = os.getenv("CORS_ALLOWED_ORIGIN", "*").strip()
    request_origin = req.headers.get("Origin", "")
    allowed = [origin.strip() for origin in configured.split(",") if origin.strip()]
    if "*" in allowed:
        selected = "*"
    elif request_origin and request_origin in allowed:
        selected = request_origin
    else:
        selected = allowed[0] if allowed else ""
    headers = {
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Cache-Control": "no-store",
        "Vary": "Origin",
    }
    if selected:
        headers["Access-Control-Allow-Origin"] = selected
    return headers


def _json_response(req: func.HttpRequest, body: dict, status_code: int) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(body, separators=(",", ":")),
        status_code=status_code,
        mimetype="application/json",
        headers=_cors_headers(req),
    )


@app.function_name(name="DietInsights")
@app.route(route="diet-insights", methods=["GET", "OPTIONS"])
def diet_insights(req: func.HttpRequest) -> func.HttpResponse:
    """Serve chart-ready nutritional insights with optional dashboard filters."""

    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=_cors_headers(req))

    started = time.perf_counter()
    request_id = str(uuid.uuid4())
    try:
        rows, source, source_reloaded = get_clean_rows(
            force_refresh=_truthy(req.params.get("refresh"))
        )
        payload = build_dashboard_payload(
            rows,
            diet_types=_query_list(req.params.get("diet_types")),
            cuisine=req.params.get("cuisine", "")[:100],
            search=req.params.get("search", "")[:100],
            source=source,
        )
        payload["metadata"].update(
            {
                "execution_time_ms": round((time.perf_counter() - started) * 1000, 2),
                "request_id": request_id,
                "source_reloaded": source_reloaded,
                "api_version": "2.0",
            }
        )
        return _json_response(req, payload, 200)
    except ValueError as exc:
        logging.warning("Invalid dataset or request %s: %s", request_id, exc)
        return _json_response(
            req,
            {"error": "invalid_data", "message": str(exc), "request_id": request_id},
            400,
        )
    except (FileNotFoundError, RuntimeError) as exc:
        logging.error("Configuration error %s: %s", request_id, exc)
        return _json_response(
            req,
            {"error": "service_not_configured", "message": str(exc), "request_id": request_id},
            503,
        )
    except Exception:
        logging.exception("Unhandled dashboard API error %s", request_id)
        return _json_response(
            req,
            {
                "error": "internal_server_error",
                "message": "The analysis service could not complete the request.",
                "request_id": request_id,
            },
            500,
        )

