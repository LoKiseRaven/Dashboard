import { api } from "../api";
import { CarteModule } from "../composants/CarteModule";
import { Encart } from "../composants/ui";
import { useSondage } from "../hooks/sondage";
import { ALLUMES, type Module } from "../types";

function resume(modules: Module[]): string {
  const allumes = modules.filter((m) => ALLUMES.includes(m.etat)).length;
  const parties = [allumes === 0 ? "Tout est éteint" : `${allumes} allumé${allumes > 1 ? "s" : ""}`];
  const travail = modules.filter((m) => m.etat === "WORKING").length;
  const attente = modules.filter((m) => m.etat === "WAITING").length;
  const erreurs = modules.filter((m) => m.etat === "ERROR").length;
  if (travail) parties.push(`${travail} au travail`);
  if (attente) parties.push(`${attente} en attente`);
  if (erreurs) parties.push(`${erreurs} en erreur`);
  return parties.join(" · ");
}

export function Accueil() {
  const { donnees: modules, erreur, recharger } = useSondage(api.modules, 1500);

  return (
    <main className="mx-auto max-w-6xl px-4 pt-6 pb-40">
      <div className="mb-6 flex items-end justify-between gap-4">
        <div className="min-w-0">
          <h1 className="text-3xl font-bold sm:text-4xl">Modules</h1>
          <p className="mt-1 text-sm text-doux" aria-live="polite">
            {modules ? resume(modules) : "Chargement…"}
          </p>
        </div>
      </div>

      {erreur && (
        <div className="mb-4">
          <Encart ton="erreur">
            {erreur}{" "}
            <button type="button" onClick={() => void recharger()} className="font-semibold text-cyan hover:underline">
              Réessayer
            </button>
          </Encart>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {modules
          ? modules.map((m, i) => <CarteModule key={m.id} module={m} index={i} surChangement={() => void recharger()} />)
          : !erreur &&
            [0, 1, 2].map((i) => <div key={i} aria-hidden className="squelette h-56 rounded-3xl" />)}
      </div>
    </main>
  );
}
