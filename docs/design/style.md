# Style « studio sombre » — guide de reproduction

Ce document décrit précisément le style visuel de l'interface web de **Verger Drama** (`web/frontend/` dans le projet d'origine), pour le reproduire à l'identique dans un autre projet. Il est écrit pour un agent de code : les valeurs sont exactes, et les classes Tailwind sont celles du code source d'origine.

---

## 1. L'esprit en une phrase

Un **studio de création sombre et nerveux**, dans l'esprit des applis vidéo verticales (TikTok) :
- un fond presque noir ;
- des cartes gris anthracite aux coins très arrondis et à bordure fine ;
- **un seul accent chaud** (rose TikTok `#fe2c55`) pour l'action principale ;
- **un accent froid** (cyan `#25f4ee`) pour l'information et la progression ;
- un **dégradé rose → cyan** réservé aux éléments « vedette » (logo, progression, étapes faites, numéros).

L'ensemble reste sobre : beaucoup de gris, peu de couleur, mais une couleur toujours saturée et lumineuse quand elle apparaît.

**Mots-clés :** sombre uniquement, dense mais aéré, arrondi, translucide et flouté pour ce qui flotte, micro-animations discrètes, pensé d'abord pour le téléphone.

---

## 2. Pile technique

| Élément | Choix | Remarque |
|---|---|---|
| Framework | React 19 + Vite + TypeScript | Tout framework convient : le style repose sur Tailwind. |
| CSS | **Tailwind CSS v4** (`@tailwindcss/vite`) | Jetons déclarés dans `@theme` (pas de `tailwind.config.js`). |
| Icônes | **lucide-react** | Trait fin, `size-4` par défaut, `size-3.5` dans les badges, `size-5` dans les panneaux, `size-7` dans les grands médaillons. |
| Polices | `@fontsource-variable/inter` et `@fontsource-variable/space-grotesk` | Embarquées (pas de Google Fonts). Importées dans `main.tsx`. |

```ts
// main.tsx
import "@fontsource-variable/inter";
import "@fontsource-variable/space-grotesk";
import "./styles.css";
```

```html
<!-- index.html -->
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<meta name="theme-color" content="#09090b" />
<!-- favicon = un emoji en SVG inline -->
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🍓</text></svg>" />
```

---

## 3. Feuille de style de base — à copier telle quelle

C'est le **cœur du style**. Copier ce fichier en `src/styles.css`. Les noms des jetons sont en français (`fond`, `surface`, `bord`, `doux`…) : les garder, car toutes les recettes de ce document les utilisent (`bg-surface`, `border-bord`, `text-doux`, etc.).

```css
@import "tailwindcss";

@theme {
  --color-fond: #09090b;        /* fond de page */
  --color-surface: #141418;     /* cartes */
  --color-surface-2: #1c1c22;   /* champs, zones internes, tuiles, pastilles */
  --color-bord: #2a2a33;        /* toutes les bordures fines */
  --color-texte: #f4f4f5;       /* texte principal */
  --color-doux: #a1a1aa;        /* texte secondaire, libellés */
  --color-rose: #fe2c55;        /* action principale, accent chaud */
  --color-rose-fonce: #e0193f;  /* survol de l'action principale */
  --color-cyan: #25f4ee;        /* accent froid : liens, info, focus, progression */
  --color-ok: #22c55e;
  --color-attente: #f59e0b;
  --color-ko: #ef4444;

  --font-texte: "Inter Variable", system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-titre: "Space Grotesk Variable", "Inter Variable", system-ui, sans-serif;
  --font-mono: ui-monospace, "Cascadia Code", Consolas, monospace;

  --animate-apparition: apparition 0.35s ease-out both;
  --animate-scintille: scintille 1.6s linear infinite;
  --animate-pulse-doux: pulse-doux 1.8s ease-in-out infinite;

  @keyframes apparition {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: none; }
  }
  @keyframes scintille {
    from { background-position: -200% 0; }
    to { background-position: 200% 0; }
  }
  @keyframes pulse-doux {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.45; }
  }
}

@layer base {
  html { color-scheme: dark; -webkit-tap-highlight-color: transparent; }
  body {
    margin: 0;
    min-height: 100dvh;
    background: var(--color-fond);
    color: var(--color-texte);
    font-family: var(--font-texte);
    -webkit-font-smoothing: antialiased;
  }
  h1, h2, h3 { font-family: var(--font-titre); letter-spacing: -0.02em; }
  :focus-visible { outline: 2px solid var(--color-cyan); outline-offset: 2px; }
  ::selection { background: color-mix(in srgb, var(--color-rose) 45%, transparent); }
}

/* Texte en dégradé rose → cyan (un mot du logo, jamais un paragraphe) */
@utility texte-degrade {
  background: linear-gradient(90deg, var(--color-rose), var(--color-cyan));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

/* Fond en dégradé rose → cyan (barres de progression, pastilles « vedette ») */
@utility fond-degrade {
  background: linear-gradient(90deg, var(--color-rose), var(--color-cyan));
}

/* Squelette de chargement scintillant */
@utility squelette {
  background: linear-gradient(90deg, var(--color-surface) 25%, var(--color-surface-2) 50%, var(--color-surface) 75%);
  background-size: 200% 100%;
  animation: var(--animate-scintille);
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

**Il n'y a pas de thème clair.** C'est un choix assumé : ne pas en ajouter, sauf demande explicite.

---

## 4. Système visuel

### 4.1 Hiérarchie des surfaces (du plus profond au plus haut)

1. **Page** : `bg-fond` (`#09090b`), avec un halo coloré fixe derrière l'en-tête (voir §4.6).
2. **Carte** : `bg-surface` + `border border-bord`.
3. **Zone interne d'une carte** : au choix, selon ce qu'elle contient :
   - `bg-surface-2` (champ, tuile, pastille) ;
   - `bg-black/30` (bloc de code, prompt, légende, lecteur replié) ;
   - `bg-black/40` (journal, terminal).
4. **Éléments flottants** (en-tête collant, panneau de tâche, barre d'action collante, notification) : couleur translucide (`bg-fond/75`, `bg-surface/90`, `bg-surface/95`) **+ `backdrop-blur-xl`** + grande ombre noire (`shadow-2xl shadow-black/60`).

Les couleurs d'accent ne servent **jamais** de fond plein pour une grande surface. Elles s'utilisent en teinte légère :
- fond à 5–15 % : `bg-rose/10`, `bg-cyan/5`, `bg-attente/10` ;
- bordure à 20–40 % : `border-rose/25`, `border-cyan/20` ;
- texte plein : `text-rose`, `text-cyan`.

Le seul aplat de couleur pleine est le **bouton principal** (`bg-rose`).

### 4.2 Typographie

| Rôle | Police | Classes |
|---|---|---|
| Titre de page (h1) | Space Grotesk (auto via `h1`) | `text-3xl sm:text-4xl font-bold` (+ `leading-tight` si le titre peut faire 2 lignes) |
| Titre de carte (h2) | Space Grotesk | `text-xl font-bold leading-tight`, ou `text-lg font-bold` |
| **Sur-titre de section** | Inter | `text-sm font-semibold tracking-wide text-doux uppercase` : **signature du style**, à utiliser en haut de chaque carte-formulaire |
| Petit sur-titre dans un encart | Inter | `text-xs font-semibold tracking-wide uppercase` + couleur de l'encart (ex. `text-rose`) |
| Texte courant | Inter | `text-sm` (dense), `leading-relaxed` pour les paragraphes |
| Texte secondaire | Inter | `text-sm text-doux` ou `text-xs text-doux` |
| Texte sur carte secondaire | Inter | `text-zinc-300` (un cran plus lumineux que `doux`, pour un texte long lisible) |
| Micro-texte | Inter | `text-[11px]` (compteur sous une barre, aide) |
| Chiffres, compteurs, numéros | **Space Grotesk** | `font-titre font-bold tabular-nums` (ex. `text-2xl` pour « 4/6 ») |
| Code, prompt, journal | Mono | `font-mono text-xs leading-relaxed whitespace-pre-wrap break-words text-zinc-300` (`text-[11px]` pour un journal) |

Les titres ont `letter-spacing: -0.02em` (serré). Le logo a en plus `tracking-tight`.

### 4.3 Arrondis

| Élément | Rayon |
|---|---|
| Grande carte (section, variante, scène, lecteur vidéo) | `rounded-3xl` (24 px) |
| Carte moyenne, encart, affiche, tuile, panneau flottant, zone interne | `rounded-2xl` (16 px) |
| Bouton, champ, médaillon d'icône, notification | `rounded-xl` (12 px) |
| Puce carrée (ingrédient), petit bouton icône | `rounded-lg` (8 px) |
| Badge, pastille, barre de progression, interrupteur | `rounded-full` |

Règle : **plus un élément est grand, plus il est arrondi.** Un élément imbriqué est un cran moins arrondi que son conteneur.

### 4.4 Espacements et mise en page

- **Conteneur de page** : `mx-auto max-w-6xl px-4 pt-6 pb-40`. Le `pb-40` laisse la place au panneau flottant du bas.
- **Formulaire centré** : `mx-auto max-w-2xl space-y-4`.
- **Padding des cartes** : `p-5 sm:p-6` (formulaire, variante), `p-4 sm:p-5` (carte de liste dense).
- **Espacement vertical interne** : `mt-4` entre les blocs d'une carte, `mt-3` pour un bloc lié, `mt-1` / `mt-0.5` entre un titre et son sous-titre.
- **Écart des grilles** : `gap-3 sm:gap-4` (affiches), `gap-4` (cartes), `gap-2` (boutons côte à côte), `gap-1.5` (puces).
- **Grille d'affiches 9:16** : `grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-3 lg:grid-cols-4`.
- **Deux colonnes média + texte** : `grid gap-5 md:grid-cols-[minmax(0,22rem)_1fr] md:gap-8`. Le média passe au-dessus du texte sur téléphone.
- **En-tête de page** : titre à gauche, action à droite, `flex items-end justify-between gap-4 mb-6`.
- **Mobile d'abord** : jamais de défilement horizontal. Utiliser `min-w-0` + `truncate` sur les textes dans un `flex`, et `flex-wrap` sur les rangées de puces et de boutons.

### 4.5 Bordures, anneaux, ombres

- **Bordure** : toujours `1px` (`border`), couleur `border-bord` par défaut.
- **Survol d'une carte** : la bordure s'éclaircit (`hover:border-doux/30` à `/40`) ou prend l'accent (`hover:border-rose/40`).
- **Anneau** `ring-1 ring-bord` sur les médaillons (icône dans un carré `bg-surface-2`) : il remplace la bordure sur les petits éléments.
- **Badges** : `ring-1 ring-inset` dans la couleur de l'état à 25–35 %.
- **Ombres** : on ne les met que dans deux cas :
  1. une **ombre colorée** sous ce qui est mis en avant (`shadow-lg shadow-rose/25` sur le bouton principal, `hover:shadow-2xl hover:shadow-rose/10` sur une affiche, `shadow-2xl shadow-rose/10` sous le lecteur vidéo) ;
  2. une **ombre noire profonde** sous ce qui flotte (`shadow-2xl shadow-black/60`).

  Aucune ombre grise neutre sur les cartes posées.

### 4.6 Halos et dégradés d'ambiance

C'est ce qui donne la profondeur « studio ». Il y a deux taches radiales floues, une rose et une cyan, placées en coins opposés.

**Halo global** (derrière l'en-tête, sur toutes les pages sauf la connexion) :
```tsx
<div
  aria-hidden
  className="pointer-events-none fixed inset-x-0 top-0 -z-10 h-80 bg-[radial-gradient(50%_60%_at_20%_0%,rgba(254,44,85,0.14),transparent),radial-gradient(40%_50%_at_85%_0%,rgba(37,244,238,0.10),transparent)]"
/>
```

**Halo de la page de connexion** (plus intense, centré) :
```tsx
<div
  aria-hidden
  className="pointer-events-none absolute inset-0 bg-[radial-gradient(40%_35%_at_30%_30%,rgba(254,44,85,0.22),transparent),radial-gradient(35%_35%_at_70%_70%,rgba(37,244,238,0.16),transparent)]"
/>
```

**Visuel de remplacement** (affiche sans image) : lueur prune au centre, `bg-[radial-gradient(80%_60%_at_50%_35%,#2a1a24,#141418)]`, avec un grand emoji `text-6xl sm:text-7xl opacity-80` au milieu.

**Voile de lisibilité** sur une image : `absolute inset-x-0 bottom-0 h-2/3 bg-gradient-to-t from-black/95 via-black/60 to-transparent`.

### 4.7 Couleurs sémantiques des états

Recette commune : fond à ~12 %, texte en teinte claire (famille Tailwind `-200` / `-300`) et non la couleur pure, anneau à ~30 %.

| État | Classes |
|---|---|
| Neutre / en cours | `bg-doux/15 text-doux ring-doux/25` (+ point qui pulse) |
| Info / choix à faire | `bg-cyan/12 text-cyan ring-cyan/30` |
| Attente / à faire | `bg-attente/12 text-amber-300 ring-attente/30` |
| Prêt / action | `bg-rose/15 text-pink-200 ring-rose/35` |
| Succès / terminé | `bg-ok/12 text-green-300 ring-ok/30` |
| Erreur | `bg-ko/12 text-red-300` (badge) ; `bg-ko/10 text-red-200` (message) |

**Encarts d'alerte** (`rounded-2xl border p-3`/`p-4 text-sm flex gap-2`, icône `mt-0.5 size-4 shrink-0` de la couleur pure) :
- information : `border-cyan/20 bg-cyan/5 text-zinc-300` + icône `Info text-cyan` ;
- avertissement : `border-attente/30 bg-attente/10 text-amber-100` + icône `TriangleAlert text-attente` ;
- erreur : `border-ko/30 bg-ko/10` + texte `text-red-200` ;
- mise en avant d'un contenu clé : `border-rose/25 bg-rose/8` + sur-titre `text-rose` avec une icône (`Zap`).

---

## 5. Recettes de composants

Recopier ces composants presque tels quels. Les classes sont exactes.

### 5.1 Bouton (4 variantes, 2 tailles)

```tsx
import type { ButtonHTMLAttributes, ReactNode } from "react";
import { Loader2 } from "lucide-react";

export type Variante = "principal" | "secondaire" | "fantome" | "danger";

const STYLES: Record<Variante, string> = {
  principal: "bg-rose text-white shadow-lg shadow-rose/25 hover:bg-rose-fonce hover:shadow-rose/40 disabled:shadow-none",
  secondaire: "border border-bord bg-surface-2 text-texte hover:border-doux/50 hover:bg-bord/60",
  fantome: "text-doux hover:bg-surface-2 hover:text-texte",
  danger: "border border-ko/40 bg-ko/10 text-red-200 hover:bg-ko/20",
};

// Exportée pour styler un <Link>, un <a> ou un <label> comme un bouton.
export function classesBouton(variante: Variante = "principal", petit = false, large = false): string {
  return [
    "inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-all duration-150",
    "active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-45 disabled:active:scale-100",
    petit ? "min-h-9 px-3 text-sm" : "min-h-11 px-4",
    large ? "w-full" : "",
    STYLES[variante],
  ].join(" ");
}

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variante?: Variante; petit?: boolean; large?: boolean; chargement?: boolean; icone?: ReactNode;
}

export function Bouton({ variante, petit, large, chargement, icone, children, className = "", disabled, ...reste }: Props) {
  return (
    <button type="button" className={`${classesBouton(variante, petit, large)} ${className}`} disabled={disabled || chargement} {...reste}>
      {chargement ? <Loader2 className="size-4 animate-spin" /> : icone}
      {children}
    </button>
  );
}
```

Règles d'usage :
- **Un seul bouton `principal` visible par zone.**
- Le bouton d'envoi d'un formulaire est `large` et peut être agrandi (`className="h-13 text-base"`).
- Pendant le chargement, l'icône est remplacée par une roue `Loader2` et le bouton est désactivé.
- Hauteur minimale de 44 px (`min-h-11`) pour le tactile.
- **Lien texte d'action secondaire** : `text-sm font-semibold text-cyan hover:underline`.
- **Lien retour** : `inline-flex items-center gap-1.5 text-sm text-doux transition hover:text-texte` + `ArrowLeft`.

### 5.2 Carte / section de formulaire

```tsx
<div className="rounded-3xl border border-bord bg-surface p-5 sm:p-6">
  <h2 className="mb-4 text-sm font-semibold tracking-wide text-doux uppercase">{titre}</h2>
  {children}
</div>
```

Une carte de liste ajoute `animate-apparition` et un décalage d'animation en cascade (§6).

### 5.3 Champs

```tsx
// Champ texte (avec icône optionnelle à gauche)
<div className="relative mt-2">
  <Lock className="pointer-events-none absolute top-1/2 left-3.5 size-4 -translate-y-1/2 text-doux" />
  <input className="h-12 w-full rounded-xl border border-bord bg-surface-2 pr-4 pl-10 text-base outline-none transition focus:border-rose/70 focus:ring-4 focus:ring-rose/15" />
</div>

// Zone de texte
<textarea className="mt-2 w-full resize-y rounded-xl border border-bord bg-surface-2 px-4 py-3 outline-none transition placeholder:text-zinc-600 focus:border-rose/70 focus:ring-4 focus:ring-rose/15" />
```

- Libellé : `block text-sm font-medium text-doux` (ou `text-sm text-doux`), placé au-dessus du champ.
- **Focus d'un champ** : bordure rose + large halo rose très léger (`focus:ring-4 focus:ring-rose/15`).
- **Focus clavier global** (boutons, liens) : contour cyan de 2 px (défini dans la base).
- `text-base` (16 px) sur les champs, pour éviter le zoom automatique sur iPhone.

### 5.4 Interrupteur (toggle)

```tsx
<label className="mt-4 flex cursor-pointer items-center justify-between gap-4">
  <span className="text-sm">Libellé</span>
  <input type="checkbox" className="peer sr-only" checked={v} onChange={...} />
  <span className="relative h-7 w-12 shrink-0 rounded-full bg-bord transition peer-checked:bg-rose peer-focus-visible:ring-2 peer-focus-visible:ring-cyan after:absolute after:top-1 after:left-1 after:size-5 after:rounded-full after:bg-white after:transition peer-checked:after:translate-x-5" />
</label>
```

### 5.5 Compteur − / +

```tsx
<div className="flex items-center gap-1 rounded-xl border border-bord bg-surface-2 p-1">
  <button className="grid size-10 place-items-center rounded-lg hover:bg-bord disabled:opacity-30"><Minus className="size-4" /></button>
  <span className="w-10 text-center font-titre text-xl font-bold tabular-nums" aria-live="polite">{n}</span>
  <button className="grid size-10 place-items-center rounded-lg hover:bg-bord disabled:opacity-30"><Plus className="size-4" /></button>
</div>
```

### 5.6 Tuile sélectionnable (choix unique)

```tsx
<button
  type="button"
  aria-pressed={actif}
  className={`rounded-2xl border p-4 text-left transition ${
    actif
      ? "border-rose/70 bg-rose/10 shadow-lg shadow-rose/10 ring-1 ring-rose/40"
      : "border-bord bg-surface-2 hover:border-doux/40"
  }`}
>
  <span className="block font-semibold">{titre}</span>
  <span className="mt-0.5 block text-sm text-doux">{sous}</span>
</button>
```

À placer dans une grille `grid gap-3 sm:grid-cols-2`.

### 5.7 Badge d'état (pastille avec point)

```tsx
<span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${STYLE_ETAT} ${surImage ? "backdrop-blur-md" : ""}`}>
  <span className={`size-1.5 rounded-full bg-current ${enCours ? "animate-pulse-doux" : ""}`} />
  {libelle}
</span>
```

Posé sur une image, il reçoit `backdrop-blur-md`.

### 5.8 Puces

- **Puce info (tag)** : `rounded-lg bg-cyan/10 px-2 py-1 text-xs font-medium text-cyan`.
- **Puce neutre (réglage)** : `rounded-lg border border-bord bg-surface-2 px-2.5 py-1 text-xs font-medium text-zinc-300`.
- **Puce personne** : `rounded-full border border-bord bg-surface-2 px-3 py-1 text-xs`, avec le nom en `font-semibold` et `· détail` en `text-doux`.

### 5.9 Médaillons (numéros, icônes, logo)

- **Numéro neutre** : `grid size-9 place-items-center rounded-xl bg-surface-2 font-titre font-bold ring-1 ring-bord`.
- **Numéro vedette** : `fond-degrade grid size-9 shrink-0 place-items-center rounded-xl font-titre font-bold text-black`. **Texte noir** sur le dégradé.
- **Icône d'état vide** : `grid size-16 place-items-center rounded-2xl bg-surface-2 ring-1 ring-bord` + icône `size-7 text-rose`.
- **Logo de l'en-tête** : `grid size-9 place-items-center rounded-xl bg-surface-2 text-xl ring-1 ring-bord transition group-hover:ring-rose/50` contenant un emoji. À côté : `font-titre text-lg font-bold tracking-tight`, **le second mot** en `texte-degrade`.

### 5.10 Barre de progression

```tsx
<div role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}
     className={`w-full overflow-hidden rounded-full bg-white/10 ${epaisse ? "h-2" : "h-1.5"}`}>
  <div className="fond-degrade h-full rounded-full transition-[width] duration-500" style={{ width: `${pct}%` }} />
</div>
```

En dessous, le texte est `mt-1 text-[11px] font-medium text-zinc-300`, ou `mt-1.5 text-xs text-doux` pour « Envoi… 42 % ».

### 5.11 Frise d'étapes (stepper)

Des pastilles rondes `size-6 text-[11px] font-bold`, reliées par des traits `h-px flex-1` :
- **étape faite** : `fond-degrade text-black` + icône `Check` (`size-3.5 strokeWidth={3}`), trait `bg-gradient-to-r from-rose to-cyan` ;
- **étape active** : `bg-rose/20 text-rose ring-2 ring-rose/60`, libellé en `text-texte` ;
- **étape à venir** : `bg-surface-2 text-doux ring-1 ring-bord`, trait `bg-bord`.

Les libellés (`text-xs font-medium`) sont masqués sur téléphone (`max-sm:hidden`). La frise est placée dans un bandeau `rounded-2xl border border-bord bg-surface/60 px-4 py-3`.

### 5.12 Affiche 9:16 (carte de grille)

```tsx
<Link
  style={{ animationDelay: `${Math.min(index, 8) * 40}ms` }}
  className="group relative block aspect-[9/16] animate-apparition overflow-hidden rounded-2xl border border-bord bg-surface transition duration-300 hover:-translate-y-1 hover:border-rose/40 hover:shadow-2xl hover:shadow-rose/10"
>
  <img className="absolute inset-0 size-full object-cover transition duration-500 group-hover:scale-105" />
  <div className="absolute inset-x-0 bottom-0 h-2/3 bg-gradient-to-t from-black/95 via-black/60 to-transparent" />
  <div className="absolute top-2.5 left-2.5">{/* badge flottant */}</div>
  <div className="absolute inset-x-0 bottom-0 p-3">
    <h2 className="line-clamp-2 text-base leading-tight font-bold text-white sm:text-lg">{titre}</h2>
    <p className="mt-1 truncate text-xs text-zinc-300">{sousTitre}</p>
  </div>
</Link>
```

Au survol : la carte monte de 4 px, reçoit une bordure et une ombre roses, et l'image zoome à 105 %.

### 5.13 Bloc dépliable (code, prompt, détails)

```tsx
<div className="mt-4 rounded-2xl border border-bord bg-black/30">
  <button aria-expanded={ouvert} className="w-full px-4 py-2.5 text-left text-xs font-semibold tracking-wide text-doux uppercase hover:text-texte">
    {ouvert ? "Masquer le prompt" : "Voir le prompt"}
  </button>
  {ouvert && (
    <pre className="max-h-72 overflow-auto border-t border-bord px-4 py-3 font-mono text-xs leading-relaxed break-words whitespace-pre-wrap text-zinc-300">…</pre>
  )}
</div>
```

**Variante « lien avec chevron »** : `flex items-center gap-1.5 text-sm font-medium text-cyan hover:underline`, suivi de `ChevronDown className={\`size-4 transition ${ouvert ? "rotate-180" : ""}\`}`. Le contenu déplié est une liste avec un filet à gauche : `space-y-3 border-l border-bord pl-4`.

### 5.14 Zone de dépôt / emplacement vide

- **Au repos** : bordure en pointillés `rounded-2xl border border-dashed border-bord bg-black/30 py-6 text-sm font-medium text-doux transition hover:border-cyan/50 hover:text-cyan`.
- **Fichier glissé au-dessus de la carte** : `border-cyan bg-cyan/5 ring-2 ring-cyan/40`.
- **Carte « terminée »** : bordure `border-ok/25`.

Même pointillé pour un **état vide de page** (`rounded-3xl border border-dashed border-bord bg-surface/60 px-6 py-16 text-center`, avec médaillon, titre `text-xl font-bold`, texte `max-w-xs text-sm text-doux` et bouton principal), et pour une **zone d'action secondaire discrète**, comme « supprimer ce brouillon » (`rounded-2xl border border-dashed border-bord px-4 py-3`).

### 5.15 En-tête collant

```tsx
<header className="sticky top-0 z-30 border-b border-bord/70 bg-fond/75 backdrop-blur-xl">
  <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-3 px-4">
    {/* logo à gauche, bouton principal `petit` à droite (masqué sur la page qu'il ouvre) */}
  </div>
</header>
```

### 5.16 Barre d'action collante en bas

```tsx
<div className="sticky bottom-4 z-20 flex justify-center">
  <div className="flex w-full max-w-xl items-center gap-3 rounded-2xl border border-bord bg-surface/90 p-3 shadow-2xl shadow-black/60 backdrop-blur-xl">
    <p className="min-w-0 flex-1 truncate pl-1 text-sm text-doux">{explication}</p>
    <Bouton>Action</Bouton>
  </div>
</div>
```

### 5.17 Panneau de tâche flottant

C'est une **carte flottante en bas à droite sur PC**, et une **feuille pleine largeur en bas sur téléphone** :

```
fixed inset-x-3 bottom-3 z-40 animate-apparition overflow-hidden rounded-2xl border bg-surface/95
shadow-2xl shadow-black/60 backdrop-blur-xl sm:inset-x-auto sm:right-5 sm:bottom-5 sm:w-[26rem]
```

- La bordure dépend de l'état : `border-ok/40` (succès), `border-ko/40` (échec), sinon `border-bord`.
- Pendant la tâche, un **liseré dégradé qui pulse** en haut : `fond-degrade h-0.5 w-full animate-pulse-doux`.
- Icône à gauche : `Loader2 animate-spin text-cyan`, `CircleCheck text-ok` ou `CircleX text-ko`.
- Titre `truncate font-semibold`, puis sous-ligne `text-sm text-doux` (étape · durée).
- Journal dépliable en `pre` mono `text-[11px] bg-black/40 max-h-[40vh]`, qui défile automatiquement jusqu'en bas.

### 5.18 Notifications (toasts)

- **Pile** : `pointer-events-none fixed inset-x-0 bottom-4 z-50 flex flex-col items-center gap-2 px-4`, avec `aria-live="polite"`.
- **Notification** : `pointer-events-auto flex max-w-md animate-apparition items-start gap-2 rounded-xl border px-4 py-3 text-sm shadow-2xl backdrop-blur`, plus :
  - succès : `border-bord bg-surface-2/95 text-texte` + icône `CircleCheck text-ok` ;
  - erreur : `border-ko/40 bg-ko/15 text-red-100` + icône `CircleX text-ko`.
- Au plus 3 notifications à la fois. Durée : 2 s pour un succès, 6 s pour une erreur.

### 5.19 Chargement et erreur

- **Squelettes** : `<div aria-hidden className="squelette rounded-2xl h-48 w-full" />`. Ils reprennent la forme exacte du contenu attendu (affiches `aspect-[9/16]`, tuiles `h-20`, lignes `h-8 w-2/3` et `h-4 w-1/3`).
- **Attente longue** : médaillon rond avec un **anneau dégradé qui s'étend** (`fond-degrade absolute inset-0 animate-ping rounded-full opacity-20`) derrière une icône `size-7 text-rose` (`Wand2`), puis un titre `text-xl font-bold` qui finit par « … » et une estimation de durée en `text-sm text-doux`.
- **Erreur de chargement** : `rounded-2xl border border-ko/30 bg-ko/10 p-6 text-center`, message `text-red-200`, lien « Réessayer » en cyan.

### 5.20 Médias

- **Vidéo** : `aspect-[9/16] w-full rounded-3xl border border-bord bg-black object-contain shadow-2xl shadow-rose/10`, avec `playsInline`.
- **Aperçu à la demande** : un bouton en pointillés `Play` « Voir le clip » remplace la vidéo tant qu'on n'a pas cliqué.

### 5.21 Page de connexion

- Page entière `relative grid min-h-dvh place-items-center overflow-hidden px-4`, avec le halo intense (§4.6).
- Carte `relative w-full max-w-sm animate-apparition rounded-3xl border border-bord bg-surface/80 p-7 shadow-2xl backdrop-blur-xl`.
- Contenu centré :
  - médaillon `size-16 rounded-2xl text-4xl` (emoji) ;
  - `h1 text-2xl font-bold` avec le second mot en dégradé ;
  - accroche `text-sm text-doux` ;
  - champ avec icône `Lock` ;
  - bouton `large` « Entrer → » (`ArrowRight`) ;
  - mention `text-xs text-doux text-center`.

---

## 6. Mouvement

| Effet | Où | Comment |
|---|---|---|
| **Apparition** (fondu + montée de 8 px, 0,35 s) | Toute carte, section, page, panneau, notification | `animate-apparition` |
| **Cascade** | Grilles et listes | `style={{ animationDelay: \`${Math.min(i, 8) * 40}ms\` }}` (60 ms pour de grosses cartes) |
| **Pulsation douce** | Point d'un badge « en cours », liseré de tâche | `animate-pulse-doux` |
| **Scintillement** | Squelettes | utilitaire `squelette` |
| **Levée au survol** | Cartes cliquables | `transition duration-300 hover:-translate-y-1` + bordure et ombre roses |
| **Zoom d'image** | Affiche | `transition duration-500 group-hover:scale-105` |
| **Pression** | Boutons | `active:scale-[0.98]`, `transition-all duration-150` |
| **Chevron** | Dépliables | `transition` + `rotate-180` |
| **Largeur de progression** | Barres | `transition-[width] duration-500` |

Tout est coupé par `prefers-reduced-motion` (bloc à la fin de la feuille de style). Pas d'animation d'entrée de page complexe, pas de parallaxe, pas de rebond.

---

## 7. Accessibilité et tactile (non négociable)

- Cibles tactiles ≥ 44 px (`min-h-11`, `size-10` au minimum pour un bouton icône).
- Focus clavier visible : contour cyan de 2 px, décalé de 2 px.
- `aria-expanded` sur les dépliables, `aria-pressed` sur les tuiles, `role="progressbar"` + `aria-valuenow`, `aria-live="polite"` sur les notifications, le panneau de tâche et les compteurs, `aria-label` sur les boutons qui n'ont qu'une icône, `aria-hidden` sur les halos et les squelettes.
- Contraste :
  - texte principal `#f4f4f5`, secondaire `#a1a1aa` sur `#09090b` ou `#141418` ;
  - sur une couleur d'état, utiliser les teintes claires `-100` à `-300`, jamais la couleur pure pour du texte long.
- Pas de défilement horizontal. Marges latérales de 16 px (`px-4`) sur téléphone.
- `min-h-dvh` plutôt que `min-h-screen`, et `viewport-fit=cover`.

---

## 8. Ton des textes

- **Tutoiement**, phrases courtes, verbes d'action sur les boutons (« Générer », « Choisir cette variante », « Copier le prompt », « Déposer », « Remplacer »).
- Confirmation de succès brève, terminée par « ✔ » (« Prompt copié ✔ »).
- Les états vides et les attentes **expliquent la suite** et donnent une durée (« Compte 1 à 2 minutes : l'avancement s'affiche en bas de l'écran »).
- Une ellipse « … » pour ce qui est en cours (« Démarrage… », « Envoi… 42 % »).
- Emojis : seulement comme **identité** (logo, visuels de remplacement, « ✨ Nouvelle série »), jamais comme décoration dans le texte courant.

---

## 9. Adapter à un autre projet

**À garder tel quel** (c'est ce qui fait le style) :
- les jetons de couleur, les deux polices, les rayons, la hiérarchie des surfaces ;
- le dégradé rose → cyan réservé aux éléments vedette ;
- le sur-titre en capitales espacées ;
- les éléments flottants translucides et floutés ;
- les halos radiaux ;
- les animations `apparition`, `pulse-doux` et `squelette`.

**À changer selon le projet** :
- l'emoji du logo et du favicon (🍓), le nom (« Verger **Drama** », le second mot en dégradé) ;
- les visuels de remplacement (emoji de fruit choisi par hachage de l'identifiant) ;
- le format des médias (9:16 ici ; pour un autre contenu, garder la même recette d'affiche avec un autre `aspect-*`).

**Changer d'accents sans casser l'ensemble :**
- remplacer `--color-rose` / `--color-rose-fonce` / `--color-cyan` par une autre paire **chaud saturé + froid lumineux** (ex. orange `#ff5a1f` + bleu électrique `#3b82f6`) ;
- mettre à jour les `rgba(...)` des halos en conséquence ;
- garder l'accent chaud pour l'action et l'accent froid pour l'information et le focus.

**Sans Tailwind :** chaque classe se traduit directement en CSS. Par exemple `bg-rose/10` = `background: color-mix(in srgb, var(--color-rose) 10%, transparent)`, `rounded-3xl` = `border-radius: 1.5rem`, `backdrop-blur-xl` = `backdrop-filter: blur(24px)`. Conserver les mêmes jetons dans `:root`.

---

## 10. Liste de contrôle avant de livrer une page

- [ ] Fond `fond`, cartes `surface` + `border-bord`, zones internes `surface-2` ou `black/30`.
- [ ] Un seul bouton `principal` par zone. Les autres sont `secondaire`, `fantome` ou des liens cyan.
- [ ] Titres en Space Grotesk, sur-titres de section en capitales `text-doux tracking-wide`.
- [ ] Chiffres en `font-titre tabular-nums`.
- [ ] Arrondis dégressifs (3xl → 2xl → xl → lg → full).
- [ ] Ce qui flotte est translucide, flouté et porte une ombre noire.
- [ ] `animate-apparition` sur les blocs, en cascade sur les listes.
- [ ] Squelettes de la forme du contenu pendant le chargement, encart rouge avec « Réessayer » en cas d'erreur.
- [ ] Rendu vérifié à 375 px de large : pas de défilement horizontal, cibles ≥ 44 px, textes tronqués proprement.
- [ ] Focus cyan visible au clavier, attributs `aria-*` en place, animations coupées avec `prefers-reduced-motion`.
