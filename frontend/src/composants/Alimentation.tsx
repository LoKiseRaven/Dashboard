import { Loader2, Power } from "lucide-react";
import { useEffect, useRef, useState, type KeyboardEvent, type MouseEvent } from "react";
import { createPortal } from "react-dom";
import { api, tachesDuRefus } from "../api";
import { useToasts } from "../hooks/contexte";
import { ALLUMES, EN_TRANSITION, type Module, type Tache } from "../types";
import { resumeTache, pourcentage } from "./taches";
import { Bouton, Encart } from "./ui";

/* ---------- Bouton d'alimentation (spec §7.3) ---------- */

export function BoutonAlimentation({
  module,
  petit = false,
  surChangement,
}: {
  module: Module;
  petit?: boolean;
  surChangement: () => void;
}) {
  const toasts = useToasts();
  const [envoi, setEnvoi] = useState(false);
  const [refus, setRefus] = useState<Tache[] | null>(null);
  const bouton = useRef<HTMLButtonElement>(null);

  const allume = ALLUMES.includes(module.etat);
  const transition = EN_TRANSITION.includes(module.etat);
  const occupe = envoi || transition;

  const basculer = async (e: MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (occupe) return;
    setEnvoi(true);
    try {
      if (allume) await api.arreter(module.id);
      else await api.demarrer(module.id);
    } catch (err) {
      const taches = tachesDuRefus(err);
      if (taches) setRefus(taches);
      else toasts.erreur((err as Error).message);
    } finally {
      setEnvoi(false);
      surChangement();
    }
  };

  const confirmer = async () => {
    setEnvoi(true);
    try {
      await api.arreter(module.id, true);
      setRefus(null);
    } catch (err) {
      toasts.erreur((err as Error).message);
    } finally {
      setEnvoi(false);
      surChangement();
    }
  };

  const fermer = () => {
    setRefus(null);
    bouton.current?.focus();
  };

  const taille = petit ? "size-9" : "size-11";
  const aspect = allume
    ? "bg-rose text-white shadow-lg shadow-rose/30 hover:bg-rose-fonce"
    : "border border-bord bg-surface-2 text-doux hover:border-rose/50 hover:text-rose";

  return (
    <>
      <button
        ref={bouton}
        type="button"
        onClick={(e) => void basculer(e)}
        disabled={occupe}
        aria-pressed={allume}
        aria-label={`${allume ? "Éteindre" : "Allumer"} ${module.nom}`}
        title={allume ? "Éteindre" : "Allumer"}
        className={`relative z-10 grid ${taille} shrink-0 place-items-center rounded-full transition-all duration-150 active:scale-95 disabled:cursor-not-allowed disabled:opacity-60 disabled:active:scale-100 ${aspect}`}
      >
        {occupe ? <Loader2 className="size-5 animate-spin" /> : <Power className="size-5" />}
      </button>
      {refus && (
        <PopupArret nom={module.nom} taches={refus} envoi={envoi} onAnnuler={fermer} onConfirmer={() => void confirmer()} />
      )}
    </>
  );
}

/* ---------- Pop-up de confirmation d'arrêt (spec §7.4) ---------- */

function PopupArret({
  nom,
  taches,
  envoi,
  onAnnuler,
  onConfirmer,
}: {
  nom: string;
  taches: Tache[];
  envoi: boolean;
  onAnnuler: () => void;
  onConfirmer: () => void;
}) {
  const boite = useRef<HTMLDivElement>(null);
  const annuler = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    annuler.current?.focus();
  }, []);

  // Échap ferme ; Tab reste piégé dans la boîte.
  const clavier = (e: KeyboardEvent) => {
    if (e.key === "Escape") {
      e.stopPropagation();
      onAnnuler();
      return;
    }
    if (e.key !== "Tab" || !boite.current) return;
    const focusables = [...boite.current.querySelectorAll<HTMLElement>("button:not([disabled])")];
    if (!focusables.length) return;
    const premier = focusables[0];
    const dernier = focusables[focusables.length - 1];
    if (e.shiftKey && document.activeElement === premier) {
      e.preventDefault();
      dernier.focus();
    } else if (!e.shiftKey && document.activeElement === dernier) {
      e.preventDefault();
      premier.focus();
    }
  };

  const enAttente = taches.every((t) => t.statut === "en_attente");

  // Portail : la carte a une transformation au survol, qui casserait le positionnement fixe.
  return createPortal(
    <div
      className="fixed inset-0 z-50 grid place-items-center bg-black/60 px-4 backdrop-blur-sm"
      onMouseDown={(e) => e.target === e.currentTarget && !envoi && onAnnuler()}
      onKeyDown={clavier}
    >
      <div
        ref={boite}
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="titre-arret"
        aria-describedby="texte-arret"
        className="w-full max-w-md animate-apparition rounded-3xl border border-bord bg-surface/95 p-6 shadow-2xl shadow-black/60 backdrop-blur-xl"
      >
        <h2 id="titre-arret" className="text-xl font-bold">
          Arrêter {nom} ?
        </h2>
        <div id="texte-arret" className="mt-4">
          <Encart ton="avertissement">
            {enAttente
              ? "Une tâche attend son tour. Elle sera annulée et perdue."
              : "Une tâche est en cours. Elle sera interrompue et perdue."}
          </Encart>
        </div>
        {taches.length > 0 && (
          <ul className="mt-4 space-y-2 rounded-2xl border border-bord bg-black/30 p-4 text-sm">
            {taches.map((t) => {
              const pct = pourcentage(t);
              return (
                <li key={t.id} className="flex items-baseline justify-between gap-3">
                  <span className="min-w-0 truncate">{resumeTache(t)}</span>
                  <span className="shrink-0 text-xs text-doux tabular-nums">
                    {t.statut === "en_attente" ? "en attente" : pct !== null ? `${Math.round(pct)} %` : "en cours"}
                  </span>
                </li>
              );
            })}
          </ul>
        )}
        <div className="mt-6 flex flex-wrap justify-end gap-2">
          <Bouton ref={annuler} variante="secondaire" onClick={onAnnuler} disabled={envoi}>
            Annuler
          </Bouton>
          <Bouton variante="danger" onClick={onConfirmer} chargement={envoi} icone={<Power className="size-4" />}>
            Arrêter quand même
          </Bouton>
        </div>
      </div>
    </div>,
    document.body,
  );
}
