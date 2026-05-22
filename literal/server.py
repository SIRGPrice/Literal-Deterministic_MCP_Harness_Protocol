"""Local HTTP API for Literal Studio and quick integrations."""

from __future__ import annotations

import json
import mimetypes
import threading
import webbrowser
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .harness import Harness
from .registry import CapabilityRegistry
from .state import AtomicStateStore
from .trace import TraceStore


@dataclass(frozen=True)
class StudioServerConfig:
    catalog_path: Path
    policy_path: Path | None = None
    state_path: Path | None = None
    trace_path: Path | None = None
    static_dir: Path | None = None


class HarnessContainer:
    """Mutable holder so config writes can hot-reload the harness."""

    def __init__(self, config: StudioServerConfig):
        self.config = config
        self._lock = threading.RLock()
        self.harness = self._load()

    def _load(self) -> Harness:
        return Harness.from_paths(
            catalog_path=self.config.catalog_path,
            policy_path=self.config.policy_path,
            state_path=self.config.state_path,
            trace_path=self.config.trace_path,
        )

    def reload(self) -> Harness:
        with self._lock:
            self.harness = self._load()
            return self.harness

    def current(self) -> Harness:
        with self._lock:
            return self.harness


def run_studio_server(
    config: StudioServerConfig,
    host: str = "127.0.0.1",
    port: int = 8787,
    open_browser: bool = True,
) -> None:
    """Run the local API and optional static Studio server."""

    container = HarnessContainer(config)
    handler_class = _make_handler(container)
    server = ThreadingHTTPServer((host, port), handler_class)
    url = f"http://{host}:{port}"
    print(f"Literal running at {url}")
    print(f"Catalog: {config.catalog_path}")
    if config.static_dir and config.static_dir.exists():
        print(f"Literal Studio static assets: {config.static_dir}")
    else:
        print("Literal Studio static assets not built yet; API endpoints are available.")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Literal.")
    finally:
        server.server_close()


def _make_handler(container: HarnessContainer):
    config = container.config

    class StudioRequestHandler(BaseHTTPRequestHandler):
        server_version = "Literal/0.2"

        def do_OPTIONS(self) -> None:
            self._send_empty(HTTPStatus.NO_CONTENT)

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)
            harness = container.current()

            if path == "/api/health":
                self._send_json({"ok": True, "name": harness.registry.name, "version": harness.registry.version})
            elif path in {"/api/config", "/api/catalog"}:
                self._send_json(harness.catalog())
            elif path == "/api/policies":
                self._send_json(harness.registry.raw_policy)
            elif path == "/api/state":
                target = query.get("target", [None])[0]
                self._send_json(harness.inspect(target))
            elif path == "/api/traces":
                limit = int(query.get("limit", [100])[0])
                self._send_json({"ok": True, "traces": harness.trace_list(limit=limit)})
            elif path == "/api/integration":
                self._send_json(_integration_snippets(config))
            elif path == "/api/stream":
                self._send_sse_snapshot(harness)
            else:
                self._serve_static(path)

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            payload = self._read_json()
            harness = container.current()

            if path == "/api/simulate":
                self._send_json(harness.simulate(str(payload.get("text", ""))))
            elif path == "/api/invoke":
                self._send_json(
                    harness.invoke(
                        target=str(payload.get("target", "")),
                        action=str(payload.get("action", "")),
                        parameters=dict(payload.get("parameters", {})),
                    )
                )
            elif path == "/api/scenario":
                self._send_json(harness.scenario(str(payload.get("name", ""))))
            else:
                self._send_json({"ok": False, "message": "Not found"}, HTTPStatus.NOT_FOUND)

        def do_PUT(self) -> None:
            path = urlparse(self.path).path
            payload = self._read_json()
            if path == "/api/config":
                catalog = payload.get("catalog") or payload
                _write_json(config.catalog_path, catalog)
                if config.policy_path and "policy" in payload:
                    _write_json(config.policy_path, payload["policy"])
                container.reload()
                self._send_json({"ok": True, "message": "Configuration saved"})
            elif path == "/api/policies" and config.policy_path:
                _write_json(config.policy_path, payload)
                container.reload()
                self._send_json({"ok": True, "message": "Policies saved"})
            elif path == "/api/catalog":
                _write_json(config.catalog_path, payload)
                container.reload()
                self._send_json({"ok": True, "message": "Catalog saved"})
            else:
                self._send_json({"ok": False, "message": "Not found or read-only"}, HTTPStatus.NOT_FOUND)

        def log_message(self, format: str, *args: Any) -> None:
            print(f"[{self.log_date_time_string()}] {format % args}")

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            if length == 0:
                return {}
            raw = self.rfile.read(length).decode("utf-8")
            return json.loads(raw or "{}")

        def _send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status)
            self._cors_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_empty(self, status: HTTPStatus) -> None:
            self.send_response(status)
            self._cors_headers()
            self.end_headers()

        def _send_sse_snapshot(self, harness: Harness) -> None:
            payload = json.dumps({"type": "snapshot", "traces": harness.trace_list(limit=20)}, ensure_ascii=False)
            body = f"data: {payload}\n\n".encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self._cors_headers()
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _serve_static(self, path: str) -> None:
            static_dir = config.static_dir
            if not static_dir or not static_dir.exists():
                self._send_json(
                    {
                        "ok": True,
                        "product": "Literal",
                        "tagline": "Deterministic MCP Harness Protocol",
                        "message": "API is running. Build apps/studio to serve the UI from this process.",
                        "endpoints": ["/api/health", "/api/catalog", "/api/simulate", "/api/traces"],
                    }
                )
                return

            relative = "index.html" if path == "/" else path.lstrip("/")
            candidate = (static_dir / relative).resolve()
            try:
                candidate.relative_to(static_dir.resolve())
            except ValueError:
                self._send_json({"ok": False, "message": "Forbidden"}, HTTPStatus.FORBIDDEN)
                return
            if not candidate.exists() or candidate.is_dir():
                candidate = static_dir / "index.html"
            content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
            body = candidate.read_bytes()
            self.send_response(HTTPStatus.OK)
            self._cors_headers()
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _cors_headers(self) -> None:
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

    return StudioRequestHandler


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with open(temp_path, "w", encoding="utf-8") as file_handle:
        json.dump(payload, file_handle, indent=2, ensure_ascii=False)
    temp_path.replace(path)


def _integration_snippets(config: StudioServerConfig) -> dict[str, str]:
    catalog = str(config.catalog_path)
    policy = str(config.policy_path) if config.policy_path else "literal.policy.json"
    return {
        "mcp_stdio": json.dumps(
            {
                "command": "python",
                "args": ["-m", "literal.mcp_server", "--catalog", catalog, "--policy", policy],
            },
            indent=2,
        ),
        "python_sdk": (
            "from literal import harness\n\n"
            f"h = harness({catalog!r}, {policy!r})\n"
            "result = h.simulate('turn on lobby lights')\n"
            "print(result)\n"
        ),
        "http": (
            "curl -X POST http://localhost:8787/api/simulate "
            "-H \"Content-Type: application/json\" "
            "-d '{\"text\":\"turn on lobby lights\"}'"
        ),
    }
