import type { Module, Session, Tache } from "./types";

export class ErreurApi extends Error {
  constructor(
    message: string,
    public statut: number,
    public corps: unknown = null,
  ) {
    super(message);
  }
}

/** Émis quand l'API répond 401 : l'application renvoie alors vers /connexion. */
export const EVENEMENT_DECONNECTE = "dashboard:deconnecte";

function messageErreur(corps: unknown, statut: number): string {
  const detail = (corps as { detail?: unknown })?.detail;
  if (typeof detail === "string") return detail;
  return statut >= 500 ? "Erreur du serveur." : `Erreur ${statut}.`;
}

async function requete<T>(chemin: string, init?: RequestInit & { json?: unknown }): Promise<T> {
  const { json, ...reste } = init ?? {};
  let reponse: Response;
  try {
    reponse = await fetch(chemin, {
      ...reste,
      headers: json !== undefined ? { "Content-Type": "application/json" } : reste.headers,
      body: json !== undefined ? JSON.stringify(json) : reste.body,
    });
  } catch {
    throw new ErreurApi("Dashboard injoignable : vérifie que le serveur tourne toujours.", 0);
  }
  if (reponse.status === 204) return undefined as T;
  const corps = await reponse.json().catch(() => null);
  if (!reponse.ok) {
    if (reponse.status === 401 && chemin !== "/api/connexion") window.dispatchEvent(new Event(EVENEMENT_DECONNECTE));
    throw new ErreurApi(messageErreur(corps, reponse.status), reponse.status, corps);
  }
  return corps as T;
}

export const api = {
  session: () => requete<Session>("/api/session"),
  connexion: (code: string) => requete<void>("/api/connexion", { method: "POST", json: { code } }),
  deconnexion: () => requete<void>("/api/deconnexion", { method: "POST" }),
  modules: () => requete<Module[]>("/api/modules"),
  module: (id: string) => requete<Module>(`/api/modules/${id}`),
  demarrer: (id: string) => requete<Module>(`/api/modules/${id}/demarrer`, { method: "POST" }),
  arreter: (id: string, force = false) =>
    requete<Module>(`/api/modules/${id}/arreter`, { method: "POST", json: { force } }),
  journal: (id: string, lignes = 200) =>
    requete<{ lignes: string[] }>(`/api/modules/${id}/journal?lignes=${lignes}`),
};

/** Tâches renvoyées par un refus d'arrêt (409), si le module est occupé. */
export function tachesDuRefus(e: unknown): Tache[] | null {
  if (!(e instanceof ErreurApi) || e.statut !== 409) return null;
  const taches = (e.corps as { taches?: Tache[] } | null)?.taches;
  return Array.isArray(taches) ? taches : null;
}

/** Adresse du module vue depuis le navigateur (fonctionne aussi depuis le téléphone). */
export function adresseModule(m: Module): string {
  return `${window.location.protocol}//${window.location.hostname}:${m.port}/`;
}

/** « Verger Drama » → ["Verger ", "Drama"] : le dernier mot s'affiche en dégradé. */
export function decouperNom(nom: string): [string, string] {
  const i = nom.lastIndexOf(" ");
  return i < 0 ? ["", nom] : [nom.slice(0, i + 1), nom.slice(i + 1)];
}
