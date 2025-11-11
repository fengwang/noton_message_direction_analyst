import json
import logging
import os
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable, Optional


LOGGER = logging.getLogger(__name__)


def _read_json_body(handler: BaseHTTPRequestHandler) -> tuple[Optional[dict], Optional[str]]:
    """Helper to read and parse a JSON body from the incoming request."""
    try:
        content_length = int(handler.headers.get("Content-Length", "0"))
    except (TypeError, ValueError):
        return None, "Invalid Content-Length header"

    raw_body = handler.rfile.read(content_length) if content_length > 0 else b""
    if not raw_body:
        return None, "Request body is empty"

    try:
        return json.loads(raw_body.decode("utf-8")), None
    except json.JSONDecodeError:
        return None, "Request body must be valid JSON"


class _APIServer(ThreadingHTTPServer):
    daemon_threads = True


class MessageAnalystAPIServer:
    """Simple background HTTP server exposing the model through a REST API."""

    def __init__(
        self,
        forward_fn: Callable[[str], str],
        *,
        host: Optional[str] = None,
        port: Optional[int] = None,
        ready_timeout: float = 5.0,
    ) -> None:
        self._forward_fn = forward_fn
        self._host = host or os.getenv("MESSAGE_ANALYST_API_HOST", "0.0.0.0")
        default_port = int(os.getenv("MESSAGE_ANALYST_API_PORT", "8601"))
        self._port = port or default_port
        self._ready_timeout = ready_timeout

        self._httpd: Optional[_APIServer] = None
        self._thread: Optional[threading.Thread] = None
        self._ready = threading.Event()
        self._startup_error: Optional[BaseException] = None

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        if self._httpd:
            return self._httpd.server_address[1]
        return self._port

    @property
    def base_url(self) -> str:
        public_base = os.getenv(
            "MESSAGE_ANALYST_API_URL",
            f"http://127.0.0.1:{self.port}",
        )
        return public_base.rstrip("/")

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._thread = threading.Thread(target=self._serve_forever, daemon=True)
        self._thread.start()

        if not self._ready.wait(timeout=self._ready_timeout):
            raise TimeoutError(
                f"API server failed to start within {self._ready_timeout} seconds"
            )

        if self._startup_error:
            raise self._startup_error

        LOGGER.info("Message analyst API server listening on %s:%s", self.host, self.port)

    def _serve_forever(self) -> None:
        try:
            handler_cls = self._build_handler()
            self._httpd = _APIServer((self._host, self._port), handler_cls)
            self._ready.set()
            self._httpd.serve_forever(poll_interval=0.5)
        except BaseException as ex:  # pylint: disable=broad-except
            self._startup_error = ex
            self._ready.set()
            LOGGER.exception("Failed to start API server: %s", ex)

    def _build_handler(self) -> type[BaseHTTPRequestHandler]:
        forward_fn = self._forward_fn

        class RequestHandler(BaseHTTPRequestHandler):
            routes: set[str] = {"/api/analyze", "/api/analyze/"}

            def _set_common_headers(self, status: HTTPStatus) -> None:
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS, GET")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.end_headers()

            def log_message(self, format: str, *args: object) -> None:  # noqa: A003
                LOGGER.debug("%s - %s", self.address_string(), format % args)

            def do_OPTIONS(self) -> None:  # noqa: N802
                self.send_response(HTTPStatus.NO_CONTENT)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.end_headers()

            def do_GET(self) -> None:  # noqa: N802
                if self.path.rstrip("/") == "/api/health":
                    self._send_json({"status": "ok"}, HTTPStatus.OK)
                else:
                    self._send_json(
                        {"error": "Not Found", "detail": "Unknown endpoint"},
                        HTTPStatus.NOT_FOUND,
                    )

            def do_POST(self) -> None:  # noqa: N802
                if self.path.rstrip("/") not in self.routes:
                    self._send_json(
                        {"error": "Not Found", "detail": "Unknown endpoint"},
                        HTTPStatus.NOT_FOUND,
                    )
                    return

                payload, error = _read_json_body(self)
                if error:
                    self._send_json({"error": "Bad Request", "detail": error}, HTTPStatus.BAD_REQUEST)
                    return

                query = payload.get("query") if isinstance(payload, dict) else None
                if not isinstance(query, str) or not query.strip():
                    self._send_json(
                        {"error": "Bad Request", "detail": "Field 'query' must be a non-empty string."},
                        HTTPStatus.BAD_REQUEST,
                    )
                    return

                started = time.perf_counter()
                try:
                    answer = forward_fn(query)
                except Exception as exc:  # pylint: disable=broad-except
                    LOGGER.exception("Failed to process query: %s", exc)
                    self._send_json(
                        {"error": "Internal Server Error", "detail": "Unable to generate response."},
                        HTTPStatus.INTERNAL_SERVER_ERROR,
                    )
                    return

                elapsed_ms = round((time.perf_counter() - started) * 1000.0, 2)
                self._send_json(
                    {
                        "query": query,
                        "response": answer,
                        "meta": {"took_ms": elapsed_ms},
                    },
                    HTTPStatus.OK,
                )

            def _send_json(self, payload: dict, status: HTTPStatus) -> None:
                self._set_common_headers(status)
                body = json.dumps(payload).encode("utf-8")
                self.wfile.write(body)

        return RequestHandler
