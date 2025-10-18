import argparse
import os
import socketserver
from http.server import BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

import requests


class UDSHTTPProxyHandler(BaseHTTPRequestHandler):
    backend_base: str = ""

    def do_GET(self):  # noqa: N802
        self._proxy()

    def do_POST(self):  # noqa: N802
        self._proxy()

    def do_PUT(self):  # noqa: N802
        self._proxy()

    def do_PATCH(self):  # noqa: N802
        self._proxy()

    def do_DELETE(self):  # noqa: N802
        self._proxy()

    def _proxy(self) -> None:
        body = None
        if self.command in {"POST", "PUT", "PATCH"}:
            length = self.headers.get("Content-Length")
            body = self.rfile.read(int(length)) if length else None
        url = f"{self.backend_base}{self.path}"
        fwd_headers = {k: v for k, v in self.headers.items() if k.lower() != "host"}
        try:
            resp = requests.request(
                self.command, url, headers=fwd_headers, data=body, timeout=5, allow_redirects=False
            )
        except Exception as exc:  # noqa: BLE001
            self.send_error(502, f"Backend error: {exc}")
            return
        self.send_response(resp.status_code)
        for k, v in resp.headers.items():
            if k.lower() in {"transfer-encoding", "connection"}:
                continue
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(resp.content)

    # Override to avoid tuple indexing on Unix sockets
    def address_string(self) -> str:  # type: ignore[override]
        return "uds"

    def log_message(self, format: str, *args) -> None:  # type: ignore[override]
        # Quiet logs; avoid stderr noise under shim
        return


class UnixHTTPServer(ThreadingMixIn, socketserver.UnixStreamServer):
    allow_reuse_address = True
    daemon_threads = True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uds", required=True)
    parser.add_argument("--backend", required=True)
    args = parser.parse_args()

    # Ensure no stale socket
    try:
        if os.path.exists(args.uds):
            os.remove(args.uds)
    except FileNotFoundError:
        pass
    UDSHTTPProxyHandler.backend_base = args.backend.rstrip("/")
    with UnixHTTPServer(args.uds, UDSHTTPProxyHandler) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    main()
