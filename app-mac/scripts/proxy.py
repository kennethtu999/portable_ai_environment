from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import http.client
import sys
import json
import os
from pathlib import Path
from dotenv import load_dotenv

_ENV_FILE = Path.home() / ".portable_ai_environment" / "claude.env"
if _ENV_FILE.exists():
    load_dotenv(_ENV_FILE)

from urllib.parse import urlparse as _urlparse
_raw = os.getenv("PROXY_TARGET_HOST", "")
_parsed = _urlparse(_raw if "://" in _raw else "https://" + _raw)
TARGET_HOST   = _parsed.hostname or ""
TARGET_PORT   = _parsed.port or 443
TARGET_PREFIX = _parsed.path.rstrip("/")
PORT = int(os.getenv("PROXY_PORT", "8888"))

MODEL_MAPPING = {
    "claude-haiku-4-5-20251001": "claude-haiku-4-5",
}

HOP_BY_HOP_HEADERS = {
    "host", "connection", "keep-alive", "proxy-authenticate",
    "proxy-authorization", "te", "trailers", "transfer-encoding",
    "upgrade", "content-length",
}


class ProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        pass

    def log(self, *args):
        print(*args, file=sys.stderr, flush=True)

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,PATCH,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Expose-Headers", "*")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self): self.forward()
    def do_POST(self): self.forward()
    def do_PUT(self): self.forward()
    def do_PATCH(self): self.forward()
    def do_DELETE(self): self.forward()

    def forward(self):
        conn = None
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length) if content_length > 0 else None

            if body and self.headers.get("Content-Type", "").startswith("application/json"):
                data = json.loads(body.decode("utf-8"))
                if "model" in data and data["model"] in MODEL_MAPPING:
                    data["model"] = MODEL_MAPPING[data["model"]]
                if data.get("top_p") == -1:
                    data.pop("top_p", None)
                if data.get("top_k") == -1:
                    data.pop("top_k", None)
                data.pop("context_management", None)
                body = json.dumps(data).encode("utf-8")

            path = self.path if self.path.startswith("/") else "/" + self.path
            path = TARGET_PREFIX + path
            headers = {k: v for k, v in self.headers.items() if k.lower() not in HOP_BY_HOP_HEADERS}
            headers["Host"] = TARGET_HOST
            headers["Connection"] = "close"
            headers["Content-Length"] = str(len(body or b""))

            self.log(f"→ {self.command} {path[:60]}")
            conn = http.client.HTTPSConnection(TARGET_HOST, TARGET_PORT, timeout=600)
            conn.request(self.command, path, body=body, headers=headers)
            resp = conn.getresponse()
            self.log(f"← {resp.status} {resp.reason}")

            content_type = dict(resp.getheaders()).get("content-type", "")
            self.send_response(resp.status, resp.reason)
            for k, v in resp.getheaders():
                if k.lower() not in HOP_BY_HOP_HEADERS and not k.lower().startswith("access-control-"):
                    self.send_header(k, v)
            self.send_cors()
            self.send_header("Connection", "close")
            self.end_headers()

            if "text/event-stream" in content_type:
                while True:
                    chunk = resp.read(1)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()
                return

            response_body = resp.read()
            if resp.status >= 400:
                self.log(f"⚠ ERROR: {response_body.decode('utf-8', errors='replace')[:200]}")
            self.wfile.write(response_body)
            self.wfile.flush()

        except Exception as e:
            self.log(f"✗ EXCEPTION: {e}")
            body = str(e).encode("utf-8", errors="replace")
            try:
                self.send_response(502)
                self.send_cors()
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception:
                pass
        finally:
            if conn:
                conn.close()


if __name__ == "__main__":
    print(f"Proxy running: http://localhost:{PORT}")
    print(f"Target: https://{TARGET_HOST}{TARGET_PREFIX}")
    ThreadingHTTPServer(("localhost", PORT), ProxyHandler).serve_forever()
