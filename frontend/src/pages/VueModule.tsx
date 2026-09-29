import { ArrowLeft, ExternalLink } from "lucide-react";
import { Link, Navigate, useParams } from "react-router";
import { adresseModule, api } from "../api";
import { classesBouton } from "../composants/ui";
import { useSondage } from "../hooks/sondage";
import { ALLUMES } from "../types";

/** Provisoire : la vue intégrée (barre + iframe, spec §7.5) arrive à l'étape 3. */
export function VueModule() {
  const { id = "" } = useParams();
  const { donnees: m, erreur } = useSondage(() => api.module(id), 1500);

  if (erreur) return <Navigate to="/" replace />;
  if (!m) return null;
  if (!ALLUMES.includes(m.etat)) return <Navigate to="/" replace />;

  return (
    <main className="mx-auto max-w-2xl px-4 py-16 text-center">
      <span className="mx-auto grid size-16 place-items-center rounded-2xl bg-surface-2 text-4xl ring-1 ring-bord">
        {m.emoji}
      </span>
      <h1 className="mt-4 text-2xl font-bold">{m.nom}</h1>
      <p className="mt-1 text-sm text-doux">La vue intégrée arrive bientôt. En attendant, ouvre le module directement.</p>
      <div className="mt-6 flex flex-wrap justify-center gap-2">
        <Link to="/" className={classesBouton("secondaire")}>
          <ArrowLeft className="size-4" />
          Dashboard
        </Link>
        <a href={adresseModule(m)} className={classesBouton("principal")}>
          <ExternalLink className="size-4" />
          Ouvrir {m.nom}
        </a>
      </div>
    </main>
  );
}
