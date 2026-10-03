import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { api, EVENEMENT_DECONNECTE } from "../api";
import type { Session } from "../types";

/* ---------- Notifications (guide §5.18) ---------- */

export interface Toast {
  id: number;
  texte: string;
  erreur: boolean;
}

interface ContexteToasts {
  toasts: Toast[];
  succes: (texte: string) => void;
  erreur: (texte: string) => void;
  fermer: (id: number) => void;
}

const CtxToasts = createContext<ContexteToasts | null>(null);

export function useToasts(): ContexteToasts {
  const c = useContext(CtxToasts);
  if (!c) throw new Error("useToasts hors du fournisseur");
  return c;
}

/* ---------- Session (code d'accès, spec §10.1) ---------- */

interface ContexteSession {
  /** null tant que la première vérification n'a pas répondu. */
  session: Session | null;
  erreur: string | null;
  verifier: () => Promise<void>;
}

const CtxSession = createContext<ContexteSession | null>(null);

export function useSession(): ContexteSession {
  const c = useContext(CtxSession);
  if (!c) throw new Error("useSession hors du fournisseur");
  return c;
}

export function Fournisseurs({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const suivant = useRef(1);

  const fermer = useCallback((id: number) => setToasts((t) => t.filter((x) => x.id !== id)), []);
  const ajouter = useCallback(
    (texte: string, erreur: boolean) => {
      const id = suivant.current++;
      setToasts((t) => [...t.slice(-2), { id, texte, erreur }]);
      window.setTimeout(() => fermer(id), erreur ? 6000 : 2000);
    },
    [fermer],
  );
  const ctxToasts = useMemo(
    () => ({ toasts, fermer, succes: (t: string) => ajouter(t, false), erreur: (t: string) => ajouter(t, true) }),
    [toasts, ajouter, fermer],
  );

  const [session, setSession] = useState<Session | null>(null);
  const [erreurSession, setErreurSession] = useState<string | null>(null);
  const verifier = useCallback(async () => {
    try {
      setSession(await api.session());
      setErreurSession(null);
    } catch (e) {
      setErreurSession((e as Error).message);
    }
  }, []);

  useEffect(() => {
    void verifier();
    const deconnecte = () => setSession((s) => (s ? { ...s, connecte: false } : s));
    window.addEventListener(EVENEMENT_DECONNECTE, deconnecte);
    return () => window.removeEventListener(EVENEMENT_DECONNECTE, deconnecte);
  }, [verifier]);

  const ctxSession = useMemo(() => ({ session, erreur: erreurSession, verifier }), [session, erreurSession, verifier]);

  return (
    <CtxSession.Provider value={ctxSession}>
      <CtxToasts.Provider value={ctxToasts}>{children}</CtxToasts.Provider>
    </CtxSession.Provider>
  );
}
