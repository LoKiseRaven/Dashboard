import { ArrowRight, Lock } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Navigate, useNavigate, useSearchParams } from "react-router";
import { api, ErreurApi } from "../api";
import { Bouton } from "../composants/ui";
import { useSession } from "../hooks/contexte";

/** Seules les adresses internes sont acceptées comme destination après connexion. */
function destination(suite: string | null): string {
  return suite && suite.startsWith("/") && !suite.startsWith("//") ? suite : "/";
}

export function Connexion() {
  const { session, verifier } = useSession();
  const [params] = useSearchParams();
  const naviguer = useNavigate();
  const [code, setCode] = useState("");
  const [erreur, setErreur] = useState<string | null>(null);
  const [envoi, setEnvoi] = useState(false);
  const suite = destination(params.get("suite"));

  if (session?.connecte) return <Navigate to={suite} replace />;

  const envoyer = async (e: FormEvent) => {
    e.preventDefault();
    if (!code.trim()) return;
    setEnvoi(true);
    setErreur(null);
    try {
      await api.connexion(code);
      await verifier();
      naviguer(suite, { replace: true });
    } catch (err) {
      setErreur(err instanceof ErreurApi && err.statut === 401 ? "Code incorrect." : (err as Error).message);
      setCode("");
    } finally {
      setEnvoi(false);
    }
  };

  return (
    <main className="relative grid min-h-dvh place-items-center overflow-hidden px-4">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(40%_35%_at_30%_30%,rgba(161,33,246,0.22),transparent),radial-gradient(35%_35%_at_70%_70%,rgba(86,216,252,0.16),transparent)]"
      />
      <form
        onSubmit={(e) => void envoyer(e)}
        className="relative w-full max-w-sm animate-apparition rounded-3xl border border-bord bg-surface/80 p-7 text-center shadow-2xl backdrop-blur-xl"
      >
        <span className="mx-auto grid size-16 place-items-center rounded-2xl bg-surface-2 text-4xl ring-1 ring-bord">
          🤓
        </span>
        <h1 className="mt-4 text-2xl font-bold">
          Dash<span className="texte-degrade">board</span>
        </h1>
        <p className="mt-1 text-sm text-doux">Entre ton code pour piloter tes modules.</p>

        <label htmlFor="code" className="sr-only">
          Code d'accès
        </label>
        <div className="relative mt-6">
          <Lock className="pointer-events-none absolute top-1/2 left-3.5 size-4 -translate-y-1/2 text-doux" />
          <input
            id="code"
            type="password"
            autoComplete="current-password"
            autoFocus
            value={code}
            onChange={(e) => setCode(e.target.value)}
            aria-invalid={erreur ? true : undefined}
            aria-describedby={erreur ? "erreur-code" : undefined}
            className="h-12 w-full rounded-xl border border-bord bg-surface-2 pr-4 pl-10 text-base outline-none transition focus:border-violet/70 focus:ring-4 focus:ring-violet/15"
          />
        </div>
        {erreur && (
          <p id="erreur-code" role="alert" className="mt-2 text-left text-sm text-red-200">
            {erreur}
          </p>
        )}
        <Bouton type="submit" large chargement={envoi} disabled={!code.trim()} className="mt-4">
          Entrer
          <ArrowRight className="size-4" />
        </Bouton>
        <p className="mt-4 text-center text-xs text-doux">Code mémorisé 30 jours sur cet appareil.</p>
      </form>
    </main>
  );
}
