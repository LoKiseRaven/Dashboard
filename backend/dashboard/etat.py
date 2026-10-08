"""Machine à états des modules et boucle de surveillance (spec §6)."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

import httpx
import psutil

from . import journal, processus
from .config import Config, Module

ROUTE_ETAT = "/api/dashboard/etat"
log = logging.getLogger("dashboard")


class Etat(StrEnum):
    OFF = "OFF"
    STARTING = "STARTING"
    ON = "ON"
    WORKING = "WORKING"
    WAITING = "WAITING"
    STOPPING = "STOPPING"
    ERROR = "ERROR"


ALLUMES = {Etat.ON, Etat.WORKING, Etat.WAITING}
OCCUPES = {Etat.WORKING, Etat.WAITING}


class Refus(Exception):
    """Action impossible dans l'état actuel (réponse 409)."""

    def __init__(self, detail: str, taches: list | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.taches = taches


@dataclass
class Suivi:
    module: Module
    etat: Etat = Etat.OFF
    message: str | None = None
    taches: list[dict] = field(default_factory=list)
    detail_disponible: bool = False
    depuis: datetime = field(default_factory=lambda: datetime.now(UTC))
    code_sortie: int | None = None
    proc: psutil.Process | None = None
    popen: subprocess.Popen | None = None  # seulement si le dashboard l'a lancé lui-même
    a_repondu: bool = False
    verrou: asyncio.Lock = field(default_factory=asyncio.Lock)

    def passer(self, etat: Etat, message: str | None = None) -> None:
        if etat != self.etat:
            self.etat = etat
            self.depuis = datetime.now(UTC)
        self.message = message

    def vers_json(self) -> dict:
        m = self.module
        return {
            "id": m.id, "nom": m.nom, "emoji": m.emoji, "port": m.port, "gpu": m.gpu,
            "etat": self.etat.value, "message": self.message, "taches": self.taches,
            "detail_disponible": self.detail_disponible, "depuis": self.depuis.isoformat(),
            "code_sortie": self.code_sortie,
        }


def etat_selon_taches(taches: list[dict]) -> Etat:
    if any(t.get("statut") == "en_cours" for t in taches):
        return Etat.WORKING
    if any(t.get("statut") == "en_attente" for t in taches):
        return Etat.WAITING
    return Etat.ON


def _taches_valides(donnees: object) -> list[dict]:
    if not isinstance(donnees, dict) or not isinstance(donnees.get("taches"), list):
        raise ValueError("réponse d'état invalide")
    return [t for t in donnees["taches"] if isinstance(t, dict)]


class Superviseur:
    def __init__(self, config: Config, dashboard_url: str, client: httpx.AsyncClient | None = None) -> None:
        self.config = config
        self.dashboard_url = dashboard_url
        self.client = client or httpx.AsyncClient(timeout=1.0)
        self.suivis = {m.id: Suivi(m) for m in config.modules}
        self._boucle: asyncio.Task | None = None
        self._arrets: set[asyncio.Task] = set()

    # ------------------------------------------------------------------ cycle de vie

    async def demarrer_surveillance(self) -> None:
        for suivi in self.suivis.values():
            if suivi.module.erreur:
                suivi.passer(Etat.ERROR, suivi.module.erreur)
            else:
                suivi.proc = await asyncio.to_thread(processus.adopter, self.config, suivi.module)
                if suivi.proc is not None:
                    log.info("%s : déjà allumé, repris par le dashboard.", suivi.module.nom)
        await self.rafraichir_tout()
        self._boucle = asyncio.create_task(self._tourner())

    async def fermer(self) -> None:
        """Arrête la surveillance ; les modules, eux, continuent de tourner (spec §5.4)."""
        if self._boucle:
            self._boucle.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._boucle
        for tache in list(self._arrets):
            with contextlib.suppress(asyncio.CancelledError):
                await tache
        await self.client.aclose()

    async def _tourner(self) -> None:
        while True:
            await asyncio.sleep(self.config.intervalle)
            await self.rafraichir_tout()

    async def rafraichir_tout(self) -> None:
        await asyncio.gather(*(self.rafraichir(s) for s in self.suivis.values()))

    # ------------------------------------------------------------------ interrogation

    async def interroger(self, module: Module) -> tuple[bool, list[dict] | None]:
        """(répond, tâches). `tâches` vaut None si l'app n'expose pas (encore) la route d'état."""
        try:
            r = await self.client.get(f"http://127.0.0.1:{module.port}{ROUTE_ETAT}")
        except httpx.HTTPError:
            return False, None
        if r.status_code != 200:
            return True, None
        try:
            return True, _taches_valides(r.json())
        except ValueError:
            return True, None

    async def rafraichir(self, suivi: Suivi) -> None:
        if suivi.module.erreur or suivi.verrou.locked():
            return
        async with suivi.verrou:
            await self._rafraichir(suivi)

    async def _rafraichir(self, suivi: Suivi) -> None:
        module = suivi.module
        if suivi.popen is not None:
            suivi.popen.poll()  # récupère le code de sortie (et évite un processus zombie)

        if not processus.vivant(suivi.proc):
            if suivi.proc is not None and suivi.etat != Etat.STOPPING:
                self._mort_inattendue(suivi)
                return
            if suivi.etat == Etat.ERROR:
                return
            # Module lancé hors du dashboard (à la main) : on l'adopte s'il écoute sur son port.
            if processus.port_ouvert(module.port):
                suivi.proc = await asyncio.to_thread(processus.adopter, self.config, module)
            if suivi.proc is None:
                suivi.taches, suivi.detail_disponible = [], False
                suivi.passer(Etat.OFF)
                return

        repond, taches = await self.interroger(module)
        if not repond:
            suivi.taches = []
            if suivi.a_repondu:
                suivi.passer(Etat.ON, "Ne répond plus.")
            else:
                suivi.passer(Etat.STARTING)
            return
        suivi.a_repondu = True
        suivi.detail_disponible = taches is not None
        suivi.taches = taches or []
        suivi.passer(etat_selon_taches(suivi.taches), None if taches is not None else "État détaillé indisponible.")

    def _mort_inattendue(self, suivi: Suivi) -> None:
        code = suivi.popen.returncode if suivi.popen is not None else None
        fin = journal.fin(journal.chemin(self.config.dossier_journaux, suivi.module.id), 20)
        suivi.code_sortie = code
        suivi.proc, suivi.popen, suivi.taches, suivi.a_repondu = None, None, [], False
        processus.oublier(self.config, suivi.module)
        texte = "Le module s'est arrêté de façon inattendue" + (f" (code {code})." if code is not None else ".")
        log.warning("%s : %s", suivi.module.nom, texte[0].lower() + texte[1:])
        suivi.passer(Etat.ERROR, "\n".join([texte, *fin]) if fin else texte)

    # ------------------------------------------------------------------ actions

    def suivi(self, id_: str) -> Suivi | None:
        return self.suivis.get(id_)

    async def allumer(self, suivi: Suivi) -> None:
        module = suivi.module
        if module.erreur:
            raise Refus(module.erreur)
        async with suivi.verrou:
            if suivi.etat not in (Etat.OFF, Etat.ERROR):
                raise Refus(f"{module.nom} est déjà allumé.")
            if processus.port_ouvert(module.port):
                raise Refus(f"Impossible d'allumer {module.nom} : le port {module.port} est déjà utilisé.")
            try:
                popen = await asyncio.to_thread(processus.lancer, self.config, module, self.dashboard_url)
            except OSError as e:
                raise Refus(f"Impossible d'allumer {module.nom} : {e}") from e
            suivi.popen, suivi.proc = popen, psutil.Process(popen.pid)
            suivi.code_sortie, suivi.a_repondu, suivi.taches = None, False, []
            suivi.passer(Etat.STARTING)
            log.info("%s : allumage (port %s).", module.nom, module.port)

    async def eteindre(self, suivi: Suivi, force: bool) -> None:
        module = suivi.module
        async with suivi.verrou:
            if suivi.etat in (Etat.OFF, Etat.ERROR, Etat.STOPPING):
                raise Refus(f"{module.nom} n'est pas allumé.")
            # On revérifie auprès du module : une tâche a pu démarrer depuis le dernier passage.
            repond, taches = await self.interroger(module)
            if repond and taches is not None:
                suivi.taches = taches
                suivi.passer(etat_selon_taches(taches))
            if suivi.etat in OCCUPES and not force:
                raise Refus(f"{module.nom} a une tâche en cours.", suivi.taches)
            suivi.passer(Etat.STOPPING)
            interrompue = " (tâche en cours interrompue)" if force and suivi.taches else ""
            log.info("%s : arrêt demandé%s.", module.nom, interrompue)

        tache = asyncio.create_task(self._eteindre(suivi))
        self._arrets.add(tache)
        tache.add_done_callback(self._arrets.discard)

    async def _eteindre(self, suivi: Suivi) -> None:
        async with suivi.verrou:
            try:
                await asyncio.to_thread(processus.arreter, self.config, suivi.module, suivi.proc)
            finally:
                if suivi.popen is not None:
                    suivi.popen.poll()
                suivi.proc, suivi.popen, suivi.taches, suivi.a_repondu = None, None, [], False
                suivi.detail_disponible = False
                suivi.passer(Etat.OFF)
                log.info("%s : éteint.", suivi.module.nom)
