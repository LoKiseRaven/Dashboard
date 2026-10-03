import time

from dashboard import acces
from dashboard.config import lire_code_acces

from .conftest import DISTANT, LOCAL


def test_distant_sans_cookie_refuse(installation):
    with installation.client(code="1234", adresse=DISTANT) as c:
        assert c.get("/api/modules").status_code == 401
        assert c.get("/api/sante").json() == {"ok": True}
        assert c.get("/api/session").json() == {"connecte": False, "local": False}


def test_pc_local_sans_code(installation):
    with installation.client(code="1234", adresse=LOCAL) as c:
        assert c.get("/api/modules").status_code == 200
        assert c.get("/api/session").json() == {"connecte": True, "local": True}


def test_connexion_et_deconnexion(installation):
    with installation.client(code="1234", adresse=DISTANT) as c:
        assert c.post("/api/connexion", json={"code": "faux"}).status_code == 401
        r = c.post("/api/connexion", json={"code": "1234"})
        assert r.status_code == 204
        cookie = r.cookies[acces.COOKIE]
        assert "1234" not in cookie
        assert c.get("/api/modules").status_code == 200
        c.post("/api/deconnexion")
        c.cookies.clear()
        assert c.get("/api/modules").status_code == 401


def test_changer_le_code_invalide_les_cookies(installation):
    with installation.client(code="1234", adresse=DISTANT) as c:
        cookie = c.post("/api/connexion", json={"code": "1234"}).cookies[acces.COOKIE]
    with installation.client(code="5678", adresse=DISTANT) as c:
        c.cookies.set(acces.COOKIE, cookie)
        assert c.get("/api/modules").status_code == 401


def test_pause_apres_cinq_echecs(installation, monkeypatch):
    monkeypatch.setattr(acces, "PAUSE_SECONDES", 0.3)
    with installation.client(code="1234", adresse=DISTANT) as c:
        for _ in range(acces.SEUIL_ECHECS):
            c.post("/api/connexion", json={"code": "faux"})
        debut = time.monotonic()
        assert c.post("/api/connexion", json={"code": "1234"}).status_code == 204
        assert time.monotonic() - debut >= 0.3
        debut = time.monotonic()
        c.post("/api/connexion", json={"code": "faux"})
        assert time.monotonic() - debut < 0.3  # compteur remis à zéro après la réussite


def test_sans_code_configure_personne_ne_se_connecte_a_distance(installation):
    with installation.client(code=None, adresse=DISTANT) as c:
        assert c.post("/api/connexion", json={"code": ""}).status_code == 401
        assert c.get("/api/modules").status_code == 401


def test_code_variable_d_environnement_prioritaire(tmp_path, monkeypatch):
    (tmp_path / "config.local.toml").write_text('code_acces = "fichier"\n')
    monkeypatch.delenv("DASHBOARD_ACCESS_CODE", raising=False)
    assert lire_code_acces(tmp_path) == "fichier"
    monkeypatch.setenv("DASHBOARD_ACCESS_CODE", "env")
    assert lire_code_acces(tmp_path) == "env"


def test_interface_non_compilee_et_repli_spa(installation, tmp_path):
    front = tmp_path / "front"
    front.mkdir()
    (front / "index.html").write_text("<html>dashboard</html>")
    (front / "a.js").write_text("js")
    from fastapi.testclient import TestClient

    from dashboard.app import creer_app
    with TestClient(creer_app(installation.config(), dossier_front=front), client=LOCAL) as c:
        assert c.get("/module/editor").text == "<html>dashboard</html>"
        assert c.get("/a.js").text == "js"
        assert c.get("/../secret").text == "<html>dashboard</html>"
    with installation.client() as c:
        assert c.get("/").status_code == 404
