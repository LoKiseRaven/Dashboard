import { CircleCheck, CircleX, LogOut, X } from "lucide-react";
import { Link, useNavigate } from "react-router";
import { api } from "../api";
import { useSession, useToasts } from "../hooks/contexte";

/* ---------- En-tête collant (guide §5.15, spec §7.1) ---------- */

export function EnTete() {
  const { session, verifier } = useSession();
  const naviguer = useNavigate();
  const toasts = useToasts();

  const seDeconnecter = async () => {
    try {
      await api.deconnexion();
      await verifier();
      naviguer("/connexion");
    } catch (e) {
      toasts.erreur((e as Error).message);
    }
  };

  return (
    <header className="sticky top-0 z-30 border-b border-bord/70 bg-fond/75 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-3 px-4">
        <Link to="/" className="group flex items-center gap-2.5">
          <span className="grid size-9 place-items-center rounded-xl bg-surface-2 text-xl ring-1 ring-bord transition group-hover:ring-rose/50">
            🤓
          </span>
          <span className="font-titre text-lg font-bold tracking-tight">
            Dash<span className="texte-degrade">board</span>
          </span>
        </Link>
        {session && !session.local && (
          <button
            type="button"
            aria-label="Se déconnecter"
            title="Se déconnecter"
            onClick={() => void seDeconnecter()}
            className="grid size-11 place-items-center rounded-xl text-doux transition hover:bg-surface-2 hover:text-texte"
          >
            <LogOut className="size-4" />
          </button>
        )}
      </div>
    </header>
  );
}

/* ---------- Notifications (guide §5.18) ---------- */

export function Toasts() {
  const { toasts, fermer } = useToasts();
  return (
    <div
      aria-live="polite"
      className="pointer-events-none fixed inset-x-0 bottom-4 z-[60] flex flex-col items-center gap-2 px-4"
    >
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`pointer-events-auto flex max-w-md animate-apparition items-start gap-2 rounded-xl border px-4 py-3 text-sm shadow-2xl backdrop-blur ${
            t.erreur ? "border-ko/40 bg-ko/15 text-red-100" : "border-bord bg-surface-2/95 text-texte"
          }`}
        >
          {t.erreur ? (
            <CircleX className="mt-0.5 size-4 shrink-0 text-ko" />
          ) : (
            <CircleCheck className="mt-0.5 size-4 shrink-0 text-ok" />
          )}
          <span className="min-w-0 flex-1">{t.texte}</span>
          <button
            type="button"
            aria-label="Fermer"
            onClick={() => fermer(t.id)}
            className="-my-1 -mr-2 grid size-7 place-items-center rounded-lg text-doux hover:text-texte"
          >
            <X className="size-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
}
