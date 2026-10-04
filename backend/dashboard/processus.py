"""Lancement, arrêt et adoption des processus des modules.

Un module est lancé détaché du dashboard (il survit à son arrêt). Son PID et sa date de
création sont notés dans `etat/<id>.json`, pour le retrouver au prochain démarrage.
Arrêter un module, c'est arrêter tout son arbre de processus (`main.py` lance souvent
un second Python ou `uvicorn`), puis tout ce qui écoute encore sur son port."""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import time
from pathlib import Path

import psutil

from . import journal
from .config import Config, Module

WINDOWS = os.name == "nt"


# --------------------------------------------------------------------------- commande


def python_module(module: Module) -> list[str]:
    """Clé `python`, sinon le `.venv` du module, sinon le Python du système (jamais celui du dashboard)."""
    if module.python:
        return [module.python]
    venv = module.dossier / ".venv" / ("Scripts/python.exe" if WINDOWS else "bin/python")
    if venv.exists():
        return [str(venv)]
    if WINDOWS and shutil.which("py"):
        return ["py", "-3"]
    return [shutil.which("python3") or shutil.which("python") or "python"]


def commande(module: Module) -> list[str]:
    return [*python_module(module), *(a.replace("{port}", str(module.port)) for a in module.commande)]


# --------------------------------------------------------------------------- fichier d'état


def _fichier_etat(config: Config, module: Module) -> Path:
    return config.dossier_etat / f"{module.id}.json"


def enregistrer(config: Config, module: Module, proc: psutil.Process) -> None:
    config.dossier_etat.mkdir(parents=True, exist_ok=True)
    donnees = {"pid": proc.pid, "create_time": proc.create_time(), "port": module.port, "lance_le": time.time()}
    _fichier_etat(config, module).write_text(json.dumps(donnees), encoding="utf-8")


def oublier(config: Config, module: Module) -> None:
    _fichier_etat(config, module).unlink(missing_ok=True)


# --------------------------------------------------------------------------- sondes


def vivant(proc: psutil.Process | None) -> bool:
    if proc is None:
        return False
    try:
        return proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
    except psutil.Error:
        return False


def port_ouvert(port: int, delai: float = 0.3) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=delai):
            return True
    except OSError:
        return False


def pid_sur_port(port: int) -> int | None:
    """PID du processus qui écoute sur `port` (None si inconnu ou inaccessible)."""
    try:
        connexions = psutil.net_connections(kind="inet")
    except psutil.Error:
        return None
    for c in connexions:
        if c.laddr and c.laddr.port == port and c.status == psutil.CONN_LISTEN and c.pid:
            return c.pid
    return None


# --------------------------------------------------------------------------- lancement


def lancer(config: Config, module: Module, dashboard_url: str) -> subprocess.Popen:
    fichier = journal.tourner(config.dossier_journaux, module.id)
    env = {**os.environ, "PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8", "DASHBOARD_URL": dashboard_url}
    env.pop("DASHBOARD_ACCESS_CODE", None)  # le code du dashboard ne regarde pas les modules
    options: dict = {"cwd": module.dossier, "env": env, "stdin": subprocess.DEVNULL, "stderr": subprocess.STDOUT}

    with fichier.open("ab") as sortie:
        options["stdout"] = sortie
        if WINDOWS:
            # Pas de fenêtre de console, et le module survit à l'arrêt du dashboard.
            base = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
            try:
                proc = subprocess.Popen(commande(module), creationflags=base | subprocess.CREATE_BREAKAWAY_FROM_JOB,
                                        **options)
            except OSError:
                sortie.write(f"{time.strftime('%H:%M:%S')} WARNING Détachement refusé par Windows : le module "
                             "s'arrêtera avec le dashboard.\n".encode())
                sortie.flush()
                proc = subprocess.Popen(commande(module), creationflags=base, **options)
        else:
            proc = subprocess.Popen(commande(module), start_new_session=True, **options)

    enregistrer(config, module, psutil.Process(proc.pid))
    return proc


# --------------------------------------------------------------------------- adoption


def adopter(config: Config, module: Module) -> psutil.Process | None:
    """Retrouve un module déjà lancé : d'abord par `etat/<id>.json`, sinon par son port."""
    fichier = _fichier_etat(config, module)
    if fichier.exists():
        try:
            donnees = json.loads(fichier.read_text(encoding="utf-8"))
            proc = psutil.Process(int(donnees["pid"]))
            if abs(proc.create_time() - float(donnees["create_time"])) < 0.01 and vivant(proc):
                return proc
        except (ValueError, KeyError, OSError, psutil.Error):
            pass
        oublier(config, module)

    if module.port and port_ouvert(module.port):
        proc = processus_du_module_sur_port(module)
        if proc is not None:
            enregistrer(config, module, proc)
        return proc
    return None


def processus_du_module_sur_port(module: Module) -> psutil.Process | None:
    """Le processus qui écoute sur le port du module, seulement s'il tourne dans le dossier du
    module : un programme étranger qui occuperait le port n'est jamais adopté ni arrêté."""
    pid = pid_sur_port(module.port)
    if not pid or pid == os.getpid():
        return None
    try:
        proc = psutil.Process(pid)
        if not _dans(proc.cwd(), module.dossier):
            return None
        return racine_du_module(proc, module)
    except psutil.Error:
        return None


def _dans(chemin: str, dossier: Path) -> bool:
    try:
        return Path(chemin).resolve().is_relative_to(dossier)
    except (OSError, ValueError):
        return False


def racine_du_module(proc: psutil.Process, module: Module) -> psutil.Process:
    """Remonte vers le `main.py` du module (le processus qui écoute est souvent un enfant).

    On ne remonte que par des processus Python lancés dans le dossier du module, pour ne
    jamais attraper le terminal depuis lequel il a été lancé à la main."""
    courant = proc
    try:
        while (parent := courant.parent()) is not None:
            nom = parent.name().lower()
            if not nom.startswith(("python", "py")) or not _dans(parent.cwd(), module.dossier):
                break
            courant = parent
    except psutil.Error:
        pass
    return courant


# --------------------------------------------------------------------------- arrêt


def _arbre(proc: psutil.Process) -> list[psutil.Process]:
    try:
        return [proc, *proc.children(recursive=True)]
    except psutil.Error:
        return [proc]


def _tuer(processus: list[psutil.Process], delai: float) -> None:
    for p in processus:
        try:
            p.terminate()
        except psutil.Error:
            pass
    _, survivants = psutil.wait_procs(processus, timeout=delai)
    for p in survivants:
        try:
            p.kill()
        except psutil.Error:
            pass
    psutil.wait_procs(survivants, timeout=delai)


def arreter(config: Config, module: Module, proc: psutil.Process | None) -> None:
    if proc is not None and vivant(proc):
        _tuer(_arbre(proc), config.delai_arret)
    # Filet de sécurité : un descendant détaché peut encore tenir le port.
    for _ in range(3):
        restant = processus_du_module_sur_port(module) if module.port else None
        if restant is None:
            break
        _tuer(_arbre(restant), config.delai_arret)
    oublier(config, module)


def adresse_locale() -> str | None:
    """Adresse IP sur le réseau local (aucun paquet n'est envoyé)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            ip = s.getsockname()[0]
        return None if ip.startswith("127.") else ip
    except OSError:
        return None

