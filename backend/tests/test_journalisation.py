import io
import json
import logging
import logging.config
import re
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[1] / "journalisation.json"


def test_format_commun_sans_requetes(monkeypatch):
    sortie = io.StringIO()
    monkeypatch.setattr("sys.stdout", sortie)
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    racine = logging.getLogger()
    anciens = (racine.handlers[:], racine.level)
    try:
        logging.config.dictConfig(config)
        logging.getLogger("dashboard").info("Montage IA : éteint.")
        logging.getLogger("uvicorn.access").info('127.0.0.1:5000 - "GET /api/modules HTTP/1.1" 200')
        logging.getLogger("httpx").info("HTTP Request: GET http://127.0.0.1:8083/api/dashboard/etat")
        logging.getLogger("uvicorn.error").info("Uvicorn running on http://0.0.0.0:8080")
        lignes = sortie.getvalue().splitlines()
    finally:
        racine.handlers[:] = anciens[0]
        racine.setLevel(anciens[1])
    assert len(lignes) == 1
    assert re.fullmatch(r"\d\d:\d\d:\d\d INFO    Montage IA : éteint\.", lignes[0])
