"""Journaux des modules : `journaux/<id>.log` (lancement en cours) et `<id>.log.1` (précédent)."""

from __future__ import annotations

from pathlib import Path

TAILLE_LECTURE = 256 * 1024


def chemin(dossier: Path, id_: str) -> Path:
    return dossier / f"{id_}.log"


def tourner(dossier: Path, id_: str) -> Path:
    """Renomme le journal courant en `.log.1` et renvoie le chemin du nouveau."""
    dossier.mkdir(parents=True, exist_ok=True)
    actuel = chemin(dossier, id_)
    if actuel.exists():
        actuel.replace(actuel.with_suffix(".log.1"))
    return actuel


def fin(fichier: Path, lignes: int = 200) -> list[str]:
    """Les `lignes` dernières lignes du fichier (lecture limitée à la fin du fichier)."""
    if lignes <= 0 or not fichier.exists():
        return []
    with fichier.open("rb") as f:
        f.seek(0, 2)
        taille = f.tell()
        f.seek(max(0, taille - TAILLE_LECTURE))
        brut = f.read()
    texte = brut.decode("utf-8", errors="replace").replace("\r\n", "\n")
    decoupe = texte.split("\n")
    if taille > TAILLE_LECTURE:
        decoupe = decoupe[1:]  # première ligne probablement tronquée
    if decoupe and decoupe[-1] == "":
        decoupe.pop()
    # Les barres de progression (pip, npm…) réécrivent la ligne avec \r : on garde le dernier état.
    return [ligne.rsplit("\r", 1)[-1] for ligne in decoupe[-lignes:]]
