import { ArrowLeft, ExternalLink, PowerOff } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link, Navigate, useParams } from "react-router";
import { adresseModule, api, ErreurApi } from "../api";
import { BoutonAlimentation } from "../composants/Alimentation";
import { pourcentage, resumeTache } from "../composants/taches";
import { BadgeEtat, classesBouton, NomDegrade } from "../composants/ui";
import { useSondage } from "../hooks/sondage";
import { ALLUMES, type Module } from "../types";

const INCONNU = "inconnu" as const;

/** Mini-libellé de la barre : « Génération du scénario · Scène 3/6 · 42 % ». */
function libelleTache(m: Module): string | null {
  if (m.etat !== "WORKING") return null;
  const t = m.taches.find((x) => x.statut === "en_cours");
  if (!t) return null;
  const pct = pourcentage(t);
  return pct === null ? resumeTache(t) : `${resumeTache(t)} · ${Math.round(pct)} %`;
}

function texteVoile(m: Module): string {
  if (m.etat === "STOPPING") return `Arrêt de ${m.nom}…`;
  if (m.etat === "STARTING") return `Redémarrage de ${m.nom}…`;
  if (m.etat === "ERROR") return `${m.nom} s'est arrêté`;
  return `${m.nom} est éteint`;
}

/** Vue d'un module allumé (spec §7.5) : barre du dashboard + l'app en iframe. */
export function VueModule() {
  const { id = "" } = useParams();
  const { donnees, recharger } = useSondage(
    () =>
      api.module(id).catch((e: unknown) => {
        if (e instanceof ErreurApi && e.statut === 404) return INCONNU;
        throw e;
      }),
    1500,
  );

  // `ouvert` : le module était allumé au premier chargement de la page.
  // `session` change à chaque rallumage, pour recharger l'iframe proprement.
  const [ouvert, setOuvert] = useState<boolean | null>(null);
  const [session, setSession] = useState(0);
  const etaitAllume = useRef(false);

  const m = donnees && donnees !== INCONNU ? donnees : null;
  const allume = m ? ALLUMES.includes(m.etat) : false;

  useEffect(() => {
    if (!m) return;
    if (ouvert === null) setOuvert(allume);
    if (allume && !etaitAllume.current && ouvert !== null) setSession((s) => s + 1);
    etaitAllume.current = allume;
  }, [m, allume, ouvert]);

  const nom = m?.nom;
  useEffect(() => {
    if (nom) document.title = `${nom} · Dashboard`;
    return () => {
      document.title = "Dashboard";
    };
  }, [nom]);

  if (donnees === INCONNU || ouvert === false) return <Navigate to="/" replace />;
  if (!m || ouvert === null) return <div className="h-dvh bg-fond" />;

  const tache = libelleTache(m);

  return (
    <div className="flex h-dvh flex-col overflow-hidden bg-fond">
      <header className="flex h-12 shrink-0 items-center gap-2 border-b border-bord/70 bg-fond/75 px-2 backdrop-blur-xl sm:gap-3 sm:px-3">
        <Link
          to="/"
          aria-label="Retour au dashboard"
          className="inline-flex min-h-10 shrink-0 items-center gap-1.5 rounded-lg px-2 text-sm text-doux transition hover:text-texte"
        >
          <ArrowLeft className="size-4" />
          <span className="max-sm:hidden">Dashboard</span>
        </Link>

        <span className="h-5 w-px shrink-0 bg-bord max-sm:hidden" aria-hidden />

        <span className="grid size-7 shrink-0 place-items-center rounded-lg bg-surface-2 text-base ring-1 ring-bord">
          {m.emoji}
        </span>
        <h1 className="min-w-0 truncate font-titre text-base font-bold tracking-tight">
          <NomDegrade nom={m.nom} />
        </h1>
        <span className="shrink-0">
          <BadgeEtat etat={m.etat} />
        </span>
        {tache && <span className="min-w-0 truncate text-xs text-doux max-md:hidden">{tache}</span>}

        <div className="ml-auto flex shrink-0 items-center gap-1.5">
          <a
            href={adresseModule(m)}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Ouvrir dans un nouvel onglet"
            title="Ouvrir dans un nouvel onglet"
            className="grid size-10 place-items-center rounded-lg text-doux transition hover:bg-surface-2 hover:text-texte"
          >
            <ExternalLink className="size-4" />
          </a>
          <BoutonAlimentation module={m} petit surChangement={() => void recharger()} />
        </div>
      </header>

      <div className="relative min-h-0 flex-1">
        <iframe
          key={session}
          src={adresseModule(m)}
          title={m.nom}
          allow="clipboard-read; clipboard-write; fullscreen; autoplay"
          allowFullScreen
          className="size-full border-0 bg-fond"
        />

        {!allume && (
          <div className="absolute inset-0 z-10 grid animate-apparition place-items-center bg-fond/85 px-4 backdrop-blur-md">
            <div className="flex max-w-sm flex-col items-center text-center" role="status" aria-live="polite">
              <span className="grid size-16 place-items-center rounded-2xl bg-surface-2 ring-1 ring-bord">
                <PowerOff className="size-7 text-rose" />
              </span>
              <h2 className="mt-4 text-xl font-bold">{texteVoile(m)}</h2>
              {m.etat === "ERROR" && m.message && (
                <p className="mt-1 text-sm break-words text-red-200">{m.message.split("\n")[0]}</p>
              )}
              {(m.etat === "OFF" || m.etat === "ERROR") && (
                <p className="mt-1 text-sm text-doux">Rallume-le avec le bouton ⏻ en haut à droite, ou reviens au dashboard.</p>
              )}
              <Link to="/" className={`${classesBouton("principal")} mt-6`}>
                <ArrowLeft className="size-4" />
                Retour au dashboard
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
