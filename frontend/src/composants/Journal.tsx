import { ChevronDown } from "lucide-react";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { api } from "../api";
import { useSondage } from "../hooks/sondage";

function lirePreference(id: string): boolean | null {
  try {
    const v = window.localStorage.getItem(`journal-ouvert:${id}`);
    return v === null ? null : v === "1";
  } catch {
    return null;
  }
}

function ecrirePreference(id: string, ouvert: boolean) {
  try {
    window.localStorage.setItem(`journal-ouvert:${id}`, ouvert ? "1" : "0");
  } catch {
    /* stockage indisponible : la préférence n'est simplement pas retenue */
  }
}

/**
 * Journal dépliable d'un module (spec §7.2) : 200 dernières lignes, rafraîchies toutes les
 * 2 s seulement quand il est déplié. Le choix de l'utilisateur est retenu par module ; à
 * défaut, il est déplié quand `ouvertParDefaut` est vrai (STARTING, ERROR).
 */
export function Journal({ id, ouvertParDefaut }: { id: string; ouvertParDefaut: boolean }) {
  const [choix, setChoix] = useState<boolean | null>(() => lirePreference(id));
  const ouvert = choix ?? ouvertParDefaut;
  const { donnees, erreur } = useSondage(() => api.journal(id, 200), 2000, ouvert);
  const pre = useRef<HTMLPreElement>(null);
  const enBas = useRef(true);

  const basculer = () => {
    setChoix(!ouvert);
    ecrirePreference(id, !ouvert);
  };

  // Défilement automatique, sauf si on est remonté lire plus haut.
  useLayoutEffect(() => {
    if (pre.current && enBas.current) pre.current.scrollTop = pre.current.scrollHeight;
  }, [donnees, ouvert]);

  useEffect(() => {
    if (!ouvert) enBas.current = true;
  }, [ouvert]);

  const lignes = donnees?.lignes ?? [];

  return (
    <div className="relative z-10 mt-4 rounded-2xl border border-bord bg-black/30">
      <button
        type="button"
        aria-expanded={ouvert}
        onClick={basculer}
        className="flex min-h-11 w-full items-center justify-between gap-2 px-4 py-2.5 text-left text-xs font-semibold tracking-wide text-doux uppercase hover:text-texte"
      >
        {ouvert ? "Masquer le journal" : "Voir le journal"}
        <ChevronDown className={`size-4 transition ${ouvert ? "rotate-180" : ""}`} />
      </button>
      {ouvert && (
        <pre
          ref={pre}
          onScroll={(e) => {
            const el = e.currentTarget;
            enBas.current = el.scrollHeight - el.scrollTop - el.clientHeight < 24;
          }}
          className="max-h-[40vh] overflow-auto rounded-b-2xl border-t border-bord bg-black/40 px-4 py-3 font-mono text-[11px] leading-relaxed break-words whitespace-pre-wrap text-zinc-300"
        >
          {erreur ? erreur : donnees === null ? "Chargement…" : lignes.length ? lignes.join("\n") : "Journal vide."}
        </pre>
      )}
    </div>
  );
}
