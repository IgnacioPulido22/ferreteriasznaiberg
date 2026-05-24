"""
Servidor de desarrollo — Ferretería Sznaiberg
Sirve archivos estáticos + endpoint POST /save-products para guardar cambios del admin.
Uso: python server.py
"""
import http.server
import json
import os
import shutil
from datetime import datetime

PORT = 3131
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_POST(self):
        if self.path == '/save-products':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                products = json.loads(body)

                # Backup del archivo anterior
                dest = os.path.join(BASE_DIR, 'products.json')
                backup_dir = os.path.join(BASE_DIR, '_backups')
                os.makedirs(backup_dir, exist_ok=True)
                if os.path.exists(dest):
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    shutil.copy2(dest, os.path.join(backup_dir, f'products_{ts}.json'))

                # Guardar nuevo catálogo
                with open(dest, 'w', encoding='utf-8') as f:
                    json.dump(products, f, ensure_ascii=False, indent=2)

                self._respond(200, {'ok': True, 'count': len(products)})
                print(f'[GUARDADO] {len(products)} productos → products.json')

            except Exception as e:
                self._respond(500, {'ok': False, 'error': str(e)})
                print(f'[ERROR] {e}')
        else:
            self._respond(404, {'ok': False})

    def _respond(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, fmt, *args):
        # Silencia los GET de archivos estáticos, solo muestra POSTs
        if 'POST' in (args[0] if args else ''):
            super().log_message(fmt, *args)


if __name__ == '__main__':
    os.chdir(BASE_DIR)
    print(f'Ferretería Sznaiberg — servidor corriendo en http://localhost:{PORT}')
    print(f'Admin panel: http://localhost:{PORT}/admin.html')
    print(f'Tienda:      http://localhost:{PORT}/index.html')
    print('Ctrl+C para detener\n')
    with http.server.ThreadingHTTPServer(('', PORT), Handler) as httpd:
        httpd.serve_forever()
