"""Lance le Dashboard : `python main.py`.

Au premier lancement, crée l'environnement Python `backend/.venv` et y installe
`backend/requirements.txt`, puis demande le code d'accès du dashboard et l'enregistre
dans `config.local.toml`. Compile l'interface (`frontend/dist`) si elle manque ou est
plus ancienne que ses sources. Démarre ensuite le serveur et affiche l'adresse à ouvrir,
y compris depuis un téléphone sur le même Wi-Fi.

Les modules allumés depuis le dashboard continuent de tourner quand il s'arrête.

Ce fichier n'utilise que la bibliothèque standard : il tourne avec n'importe quel
Python 3.11 à 3.13, avant même que les dépendances soient installées.
"""

import getpass
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import tomllib
from pathlib import Path

RACINE = Path(__file__).resolve().parent
BACKEND = RACINE / "backend"
FRONTEND = RACINE / "frontend"
VENV = BACKEND / ".venv"
REQUIREMENTS = BACKEND / "requirements.txt"
MARQUEUR = VENV / ".installe"
CONFIG_LOCALE = RACINE / "config.local.toml"
VERSIONS = ((3, 11), (3, 13))


def journal(message: str, niveau: str = "INFO") -> None:
    """Même format que les journaux du serveur et des modules : « 14:02:11 INFO    message »."""
    print(f"{time.strftime('%H:%M:%S')} {niveau:<7} {message}", flush=True)


def python_venv() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def verifier_python() -> None:
    if not VERSIONS[0] <= sys.version_info[:2] <= VERSIONS[1]:
        sys.exit(f"Python {sys.version.split()[0]} détecté : il faut Python 3.11, 3.12 ou 3.13 "
                 "(https://www.python.org/downloads/).")


def lancer(cmd: list[str | Path], cwd: Path | None = None) -> None:
    res = subprocess.run([str(c) for c in cmd], cwd=cwd)
    if res.returncode != 0:
        sys.exit(f"Échec de la commande : {' '.join(str(c) for c in cmd)}")


def preparer_python() -> None:
    if not python_venv().exists():
        journal("Création de l'environnement Python (backend/.venv)…")
        lancer([sys.executable, "-m", "venv", VENV])
    if not MARQUEUR.exists() or REQUIREMENTS.stat().st_mtime > MARQUEUR.stat().st_mtime:
        journal("Installation des dépendances Python…")
        lancer([python_venv(), "-m", "pip", "install", "--quiet", "--upgrade", "pip"])
        lancer([python_venv(), "-m", "pip", "install", "--quiet", "-r", REQUIREMENTS])
        MARQUEUR.touch()


def interface_perimee() -> bool:
    index = FRONTEND / "dist" / "index.html"
    if not index.exists():
        return True
    date = index.stat().st_mtime
    sources = [FRONTEND / "index.html", FRONTEND / "package.json", *(FRONTEND / "src").rglob("*")]
    return any(p.is_file() and p.stat().st_mtime > date for p in sources)


def preparer_interface() -> None:
    if not (FRONTEND / "package.json").exists() or not interface_perimee():
        return
    npm = shutil.which("npm")
    if npm is None:
        if (FRONTEND / "dist" / "index.html").exists():
            journal("npm introuvable : l'interface existante (peut-être ancienne) est utilisée.", "WARNING")
            return
        sys.exit("npm introuvable : installe Node.js (https://nodejs.org) pour compiler l'interface.")
    if not (FRONTEND / "node_modules").exists():
        journal("Installation des dépendances de l'interface…")
        lancer([npm, "install", "--silent"], cwd=FRONTEND)
    journal("Compilation de l'interface…")
    lancer([npm, "run", "build", "--silent"], cwd=FRONTEND)


def code_acces() -> str | None:
    code = os.environ.get("DASHBOARD_ACCESS_CODE", "").strip()
    if not code and CONFIG_LOCALE.exists():
        code = str(tomllib.loads(CONFIG_LOCALE.read_text(encoding="utf-8")).get("code_acces", "")).strip()
    return code or None


def demander_code() -> str | None:
    """Premier lancement : demande le code dans la console et l'enregistre (spec §10.1)."""
    if not sys.stdin or not sys.stdin.isatty():
        return None
    print("Premier lancement : choisis le code d'accès du dashboard (demandé sur les autres appareils).")
    while True:
        code = getpass.getpass("Code d'accès : ").strip()
        if len(code) < 4:
            print("Au moins 4 caractères.")
            continue
        if getpass.getpass("Confirme le code : ").strip() != code:
            print("Les deux saisies diffèrent, recommence.")
            continue
        break
    # Une chaîne JSON est une chaîne TOML valide (guillemets et échappements compatibles).
    CONFIG_LOCALE.write_text(f"code_acces = {json.dumps(code, ensure_ascii=False)}\n", encoding="utf-8")
    journal("Code enregistré dans config.local.toml.")
    return code


def adresse_locale() -> str | None:
    """Adresse IP sur le réseau local (aucun paquet n'est envoyé)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            ip = s.getsockname()[0]
        return None if ip.startswith("127.") else ip
    except OSError:
        return None


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):  # console Windows en cp1252 : pas de plantage sur « » ou les emojis
        sys.stdout.reconfigure(errors="replace")

    verifier_python()
    preparer_python()
    preparer_interface()

    port = int(tomllib.loads((RACINE / "modules.toml").read_text(encoding="utf-8")).get("dashboard", {})
               .get("port", 8080))
    reseau = bool(code_acces() or demander_code())
    hote = "0.0.0.0" if reseau else "127.0.0.1"

    journal(f"Dashboard : http://localhost:{port}")
    ip = adresse_locale()
    if not reseau:
        journal("Aucun code d'accès défini : le dashboard n'est accessible que depuis ce PC.", "WARNING")
    elif ip:
        journal(f"Depuis ton téléphone (même Wi-Fi) : http://{ip}:{port}")
    journal("Ctrl+C pour arrêter (les modules allumés continuent de tourner).")
    try:
        subprocess.run([str(python_venv()), "-m", "uvicorn", "--factory", "dashboard.app:creer_app_defaut",
                        "--host", hote, "--port", str(port),
                        # Journal au format commun, sans une ligne par requête GET/POST.
                        "--log-config", str(BACKEND / "journalisation.json"), "--no-access-log"], cwd=BACKEND)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
