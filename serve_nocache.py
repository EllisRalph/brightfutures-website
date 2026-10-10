"""Tiny no-cache static server for local preview of the built Bright Futures site (serves dist/; run `py _build/build.py` first)."""
import http.server, os
from http.server import ThreadingHTTPServer

PORT = 5180
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist"))

class Handler(http.server.SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()
    def log_message(self, *a):  # quiet
        pass

with ThreadingHTTPServer(("", PORT), Handler) as httpd:
    httpd.daemon_threads = True
    print(f"Bright Futures Recruitment preview at http://localhost:{PORT}")
    httpd.serve_forever()
