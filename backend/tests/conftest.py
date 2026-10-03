import dataclasses
import shutil
import socket
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from dashboard import processus
from dashboard.app import creer_app
from dashboard.config import charger

FAUX_MODULE = Path(__file__).parent / "faux_module.py"
LOCAL = ("127.0.0.1", 50000)
DISTANT = ("192.168.1.20", 50000)


def port_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Installation:
    """Un dossier de dashboard temporaire, avec des faux modules à côté."""

    def __init__(self, racine: Path) -> None:
        self.racine = racine
        self.modules: dict[str, dict] = {}
        (racine / "Dashboard").mkdir()

    @property
    def dossier_dashboard(self) -> Path:
        return self.racine / "Dashboard"

    def ajouter(self, id_: str, *options: str, dossier: str | None = None) -> dict:
        dossier_module = self.racine / (dossier or id_)
        if dossier is None:
            dossier_module.mkdir()
            shutil.copy(FAUX_MODULE, dossier_module / "main.py")
        self.modules[id_] = {"id": id_, "dossier": dossier_module, "port": port_libre(), "options": list(options)}
        return self.modules[id_]

    def ecrire(self, code: str | None = None) -> Path:
        lignes = ["[dashboard]", f"port = {port_libre()}", ""]
        for m in self.modules.values():
            commande = ", ".join(f'"{a}"' for a in ["main.py", "--port", "{port}", *m["options"]])
            python = sys.executable.replace("\\", "\\\\")
            lignes += [
                "[[modules]]", f'id = "{m["id"]}"', f'nom = "Module {m["id"]}"', 'emoji = "🧪"',
                f'dossier = "../{m["dossier"].name}"', f"commande = [{commande}]", f'port = {m["port"]}',
                f'python = "{python}"', "",
            ]
        chemin = self.dossier_dashboard / "modules.toml"
        chemin.write_text("\n".join(lignes), encoding="utf-8")
        if code is not None:
            (self.dossier_dashboard / "config.local.toml").write_text(f'code_acces = "{code}"\n', encoding="utf-8")
        return chemin

    def config(self, code: str | None = None):
        config = charger(self.ecrire(code))
        return dataclasses.replace(config, intervalle=0.1, delai_arret=2.0)

    def client(self, code: str | None = None, adresse=LOCAL) -> TestClient:
        return TestClient(creer_app(self.config(code), dossier_front=self.racine / "pas-de-front"), client=adresse)


@pytest.fixture
def installation(tmp_path, monkeypatch):
    monkeypatch.delenv("DASHBOARD_ACCESS_CODE", raising=False)
    inst = Installation(tmp_path)
    yield inst
    # Ménage : aucun faux module ne doit survivre au test.
    config = charger(inst.dossier_dashboard / "modules.toml") if (inst.dossier_dashboard / "modules.toml").exists() \
        else None
    if config:
        for module in config.modules:
            if not module.erreur:
                processus.arreter(config, module, processus.adopter(config, module))


def attendre(condition, delai: float = 15.0, pas: float = 0.05):
    fin = time.monotonic() + delai
    while time.monotonic() < fin:
        valeur = condition()
        if valeur:
            return valeur
        time.sleep(pas)
    raise AssertionError("condition jamais remplie")


def attendre_etat(client: TestClient, id_: str, *etats: str, delai: float = 15.0) -> dict:
    def lire():
        m = client.get(f"/api/modules/{id_}").json()
        return m if m["etat"] in etats else None
    return attendre(lire, delai)
