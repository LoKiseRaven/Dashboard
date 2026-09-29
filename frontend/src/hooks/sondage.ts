import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Appelle `charger` tout de suite, puis toutes les `intervalle` ms tant que l'onglet est
 * visible et que `actif` est vrai. Une requête n'est jamais lancée tant que la précédente
 * n'a pas répondu. `recharger()` force un appel immédiat (après une action).
 */
export function useSondage<T>(charger: () => Promise<T>, intervalle: number, actif = true) {
  const [donnees, setDonnees] = useState<T | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const enCours = useRef(false);
  const chargerRef = useRef(charger);
  chargerRef.current = charger;

  const recharger = useCallback(async () => {
    if (enCours.current) return;
    enCours.current = true;
    try {
      setDonnees(await chargerRef.current());
      setErreur(null);
    } catch (e) {
      setErreur((e as Error).message);
    } finally {
      enCours.current = false;
    }
  }, []);

  useEffect(() => {
    if (!actif) return;
    let minuterie: number | undefined;
    const demarrer = () => {
      window.clearInterval(minuterie);
      if (document.visibilityState !== "visible") return;
      void recharger();
      minuterie = window.setInterval(() => void recharger(), intervalle);
    };
    demarrer();
    document.addEventListener("visibilitychange", demarrer);
    return () => {
      window.clearInterval(minuterie);
      document.removeEventListener("visibilitychange", demarrer);
    };
  }, [actif, intervalle, recharger]);

  return { donnees, erreur, recharger };
}
