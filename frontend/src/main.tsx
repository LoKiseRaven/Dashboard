import "@fontsource-variable/inter";
import "@fontsource-variable/space-grotesk";
import "./styles.css";

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Link, Navigate, Outlet, Route, Routes, useLocation } from "react-router";
import { EnTete, Toasts } from "./composants/cadre";
import { classesBouton, Encart, Halo } from "./composants/ui";
import { Fournisseurs, useSession } from "./hooks/contexte";
import { Accueil } from "./pages/Accueil";
import { Connexion } from "./pages/Connexion";
import { VueModule } from "./pages/VueModule";

/** Pages protégées : renvoie vers /connexion tant que le code n'a pas été saisi. */
function Protege() {
  const { session, erreur, verifier } = useSession();
  const { pathname, search } = useLocation();

  if (!session) {
    return erreur ? (
      <main className="mx-auto max-w-md px-4 py-20">
        <Encart ton="erreur">
          {erreur}{" "}
          <button type="button" onClick={() => void verifier()} className="font-semibold text-cyan hover:underline">
            Réessayer
          </button>
        </Encart>
      </main>
    ) : null;
  }
  if (!session.connecte) {
    return <Navigate to={`/connexion?suite=${encodeURIComponent(pathname + search)}`} replace />;
  }
  return <Outlet />;
}

function Cadre() {
  return (
    <>
      <Halo />
      <EnTete />
      <Outlet />
    </>
  );
}

function Introuvable() {
  return (
    <main className="py-20 text-center">
      <h1 className="text-3xl font-bold">Page introuvable</h1>
      <Link to="/" className={`${classesBouton("secondaire")} mt-6`}>
        Retour au dashboard
      </Link>
    </main>
  );
}

createRoot(document.getElementById("racine")!).render(
  <StrictMode>
    <Fournisseurs>
      <BrowserRouter>
        <Routes>
          <Route path="connexion" element={<Connexion />} />
          <Route element={<Protege />}>
            {/* Vue module : pleine hauteur, sans l'en-tête du dashboard (spec §7.5). */}
            <Route path="module/:id" element={<VueModule />} />
            <Route element={<Cadre />}>
              <Route index element={<Accueil />} />
              <Route path="*" element={<Introuvable />} />
            </Route>
          </Route>
        </Routes>
        <Toasts />
      </BrowserRouter>
    </Fournisseurs>
  </StrictMode>,
);
