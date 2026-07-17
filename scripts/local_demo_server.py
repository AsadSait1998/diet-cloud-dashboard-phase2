"""Zero-dependency local server for the dashboard and a simulated Function endpoint."""

from __future__ import annotations

import json
import mimetypes
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


PROJECT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_DIR / "frontend"
BACKEND_DIR = PROJECT_DIR / "backend"
DATASET_PATH = PROJECT_DIR / "data" / "All_Diets.csv"
sys.path.insert(0, str(BACKEND_DIR))

from analysis_service import build_dashboard_payload, clean_csv_bytes


ROWS = clean_csv_bytes(DATASET_PATH.read_bytes())


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "DietCloudDemo/2.0"

    def log_message(self, format_string, *args):
        sys.stdout.write("[diet-cloud] " + format_string % args + "\n")

    def _send_json(self, body, status=200):
        encoded = json.dumps(body, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def _serve_api(self, query):
        started = time.perf_counter()
        diets = [value.strip() for value in query.get("diet_types", [""])[0].split(",") if value.strip()]
        payload = build_dashboard_payload(
            ROWS,
            diet_types=diets,
            cuisine=query.get("cuisine", [""])[0],
            search=query.get("search", [""])[0],
            source={"storage": "local demo using the Phase 1 dataset"},
        )
        payload["metadata"].update(
            {
                "execution_time_ms": round((time.perf_counter() - started) * 1000, 2),
                "request_id": "local-demo",
                "source_reloaded": query.get("refresh", ["false"])[0].casefold() == "true",
                "api_version": "2.0-local",
            }
        )
        self._send_json(payload)

    def _serve_static(self, request_path):
        relative = "index.html" if request_path in {"", "/"} else request_path.lstrip("/")
        candidate = (FRONTEND_DIR / relative).resolve()
        if FRONTEND_DIR.resolve() not in candidate.parents and candidate != FRONTEND_DIR.resolve():
            self.send_error(403)
            return
        if not candidate.is_file():
            candidate = FRONTEND_DIR / "index.html"
        content = candidate.read_bytes()
        content_type, _ = mimetypes.guess_type(candidate.name)
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type or 'application/octet-stream'}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/diet-insights":
            self._serve_api(parse_qs(parsed.query))
        else:
            self._serve_static(parsed.path)


if __name__ == "__main__":
    host, port = "127.0.0.1", 8000
    print(f"Diet Cloud local demo: http://{host}:{port}")
    ThreadingHTTPServer((host, port), DashboardHandler).serve_forever()

