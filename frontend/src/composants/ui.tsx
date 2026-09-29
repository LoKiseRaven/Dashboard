import { CircleX, Info, Loader2, TriangleAlert } from "lucide-react";
import type { ButtonHTMLAttributes, ReactNode, Ref } from "react";
import { decouperNom } from "../api";
import type { Etat } from "../types";

/* ---------- Bouton (guide §5.1) ---------- */

export type Variante = "principal" | "secondaire" | "fantome" | "danger";

const STYLES: Record<Variante, string> = {
  principal:
    "bg-rose text-white shadow-lg shadow-rose/25 hover:bg-rose-fonce hover:shadow-rose/40 disabled:shadow-none",
  secondaire: "border border-bord bg-surface-2 text-texte hover:border-doux/50 hover:bg-bord/60",
  fantome: "text-doux hover:bg-surface-2 hover:text-texte",
  danger: "border border-ko/40 bg-ko/10 text-red-200 hover:bg-ko/20",
};

export function classesBouton(variante: Variante = "principal", petit = false, large = false): string {
  return [
    "inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-all duration-150",
    "active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-45 disabled:active:scale-100",
    petit ? "min-h-9 px-3 text-sm" : "min-h-11 px-4",
    large ? "w-full" : "",
    STYLES[variante],
  ].join(" ");
}

interface PropsBouton extends ButtonHTMLAttributes<HTMLButtonElement> {
  variante?: Variante;
  petit?: boolean;
  large?: boolean;
  chargement?: boolean;
  icone?: ReactNode;
  ref?: Ref<HTMLButtonElement>;
}

export function Bouton({
  variante,
  petit,
  large,
  chargement,
  icone,
  children,
  className = "",
  disabled,
  type = "button",
  ...reste
}: PropsBouton) {
  return (
    <button
      type={type}
      className={`${classesBouton(variante, petit, large)} ${className}`}
      disabled={disabled || chargement}
      {...reste}
    >
      {chargement ? <Loader2 className="size-4 animate-spin" /> : icone}
      {children}
    </button>
  );
}

/* ---------- Badge d'état (guide §5.7, spec §7.2) ---------- */

const BADGES: Record<Etat, { classes: string; libelle: string; pulse: boolean }> = {
  OFF: { classes: "bg-doux/15 text-doux ring-doux/25", libelle: "OFF", pulse: false },
  STARTING: { classes: "bg-doux/15 text-doux ring-doux/25", libelle: "Démarrage…", pulse: true },
  STOPPING: { classes: "bg-doux/15 text-doux ring-doux/25", libelle: "Arrêt…", pulse: true },
  ON: { classes: "bg-ok/12 text-green-300 ring-ok/30", libelle: "ON", pulse: false },
  WORKING: { classes: "bg-cyan/12 text-cyan ring-cyan/30", libelle: "WORKING", pulse: true },
  WAITING: { classes: "bg-attente/12 text-amber-300 ring-attente/30", libelle: "WAITING", pulse: true },
  ERROR: { classes: "bg-ko/12 text-red-300 ring-ko/30", libelle: "ERROR", pulse: false },
};

export function BadgeEtat({ etat }: { etat: Etat }) {
  const b = BADGES[etat];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${b.classes}`}
    >
      <span className={`size-1.5 rounded-full bg-current ${b.pulse ? "animate-pulse-doux" : ""}`} />
      {b.libelle}
    </span>
  );
}

/* ---------- Nom avec le dernier mot en dégradé (guide §5.9) ---------- */

export function NomDegrade({ nom }: { nom: string }) {
  const [debut, fin] = decouperNom(nom);
  return (
    <>
      {debut}
      <span className="texte-degrade">{fin}</span>
    </>
  );
}

/* ---------- Barre de progression (guide §5.10) ---------- */

/** `pct` de 0 à 100, ou null si inconnu : barre pleine qui pulse. */
export function Progression({ pct }: { pct: number | null }) {
  const valeur = pct === null ? null : Math.round(Math.max(0, Math.min(100, pct)));
  return (
    <div
      role="progressbar"
      aria-valuenow={valeur ?? undefined}
      aria-valuemin={0}
      aria-valuemax={100}
      className="h-1.5 w-full overflow-hidden rounded-full bg-white/10"
    >
      <div
        className={`fond-degrade h-full rounded-full transition-[width] duration-500 ${valeur === null ? "animate-pulse-doux" : ""}`}
        style={{ width: `${valeur ?? 100}%` }}
      />
    </div>
  );
}

/* ---------- Encarts (guide §4.7) ---------- */

export function Encart({ ton, children }: { ton: "info" | "avertissement" | "erreur"; children: ReactNode }) {
  const conf = {
    info: { c: "border-cyan/20 bg-cyan/5 text-zinc-300", i: <Info className="mt-0.5 size-4 shrink-0 text-cyan" /> },
    avertissement: {
      c: "border-attente/30 bg-attente/10 text-amber-100",
      i: <TriangleAlert className="mt-0.5 size-4 shrink-0 text-attente" />,
    },
    erreur: { c: "border-ko/30 bg-ko/10 text-red-200", i: <CircleX className="mt-0.5 size-4 shrink-0 text-ko" /> },
  }[ton];
  return (
    <div role={ton === "erreur" ? "alert" : undefined} className={`flex gap-2 rounded-2xl border p-3 text-sm ${conf.c}`}>
      {conf.i}
      <div className="min-w-0 flex-1 leading-relaxed break-words">{children}</div>
    </div>
  );
}

/* ---------- Halo global (guide §4.6) ---------- */

export function Halo() {
  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-x-0 top-0 -z-10 h-80 bg-[radial-gradient(50%_60%_at_20%_0%,rgba(254,44,85,0.14),transparent),radial-gradient(40%_50%_at_85%_0%,rgba(37,244,238,0.10),transparent)]"
    />
  );
}
