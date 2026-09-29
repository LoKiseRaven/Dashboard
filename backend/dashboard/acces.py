"""Code d'accès du dashboard : saisi une fois par appareil, mémorisé 30 jours.

Le cookie contient un HMAC du code (pas le code lui-même) : il reste valide après un
redémarrage du serveur et devient invalide dès que le code change. Les requêtes venant
du PC lui-même (127.0.0.1, ::1) passent sans code."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from pathlib import Path

COOKIE = "dashboard_acces"  # nom propre au dashboard : les cookies sont partagés entre ports
DUREE_COOKIE = 30 * 24 * 3600
SEUIL_ECHECS = 5
PAUSE_SECONDES = 2.0
ADRESSES_LOCALES = {"127.0.0.1", "::1", "::ffff:127.0.0.1"}


def charger_secret(path: Path) -> bytes:
    if path.exists():
        data = path.read_bytes()
        if len(data) >= 32:
            return data
    path.parent.mkdir(parents=True, exist_ok=True)
    data = secrets.token_bytes(32)
    path.write_bytes(data)
    return data


def jeton(code: str, secret: bytes) -> str:
    return hmac.new(secret, code.encode("utf-8"), hashlib.sha256).hexdigest()


def jeton_valide(valeur: str | None, code: str | None, secret: bytes) -> bool:
    return bool(valeur) and code is not None and hmac.compare_digest(valeur, jeton(code, secret))


def code_correct(saisi: str, code: str | None) -> bool:
    return code is not None and hmac.compare_digest(saisi.encode("utf-8"), code.encode("utf-8"))


def est_local(ip: str | None) -> bool:
    return ip in ADRESSES_LOCALES


class LimiteurEchecs:
    """À partir du 5ᵉ échec depuis une même adresse, chaque tentative attend 2 s."""

    def __init__(self) -> None:
        self._echecs: dict[str, int] = {}

    def pause_avant(self, ip: str) -> float:
        return PAUSE_SECONDES if self._echecs.get(ip, 0) >= SEUIL_ECHECS else 0.0

    def echec(self, ip: str) -> None:
        self._echecs[ip] = self._echecs.get(ip, 0) + 1

    def succes(self, ip: str) -> None:
        self._echecs.pop(ip, None)
