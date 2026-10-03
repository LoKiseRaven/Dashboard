"""Faux module pour les tests : copié en `main.py` dans un dossier temporaire.

Options :
  --port N     port d'écoute
  --host H     adresse d'écoute (défaut : 127.0.0.1)
  --enfant     comme AI-Video-Editor : relance un sous-processus qui, lui, écoute sur le port
  --retard S   attend S secondes avant d'écouter (simule un premier lancement)
  --mourir     s'arrête tout seul avec le code 3 après 0,5 s
Fichiers lus dans le dossier courant à chaque requête :
  taches.json  liste des tâches renvoyée par /api/dashboard/etat
  sans_etat    si présent, /api/dashboard/etat répond 404
"""

import json
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class Gestionnaire(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path == "/api/dashboard/etat" and not Path("sans_etat").exists():
            fichier = Path("taches.json")
            taches = json.loads(fichier.read_text()) if fichier.exists() else []
            corps, code = json.dumps({"version": 1, "taches": taches}).encode(), 200
        elif self.path == "/":
            corps, code = b"<html>faux module</html>", 200
        else:
            corps, code = b"{}", 404
        self.send_response(code)
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)

    def log_message(self, *args):
        pass


def main(argv):
    port = int(argv[argv.index("--port") + 1])
    print(f"faux module sur le port {port}", flush=True)
    if "--mourir" in argv:
        time.sleep(0.5)
        print("adieu", flush=True)
        sys.exit(3)
    if "--retard" in argv:
        time.sleep(float(argv[argv.index("--retard") + 1]))
    if "--enfant" in argv:
        reste = [a for a in argv if a != "--enfant"]
        sys.exit(subprocess.call([sys.executable, __file__, *reste]))
    hote = argv[argv.index("--host") + 1] if "--host" in argv else "127.0.0.1"
    ThreadingHTTPServer((hote, port), Gestionnaire).serve_forever()


if __name__ == "__main__":
    main(sys.argv[1:])
