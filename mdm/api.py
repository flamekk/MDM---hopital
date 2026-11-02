"""API locale de consultation, sans mutation, accessible sur 127.0.0.1 seulement."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from urllib.parse import urlsplit
from . import store


def serve(root, port=8080):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = urlsplit(self.path).path.rstrip('/')
            try:
                if path == '/api/health':
                    result = {'status': 'ok', 'audit_valid': store.verify(root)}
                elif path == '/api/runs':
                    result = store.list_runs(root)
                elif path.startswith('/api/runs/'):
                    parts = path.split('/')
                    payload = store.load_run(root, parts[3])
                    resource = parts[4] if len(parts) == 5 else None
                    if resource not in {'masters', 'xrefs', 'catalogue', 'quality', 'metrics'}:
                        self.send_error(404)
                        return
                    result = payload[resource]
                else:
                    self.send_error(404)
                    return
                body = json.dumps(result, ensure_ascii=False).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except ValueError as exc:
                self.send_error(404, str(exc))
    print(f'API : http://127.0.0.1:{port}/api/health', flush=True)
    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()
