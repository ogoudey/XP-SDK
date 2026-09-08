"""One-shot local loopback HTTP server used to receive the browser
redirect during `xp login`.

Binds to 127.0.0.1 only (never 0.0.0.0), on a freshly chosen free
port, and shuts itself down after handling exactly one /callback
request or timing out.
"""
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional
from urllib.parse import urlparse, parse_qs

SUCCESS_HTML = """<!doctype html>
<html><head><title>xp login</title></head>
<body style="font-family: sans-serif; text-align:center; margin-top: 15vh;">
<h2>You're logged in.</h2>
<p>You can close this tab and return to your terminal.</p>
</body></html>"""

ERROR_HTML = """<!doctype html>
<html><head><title>xp login</title></head>
<body style="font-family: sans-serif; text-align:center; margin-top: 15vh;">
<h2>Login failed.</h2>
<p>{message}</p>
<p>You can close this tab and try again in your terminal.</p>
</body></html>"""


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _CallbackHandler(BaseHTTPRequestHandler):
    # These class attrs are overridden per-instance-class in CallbackServer.
    expected_state: str = ""
    result: dict = {}
    result_event: threading.Event = threading.Event()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return

        params = {k: v[0] for k, v in parse_qs(parsed.query).items()}

        if params.get("state") != self.expected_state:
            self._respond(400, ERROR_HTML.format(message="State mismatch. Please try again."))
            self.result.update({"error": "state_mismatch"})
            self.result_event.set()
            return

        if "error" in params:
            self._respond(400, ERROR_HTML.format(message=params.get("error_description", params["error"])))
            self.result.update({"error": params["error"]})
            self.result_event.set()
            return

        code = params.get("code")
        if not code:
            self._respond(400, ERROR_HTML.format(message="Missing authorization code."))
            self.result.update({"error": "missing_code"})
            self.result_event.set()
            return

        self._respond(200, SUCCESS_HTML)
        self.result.update({"code": code})
        self.result_event.set()

    def _respond(self, status: int, body: str):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def log_message(self, format, *args):
        pass  # silence default request logging to stderr


class CallbackServer:
    """Runs a local HTTP server on 127.0.0.1 that waits for a single
    /callback request carrying `code` and `state`."""

    def __init__(self, expected_state: str):
        self.port = find_free_port()
        handler = type("Handler", (_CallbackHandler,), {
            "expected_state": expected_state,
            "result": {},
            "result_event": threading.Event(),
        })
        self._handler_cls = handler
        self._httpd = HTTPServer(("127.0.0.1", self.port), handler)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)

    @property
    def redirect_uri(self) -> str:
        return f"http://127.0.0.1:{self.port}/callback"

    def start(self):
        self._thread.start()

    def wait_for_result(self, timeout: float) -> Optional[dict]:
        got_it = self._handler_cls.result_event.wait(timeout)
        self._httpd.shutdown()
        self._thread.join(timeout=2)
        if not got_it:
            return None
        return self._handler_cls.result
