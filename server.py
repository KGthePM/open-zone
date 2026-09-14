#!/usr/bin/env python3
"""Open RedZone spike server: static files + CORS-unlocking HLS proxy.

Every m3u8 request can be routed through /proxy?url=<encoded> — the proxy
fetches upstream, rewrites manifest URLs (variants, segments, keys) to route
back through itself, and adds permissive CORS headers. This makes CORS-blocked
channels playable in the browser. (HEVC channels still need an HEVC-capable
browser/client.)
"""
import http.server
import socketserver
import urllib.request
import urllib.parse
import re
import os
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8790
ROOT = os.path.dirname(os.path.abspath(__file__))

URI_ATTR = re.compile(r'URI="([^"]+)"')
NON_COMMENT_LINE = re.compile(r'^(?![##\s])\S+$', re.MULTILINE)


def absolutize(url, base):
    return urllib.parse.urljoin(base, url)


def rewrite_manifest(text, base_url):
    origin = f"http://localhost:{PORT}/proxy?url="

    def proxied(u):
        absu = absolutize(u, base_url)
        return origin + urllib.parse.quote(absu, safe="")

    # rewrite URI="..." attributes (keys, maps, subtitles)
    text = URI_ATTR.sub(lambda m: f'URI="{proxied(m.group(1))}"', text)
    # rewrite bare URL lines (variants, segments)
    out_lines = []
    for line in text.splitlines():
        if line and not line.startswith("#"):
            out_lines.append(proxied(line))
        else:
            out_lines.append(line)
    return "\n".join(out_lines) + "\n"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def log_message(self, fmt, *args):
        pass  # quiet

    def _origin(self):
        # use the Host header the client connected to, so proxied URLs work
        # from any device on the LAN (phone/TV), not just localhost
        host = self.headers.get("Host") or f"localhost:{PORT}"
        return f"http://{host}/proxy?url="

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/proxy":
            return self.handle_proxy(urllib.parse.parse_qs(parsed.query).get("url", [""])[0])
        # block plalylist requests (we never added it; keep static minimal)
        return super().do_GET()

    def handle_proxy(self, url):
        if not url.startswith(("http://", "https://")):
            self.send_error(400, "bad url")
            return
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                data = r.read()
                ctype = r.headers.get("Content-Type", "application/vnd.apple.mpegurl")
                is_manifest = (
                    ".m3u8" in url.split("?")[0]
                    or "mpegurl" in ctype.lower()
                )
                if is_manifest:
                    try:
                        text = data.decode("utf-8", errors="replace")
                        origin = self._origin()
                        data = _make_rewriter(origin)(text, url).encode()
                        ctype = "application/vnd.apple.mpegurl"
                    except Exception:
                        pass
                self.send_response(200)
                self._cors()
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(data)
        except Exception as e:
            self.send_error(502, f"upstream: {e}")


class ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


# bind the origin accessor to the handler instance (module-level rewrite needs it)
def _make_rewriter(origin):
    def rewrite_manifest(text, base_url):
        def proxied(u):
            absu = absolutize(u, base_url)
            return origin + urllib.parse.quote(absu, safe="")
        text = URI_ATTR.sub(lambda m: f'URI="{proxied(m.group(1))}"', text)
        out_lines = []
        for line in text.splitlines():
            if line and not line.startswith("#"):
                out_lines.append(proxied(line))
            else:
                out_lines.append(line)
        return "\n".join(out_lines) + "\n"
    return rewrite_manifest


if __name__ == "__main__":
    print(f"Open RedZone spike server on http://0.0.0.0:{PORT} (proxy: /proxy?url=...)")
    print(f"LAN: replace 'localhost' with this machine's IP, e.g. http://<ip>:{PORT}")
    ThreadingServer(("0.0.0.0", PORT), Handler).serve_forever()
