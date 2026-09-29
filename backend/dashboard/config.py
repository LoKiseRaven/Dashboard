"""Lecture et vérification de `modules.toml` et `config.local.toml`."""

from __future__ import annotations

import os
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
ID_VALIDE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


@dataclass(frozen=True)
class Module:
    id: str
    nom: str
    emoji: str
    dossier: Path
    commande: tuple[str, ...]
    port: int
    gpu: bool = True
    python: str | None = None
    erreur: str | None = None  # configuration invalide : le module reste affiché, en ERROR


@dataclass(frozen=True)
class Config:
    racine: Path
    port: int
    modules: tuple[Module, ...]
    code_acces: str | None = None
    intervalle: float = 2.0
    delai_arret: float = 5.0
    index: dict[str, Module] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "index", {m.id: m for m in self.modules})

    @property
    def dossier_etat(self) -> Path:
        return self.racine / "etat"

    @property
    def dossier_journaux(self) -> Path:
        return self.racine / "journaux"

    def module(self, id_: str) -> Module | None:
        return self.index.get(id_)


class ConfigInvalide(Exception):
    pass


def lire_code_acces(racine: Path) -> str | None:
    """`DASHBOARD_ACCESS_CODE` en priorité, sinon `code_acces` de `config.local.toml`."""
    code = os.environ.get("DASHBOARD_ACCESS_CODE", "").strip()
    if code:
        return code
    local = racine / "config.local.toml"
    if local.exists():
        code = str(tomllib.loads(local.read_text(encoding="utf-8")).get("code_acces", "")).strip()
    return code or None


def _erreur_module(brut: dict, dossier: Path, commande: list, port: object) -> str | None:
    if not brut.get("nom"):
        return "Nom manquant."
    if not commande or not all(isinstance(a, str) for a in commande):
        return "Commande manquante ou invalide."
    if not isinstance(port, int) or not 1 <= port <= 65535:
        return "Port invalide."
    if not dossier.is_dir():
        return f"Dossier introuvable : {dossier}"
    if not (dossier / commande[0]).is_file():
        return f"Fichier introuvable : {dossier / commande[0]}"
    return None


def charger(chemin: Path | None = None) -> Config:
    chemin = chemin or RACINE / "modules.toml"
    racine = chemin.resolve().parent
    donnees = tomllib.loads(chemin.read_text(encoding="utf-8"))
    port_dashboard = int(donnees.get("dashboard", {}).get("port", 8080))

    modules: list[Module] = []
    ports_vus: dict[int, str] = {port_dashboard: "le dashboard"}
    for brut in donnees.get("modules", []):
        id_ = str(brut.get("id", ""))
        if not ID_VALIDE.match(id_) or any(m.id == id_ for m in modules):
            raise ConfigInvalide(f"Identifiant de module invalide ou en double : {id_!r}")
        dossier = (racine / str(brut.get("dossier", ""))).resolve()
        commande = brut.get("commande", [])
        port = brut.get("port")
        erreur = _erreur_module(brut, dossier, commande, port)
        if erreur is None and port in ports_vus:
            erreur = f"Port {port} déjà pris par {ports_vus[port]}."
        if erreur is None:
            ports_vus[port] = str(brut["nom"])
        modules.append(Module(
            id=id_,
            nom=str(brut.get("nom", id_)),
            emoji=str(brut.get("emoji", "🧩")),
            dossier=dossier,
            commande=tuple(str(a) for a in commande) if isinstance(commande, list) else (),
            port=port if isinstance(port, int) else 0,
            gpu=bool(brut.get("gpu", True)),
            python=brut.get("python"),
            erreur=erreur,
        ))
    return Config(racine=racine, port=port_dashboard, modules=tuple(modules), code_acces=lire_code_acces(racine))
