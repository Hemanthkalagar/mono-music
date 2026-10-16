import http.server
import socketserver
import urllib.parse
import os
import sys

# Ensure root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.index import handler

PORT = int(os.environ.get('PORT', 3000))

class LocalDevHandler(handler, http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        http.server.SimpleHTTPRequestHandler.end_headers(self)

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/favicon.ico':
            svg_data = b"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='48' fill='%23111111'/><circle cx='50' cy='50' r='18' fill='%23faf9f5'/><circle cx='50' cy='50' r='6' fill='%23111111'/></svg>"
            self.send_response(200)
            self.send_header('Content-Type', 'image/svg+xml')
            self.send_header('Content-Length', str(len(svg_data)))
            self.end_headers()
            self.wfile.write(svg_data)
            return

        if parsed.path in ('/mobile', '/mobile/'):
            self.path = '/mobile.html'
            return http.server.SimpleHTTPRequestHandler.do_GET(self)

        if parsed.path.startswith('/api/'):
            return handler.do_GET(self)

        return http.server.SimpleHTTPRequestHandler.do_GET(self)

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

if __name__ == '__main__':
    with ThreadedHTTPServer(("", PORT), LocalDevHandler) as httpd:
        print(f"mono Music Local Server listening on http://localhost:{PORT}")
        httpd.serve_forever()
