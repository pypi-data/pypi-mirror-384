import os
import selectors
import signal
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

import requests

GATEWAY_PORT = 23456
GATEWAY_PIDFILE = os.path.join(".mcpd", "gateway.pid")


class UDSToHTTPProxyHandler(BaseHTTPRequestHandler):
    routes = {}  # task_id -> { 'uds': {'path': str}, 'tcp': {'host':str,'port':int} }

    def do_GET(self):  # noqa: N802
        self._proxy()

    def do_POST(self):  # noqa: N802
        self._proxy()

    def do_PUT(self):  # noqa: N802
        self._proxy()

    def do_DELETE(self):  # noqa: N802
        self._proxy()

    def _proxy(self):
        parsed = urlparse(self.path)
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) < 2 or parts[0] != "apps":
            self.send_error(404, "Not Found")
            return
        task_id = parts[1]
        route = self.routes.get(task_id)
        if not route:
            self.send_error(410, "Gone")
            return

        # Reconstruct path to backend (strip /apps/<task_id>)
        backend_path = "/" + "/".join(parts[2:])
        if backend_path == "/":
            backend_path = "/"
        if parsed.query:
            backend_path = backend_path + "?" + parsed.query

        # Prepare HTTP/1.1 request over UDS
        body = None
        content_length = self.headers.get("Content-Length")
        if content_length:
            body = self.rfile.read(int(content_length))

        req_lines = [
            f"{self.command} {backend_path} HTTP/1.1",
            "Host: uds",
            "Connection: close",
        ]
        for k, v in self.headers.items():
            if k.lower() in {"host", "content-length"}:
                continue
            req_lines.append(f"{k}: {v}")
        if body is not None:
            req_lines.append(f"Content-Length: {len(body)}")
        req_lines.append("")
        req_head = "\r\n".join(req_lines).encode()

        try:
            # Prefer TCP (more stable), then try UDS
            if route.get("tcp"):
                host = route["tcp"].get("host", "127.0.0.1")
                port = int(route["tcp"].get("port"))
                url = f"http://{host}:{port}{backend_path}"
                fwd_headers = {k: v for k, v in self.headers.items() if k.lower() != "host"}
                resp = requests.request(
                    self.command,
                    url,
                    headers=fwd_headers,
                    data=body,
                    timeout=5,
                    allow_redirects=False,
                )
                self.send_response(resp.status_code)
                for k, v in resp.headers.items():
                    if k.lower() in {"transfer-encoding", "connection"}:
                        continue
                    self.send_header(k, v)
                self.end_headers()
                self.wfile.write(resp.content)
                return
            if route.get("uds"):
                try:
                    path = route["uds"].get("path")
                    if not path or not os.path.exists(path):
                        raise FileNotFoundError("uds path missing")
                    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                        s.settimeout(0.5)
                        s.connect(path)
                        s.sendall(req_head)
                        if body is not None:
                            s.sendall(body)
                        head_lines, body_bytes = self._recv_http(s)
                        status_line = head_lines[0]
                        _http, code_str, reason = status_line.split(" ", 2)
                        code = int(code_str)
                        self.send_response(code, reason)
                        for hdr in head_lines[1:]:
                            if not hdr or ":" not in hdr:
                                continue
                            k, v = hdr.split(":", 1)
                            if k.lower() in {"transfer-encoding", "connection"}:
                                continue
                            self.send_header(k.strip(), v.strip())
                        self.end_headers()
                        self.wfile.write(body_bytes)
                        return
                except Exception:
                    pass
            # If neither worked
            self.send_error(502, "Bad Gateway: no backend available")
            return
        except Exception as exc:  # noqa: BLE001
            self.send_error(502, f"Bad Gateway: {exc}")
            return

        # For TCP path handled above via requests; not reached.

    def _recv_all(self, s: socket.socket) -> bytes:
        sel = selectors.DefaultSelector()
        sel.register(s, selectors.EVENT_READ)
        chunks: list[bytes] = []
        s.settimeout(5)
        while True:
            events = sel.select(timeout=0.5)
            if not events:
                break
            for _key, _mask in events:
                data = s.recv(65536)
                if not data:
                    events = []
                    break
                chunks.append(data)
        return b"".join(chunks)

    def _recv_http(self, s: socket.socket) -> tuple[list[str], bytes]:
        # Read until header complete
        buf = bytearray()
        s.settimeout(5)
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf.extend(chunk)
            idx = buf.find(b"\r\n\r\n")
            if idx != -1:
                head = bytes(buf[:idx])
                rest = bytes(buf[idx + 4 :])
                break
        else:
            head = bytes(buf)
            rest = b""
        head_lines = head.decode(errors="ignore").split("\r\n") if head else []
        # Determine content-length if present
        content_length = 0
        for line in head_lines[1:]:
            if line.lower().startswith("content-length:"):
                try:
                    content_length = int(line.split(":", 1)[1].strip())
                except Exception:
                    content_length = 0
                break
        body = bytearray(rest)
        while content_length and len(body) < content_length:
            chunk = s.recv(min(65536, content_length - len(body)))
            if not chunk:
                break
            body.extend(chunk)
        return head_lines, bytes(body)


class Gateway:
    def __init__(self, port: int = GATEWAY_PORT):
        self.port = port
        self.httpd: HTTPServer | None = None
        self._bound_port: int | None = None

    def add_route(self, task_id: str, uds_path: str) -> None:
        existing = UDSToHTTPProxyHandler.routes.get(task_id, {})
        existing["uds"] = {"path": uds_path}
        UDSToHTTPProxyHandler.routes[task_id] = existing

    def add_tcp_route(self, task_id: str, host: str, port: int) -> None:
        existing = UDSToHTTPProxyHandler.routes.get(task_id, {})
        existing["tcp"] = {"host": host, "port": port}
        UDSToHTTPProxyHandler.routes[task_id] = existing

    def remove_route(self, task_id: str) -> None:
        UDSToHTTPProxyHandler.routes.pop(task_id, None)

    def start(self) -> None:
        class ReusableHTTPServer(HTTPServer):
            allow_reuse_address = True

        # Ensure pid dir
        os.makedirs(os.path.dirname(GATEWAY_PIDFILE), exist_ok=True)
        # Try to bind; if busy, kill previous pid from pidfile and retry
        server: HTTPServer | None = None
        for attempt in range(3):
            bind_port = self.port if attempt == 0 else 0
            try:
                candidate = ReusableHTTPServer(("127.0.0.1", bind_port), UDSToHTTPProxyHandler)
                server = candidate
                self._bound_port = candidate.server_address[1]
                break
            except OSError:
                if attempt == 0 and os.path.exists(GATEWAY_PIDFILE):
                    try:
                        with open(GATEWAY_PIDFILE, "r", encoding="utf-8") as f:
                            pid = int(f.read().strip() or "0")
                        if pid > 0:
                            os.kill(pid, signal.SIGTERM)
                            time.sleep(0.5)
                            continue
                    except Exception:
                        pass
                time.sleep(0.2)
        if server is None:
            self.httpd = None
            self._bound_port = None
            return
        self.httpd = server
        with open(GATEWAY_PIDFILE, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
        thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        thread.start()

    def stop(self) -> None:
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None
        try:
            if os.path.exists(GATEWAY_PIDFILE):
                os.remove(GATEWAY_PIDFILE)
        except Exception:
            pass
        self._bound_port = None

    @property
    def bound_port(self) -> int:
        return self._bound_port if self._bound_port is not None else self.port

    @property
    def is_available(self) -> bool:
        return self.httpd is not None
