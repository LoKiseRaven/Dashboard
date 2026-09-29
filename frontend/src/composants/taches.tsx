import type { Tache } from "../types";
import { Progression } from "./ui";

export function resumeTache(t: Tache): string {
  return [t.libelle, t.etape].filter(Boolean).join(" · ");
}

export function pourcentage(t: Tache): number | null {
  return typeof t.progression === "number" ? t.progression : null;
}

/** « En attente du GPU · 2e dans la file » (spec §7.2). */
export function texteFile(taches: Tache[]): string {
  const positions = taches
    .filter((t) => t.statut === "en_attente" && typeof t.position_file === "number")
    .map((t) => t.position_file as number);
  if (!positions.length) return "En attente du GPU";
  const p = Math.min(...positions);
  return `En attente du GPU · ${p === 1 ? "prochain" : `${p}e`} dans la file`;
}

export function LigneTache({ tache }: { tache: Tache }) {
  const pct = pourcentage(tache);
  return (
    <div>
      <div className="flex items-baseline justify-between gap-3">
        <p className="min-w-0 truncate text-sm font-medium">{resumeTache(tache)}</p>
        {pct !== null && (
          <span className="shrink-0 font-titre text-sm font-bold tabular-nums">{Math.round(pct)} %</span>
        )}
      </div>
      <div className="mt-1.5">
        <Progression pct={pct} />
      </div>
    </div>
  );
}
