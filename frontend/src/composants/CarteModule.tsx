import { Link } from "react-router";
import { ALLUMES, type Etat, type Module } from "../types";
import { BoutonAlimentation } from "./Alimentation";
import { Journal } from "./Journal";
import { LigneTache, texteFile } from "./taches";
import { BadgeEtat, Encart, NomDegrade } from "./ui";

const BORDURES: Partial<Record<Etat, string>> = {
  ON: "border-ok/25",
  WORKING: "border-cyan/30",
  WAITING: "border-attente/30",
  ERROR: "border-ko/30",
};

/** Première ligne du message d'erreur : le reste (fin du journal) est dans le journal. */
function titreErreur(m: Module): string {
  return (m.message ?? "Erreur inconnue.").split("\n")[0];
}

export function CarteModule({ module: m, index, surChangement }: { module: Module; index: number; surChangement: () => void }) {
  const cliquable = ALLUMES.includes(m.etat);
  const enCours = m.taches.filter((t) => t.statut === "en_cours");

  return (
    <article
      aria-label={m.nom}
      style={{ animationDelay: `${Math.min(index, 8) * 60}ms` }}
      className={`relative min-w-0 animate-apparition rounded-3xl border bg-surface p-5 sm:p-6 ${BORDURES[m.etat] ?? "border-bord"} ${
        cliquable
          ? "transition duration-300 hover:-translate-y-1 hover:border-violet/40 hover:shadow-2xl hover:shadow-violet/10"
          : ""
      }`}
    >
      {/* Lien étiré sur toute la carte : les éléments interactifs passent au-dessus (z-10). */}
      {cliquable && (
        <Link to={`/module/${m.id}`} aria-label={`Ouvrir ${m.nom}`} className="absolute inset-0 z-0 rounded-3xl" />
      )}

      <div className="flex items-start gap-3">
        <span
          className={`grid size-12 shrink-0 place-items-center rounded-2xl bg-surface-2 text-2xl ring-1 ring-bord ${
            m.etat === "OFF" ? "opacity-60" : ""
          }`}
        >
          {m.emoji}
        </span>
        <div className="min-w-0 flex-1">
          <h2 className={`truncate text-xl leading-tight font-bold ${m.etat === "OFF" ? "opacity-60" : ""}`}>
            <NomDegrade nom={m.nom} />
          </h2>
          <div className="mt-1.5 flex flex-wrap items-center gap-2">
            <BadgeEtat etat={m.etat} />
            <span className="text-xs text-doux tabular-nums">:{m.port}</span>
          </div>
        </div>
        <BoutonAlimentation module={m} surChangement={surChangement} />
      </div>

      {m.etat === "STARTING" && (
        <p className="mt-4 text-sm text-doux">
          Premier lancement : compte quelques minutes (installation). Suis l'avancement dans le journal.
        </p>
      )}

      {m.etat === "WORKING" && enCours.length > 0 && (
        <div className="mt-4 rounded-2xl bg-black/30 p-4">
          <p className="text-xs font-semibold tracking-wide text-cyan uppercase">
            {enCours.length > 1 ? "Tâches en cours" : "Tâche en cours"}
          </p>
          <div className="mt-2 space-y-3">
            {enCours.map((t) => (
              <LigneTache key={t.id} tache={t} />
            ))}
          </div>
        </div>
      )}

      {m.etat === "WAITING" && <p className="mt-4 text-sm text-amber-300">{texteFile(m.taches)}</p>}

      {m.etat === "ERROR" && (
        <div className="mt-4">
          <Encart ton="erreur">{titreErreur(m)}</Encart>
        </div>
      )}

      {m.message && m.etat !== "ERROR" && m.etat !== "STARTING" && (
        <p className="mt-3 text-xs text-doux">{m.message}</p>
      )}

      {m.etat !== "OFF" && <Journal id={m.id} ouvertParDefaut={m.etat === "STARTING" || m.etat === "ERROR"} />}
    </article>
  );
}
