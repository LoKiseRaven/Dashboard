"""Application FastAPI : API `/api/*` (spec §8) et service de `frontend/dist`."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel

from . import acces, journal, processus
from .config import Config, charger
from .etat import Refus, Suivi, Superviseur

ROUTES_LIBRES = {"/api/sante", "/api/session", "/api/connexion"}


class DemandeArret(BaseModel):
    force: bool = False


class DemandeConnexion(BaseModel):
    code: str


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def creer_app(config: Config, superviseur: Superviseur | None = None, dossier_front: Path | None = None) -> FastAPI:
    ip = processus.adresse_locale() or "127.0.0.1"
    sup = superviseur or Superviseur(config, dashboard_url=f"http://{ip}:{config.port}")
    secret = acces.charger_secret(config.dossier_etat / "secret.bin")
    limiteur = acces.LimiteurEchecs()
    dossier_front = dossier_front if dossier_front is not None else config.racine / "frontend" / "dist"

    @asynccontextmanager
    async def cycle(_: FastAPI) -> AsyncIterator[None]:
        await sup.demarrer_surveillance()
        yield
        await sup.fermer()

    app = FastAPI(title="Dashboard", lifespan=cycle)
    app.state.superviseur = sup

    def autorise(request: Request) -> bool:
        return acces.est_local(_ip(request)) or acces.jeton_valide(
            request.cookies.get(acces.COOKIE), config.code_acces, secret)

    @app.middleware("http")
    async def verifier_acces(request: Request, call_next):
        chemin = request.url.path
        if chemin.startswith("/api/") and chemin not in ROUTES_LIBRES and not autorise(request):
            return JSONResponse({"detail": "Code d'accès requis."}, status_code=401)
        return await call_next(request)

    def trouver(id_: str) -> Suivi:
        suivi = sup.suivi(id_)
        if suivi is None:
            raise HTTPException(404, "Module inconnu.")
        return suivi

    # ------------------------------------------------------------------ accès

    @app.get("/api/sante")
    async def sante() -> dict:
        return {"ok": True}

    @app.get("/api/session")
    async def session(request: Request) -> dict:
        return {"connecte": autorise(request), "local": acces.est_local(_ip(request))}

    @app.post("/api/connexion", status_code=204)
    async def connexion(demande: DemandeConnexion, request: Request) -> Response:
        adresse = _ip(request) or "?"
        if pause := limiteur.pause_avant(adresse):
            await asyncio.sleep(pause)
        if not acces.code_correct(demande.code, config.code_acces):
            limiteur.echec(adresse)
            raise HTTPException(401, "Code incorrect.")
        limiteur.succes(adresse)
        reponse = Response(status_code=204)
        reponse.set_cookie(acces.COOKIE, acces.jeton(config.code_acces, secret), max_age=acces.DUREE_COOKIE,
                           httponly=True, samesite="lax")
        return reponse

    @app.post("/api/deconnexion", status_code=204)
    async def deconnexion() -> Response:
        reponse = Response(status_code=204)
        reponse.delete_cookie(acces.COOKIE)
        return reponse

    # ------------------------------------------------------------------ modules

    @app.get("/api/modules")
    async def modules() -> list[dict]:
        return [s.vers_json() for s in sup.suivis.values()]

    @app.get("/api/modules/{id_}")
    async def module(id_: str) -> dict:
        return trouver(id_).vers_json()

    @app.post("/api/modules/{id_}/demarrer", status_code=202)
    async def demarrer(id_: str) -> dict:
        suivi = trouver(id_)
        try:
            await sup.allumer(suivi)
        except Refus as e:
            raise HTTPException(409, e.detail) from e
        return suivi.vers_json()

    @app.post("/api/modules/{id_}/arreter", status_code=202)
    async def arreter(id_: str, demande: DemandeArret | None = None) -> dict:
        suivi = trouver(id_)
        try:
            await sup.eteindre(suivi, force=bool(demande and demande.force))
        except Refus as e:
            contenu: dict = {"detail": e.detail}
            if e.taches is not None:
                contenu["taches"] = e.taches
            return JSONResponse(contenu, status_code=409)
        return suivi.vers_json()

    @app.get("/api/modules/{id_}/journal")
    async def lire_journal(id_: str, lignes: int = 200) -> dict:
        suivi = trouver(id_)
        fichier = journal.chemin(config.dossier_journaux, suivi.module.id)
        return {"lignes": await asyncio.to_thread(journal.fin, fichier, max(0, min(lignes, 2000)))}

    @app.api_route("/api/{reste:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    async def api_inconnue(reste: str) -> None:
        raise HTTPException(404, "Route inconnue.")

    # ------------------------------------------------------------------ interface (repli SPA)

    @app.get("/{chemin:path}", include_in_schema=False)
    async def interface(chemin: str) -> Response:
        index = dossier_front / "index.html"
        if not index.exists():
            return JSONResponse({"detail": "Interface non compilée (frontend/dist absent)."}, status_code=404)
        fichier = (dossier_front / chemin).resolve()
        if chemin and fichier.is_file() and fichier.is_relative_to(dossier_front.resolve()):
            return FileResponse(fichier)
        return FileResponse(index, headers={"Cache-Control": "no-cache"})

    return app


def creer_app_defaut() -> FastAPI:
    """Point d'entrée d'uvicorn (`--factory dashboard.app:creer_app_defaut`)."""
    return creer_app(charger())
