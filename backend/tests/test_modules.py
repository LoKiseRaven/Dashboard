import json
import socket
import subprocess
import sys

import psutil

from dashboard import processus

from .conftest import attendre, attendre_etat


def arbre(pid: int) -> list[psutil.Process]:
    racine = psutil.Process(pid)
    return [racine, *racine.children(recursive=True)]


def pid_enregistre(installation, id_: str) -> int:
    return json.loads((installation.dossier_dashboard / "etat" / f"{id_}.json").read_text())["pid"]


def test_off_par_defaut(installation):
    installation.ajouter("a")
    with installation.client() as c:
        modules = c.get("/api/modules").json()
    assert [(m["id"], m["etat"], m["emoji"]) for m in modules] == [("a", "OFF", "🧪")]


def test_allumer_puis_eteindre_tout_l_arbre(installation):
    m = installation.ajouter("a", "--enfant")
    with installation.client() as c:
        r = c.post("/api/modules/a/demarrer")
        assert r.status_code == 202 and r.json()["etat"] == "STARTING"
        etat = attendre_etat(c, "a", "ON")
        assert etat["detail_disponible"] is True and etat["taches"] == []

        def arbre_complet():
            processus_lances = arbre(pid_enregistre(installation, "a"))
            return processus_lances if len(processus_lances) >= 2 else None

        processus_du_module = attendre(arbre_complet)
        assert c.post("/api/modules/a/arreter", json={"force": False}).status_code == 202
        attendre_etat(c, "a", "OFF")

    _, vivants = psutil.wait_procs(processus_du_module, timeout=5)
    assert vivants == []
    assert not processus.port_ouvert(m["port"])
    assert not (installation.dossier_dashboard / "etat" / "a.json").exists()


def test_starting_tant_que_le_port_ne_repond_pas(installation):
    installation.ajouter("a", "--retard", "1.5")
    with installation.client() as c:
        c.post("/api/modules/a/demarrer")
        assert c.get("/api/modules/a").json()["etat"] == "STARTING"
        attendre_etat(c, "a", "ON")


def test_refus_si_tache_en_cours_puis_arret_force(installation):
    m = installation.ajouter("a")
    tache = {"id": "t1", "libelle": "Génération", "etape": "1/3", "progression": 42, "gpu": True,
             "statut": "en_cours", "position_file": None, "debut": "2026-09-29T10:00:00Z"}
    (m["dossier"] / "taches.json").write_text(json.dumps([tache]))
    with installation.client() as c:
        c.post("/api/modules/a/demarrer")
        etat = attendre_etat(c, "a", "WORKING")
        assert etat["taches"][0]["progression"] == 42

        r = c.post("/api/modules/a/arreter", json={"force": False})
        assert r.status_code == 409
        assert r.json()["taches"][0]["libelle"] == "Génération"
        assert c.get("/api/modules/a").json()["etat"] == "WORKING"

        assert c.post("/api/modules/a/arreter", json={"force": True}).status_code == 202
        attendre_etat(c, "a", "OFF")


def test_refus_si_une_tache_demarre_juste_avant_l_arret(installation):
    m = installation.ajouter("a")
    with installation.client() as c:
        c.post("/api/modules/a/demarrer")
        attendre_etat(c, "a", "ON")
        # Le dashboard croit encore le module libre : l'arrêt doit revérifier auprès de lui.
        (m["dossier"] / "taches.json").write_text(json.dumps([{"id": "t", "libelle": "x", "statut": "en_cours"}]))
        assert c.post("/api/modules/a/arreter").status_code == 409


def test_waiting_si_seulement_en_file(installation):
    m = installation.ajouter("a")
    (m["dossier"] / "taches.json").write_text(json.dumps([{"id": "t", "libelle": "x", "statut": "en_attente",
                                                          "position_file": 2}]))
    with installation.client() as c:
        c.post("/api/modules/a/demarrer")
        attendre_etat(c, "a", "WAITING")
        assert c.post("/api/modules/a/arreter").status_code == 409


def test_app_sans_route_d_etat(installation):
    m = installation.ajouter("a")
    (m["dossier"] / "sans_etat").touch()
    with installation.client() as c:
        c.post("/api/modules/a/demarrer")
        etat = attendre_etat(c, "a", "ON")
        assert etat["detail_disponible"] is False
        assert etat["message"] == "État détaillé indisponible."


def test_mort_inattendue_donne_error_puis_relance_possible(installation):
    installation.ajouter("a", "--mourir")
    with installation.client() as c:
        c.post("/api/modules/a/demarrer")
        etat = attendre_etat(c, "a", "ERROR")
        assert etat["code_sortie"] == 3
        assert "adieu" in etat["message"]
        assert c.post("/api/modules/a/demarrer").status_code == 202


def test_journal(installation):
    m = installation.ajouter("a")
    with installation.client() as c:
        c.post("/api/modules/a/demarrer")
        attendre_etat(c, "a", "ON")
        lignes = c.get("/api/modules/a/journal?lignes=50").json()["lignes"]
    assert f"faux module sur le port {m['port']}" in lignes


def test_le_module_survit_au_dashboard_et_est_adopte(installation):
    installation.ajouter("a", "--enfant")
    with installation.client() as c:
        c.post("/api/modules/a/demarrer")
        attendre_etat(c, "a", "ON")
    pid = pid_enregistre(installation, "a")
    assert psutil.pid_exists(pid)

    with installation.client() as c:
        assert c.get("/api/modules/a").json()["etat"] == "ON"
        c.post("/api/modules/a/arreter")
        attendre_etat(c, "a", "OFF")
    assert not psutil.pid_exists(pid) or psutil.Process(pid).status() == psutil.STATUS_ZOMBIE


def test_module_lance_a_la_main_est_adopte(installation):
    m = installation.ajouter("a")
    proc = subprocess.Popen([sys.executable, "main.py", "--port", str(m["port"])], cwd=m["dossier"],
                            stdout=subprocess.DEVNULL)
    try:
        attendre(lambda: processus.port_ouvert(m["port"]))
        with installation.client() as c:
            attendre_etat(c, "a", "ON")
            c.post("/api/modules/a/arreter")
            attendre_etat(c, "a", "OFF")
        assert proc.wait(timeout=5) is not None
    finally:
        proc.kill()


def test_programme_etranger_sur_le_port_n_est_jamais_adopte(installation):
    m = installation.ajouter("a")
    with socket.socket() as s:
        s.bind(("127.0.0.1", m["port"]))
        s.listen()
        with installation.client() as c:
            assert c.get("/api/modules/a").json()["etat"] == "OFF"
            r = c.post("/api/modules/a/demarrer")
            assert r.status_code == 409
            assert "déjà utilisé" in r.json()["detail"]


def test_config_invalide(installation):
    installation.ajouter("a", dossier="inexistant")
    installation.ajouter("b")
    with installation.client() as c:
        a = c.get("/api/modules/a").json()
        assert a["etat"] == "ERROR" and "introuvable" in a["message"]
        assert c.post("/api/modules/a/demarrer").status_code == 409
        assert c.get("/api/modules/b").json()["etat"] == "OFF"


def test_double_demarrage_refuse(installation):
    installation.ajouter("a")
    with installation.client() as c:
        assert c.post("/api/modules/a/demarrer").status_code == 202
        assert c.post("/api/modules/a/demarrer").status_code == 409
        assert c.post("/api/modules/a/arreter").status_code in (202, 409)
        attendre_etat(c, "a", "OFF", "STARTING", "ON")


def test_module_inconnu(installation):
    installation.ajouter("a")
    with installation.client() as c:
        assert c.get("/api/modules/zz").status_code == 404
        assert c.post("/api/modules/zz/demarrer").status_code == 404
        assert c.get("/api/inconnue").status_code == 404
