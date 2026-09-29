# Dashboard — spécification

Version 1, du 2026-09-29. Statut : **à valider**.
Guide de style : `docs/design/style.md`, copie conforme de celui d'AI-Video-Editor. L'interface doit le respecter à la lettre.

---

## 1. Objectif

Une page d'accueil unique pour piloter mes applications locales :

| Module | Dépôt / dossier | Rôle |
|---|---|---|
| AI-Video-Generator | `../AI-Video-Generator` | Mini-séries « fruits IA » : veille, scénario, prompts, montage |
| AI-YouTube-to-TikTok | `../AI-YouTube-to-TikTok` | Découpe de vidéos YouTube en extraits verticaux, puis publication |
| AI-Video-Editor | `../AI-Video-Editor` | Montage IA |

Le dashboard permet de :
1. voir l'état de chaque module (OFF, STARTING, ON, WORKING, WAITING…) ;
2. allumer ou éteindre un module avec un bouton d'alimentation (lance ou arrête son `main.py`) ;
3. ouvrir un module allumé dans le même onglet, avec une barre de retour vers le dashboard ;
4. plus tard : gérer une file d'attente commune pour les tâches qui utilisent le GPU (§9).

Il est accessible depuis le PC et depuis le téléphone, sur le même Wi-Fi.

### Hors périmètre de la v1

- Démarrage automatique avec Windows (étape finale, §11).
- Logique de la file d'attente GPU : seuls l'emplacement dans l'API et l'affichage sont prévus (§9).
- Authentification : pas de mot de passe. Le dashboard est ouvert à tout appareil du réseau local (§10).

---

## 2. Contexte technique relevé dans les 3 apps

| | AI-Video-Generator | AI-YouTube-to-TikTok | AI-Video-Editor |
|---|---|---|---|
| Commande web | `main.py web` (ou sans argument) | `main.py web` (ou sans argument) | `main.py` |
| Port par défaut | 8000 (`WEB_PORT`) | 8000 | 8000 (`PORT`) |
| Adresse d'écoute par défaut | 0.0.0.0 (`--local` = 127.0.0.1) | **127.0.0.1** (`--host`) | 0.0.0.0 |
| Ouvre un navigateur | non | **oui** (`--no-browser` pour l'éviter) | non |
| Environnement Python | Python du système | se relance dans son `.venv` s'il existe | crée et utilise `backend/.venv` |
| Protection | **code d'accès** (`WEB_ACCESS_CODE`, cookie `SameSite=Lax`) | aucune | aucune |
| Gestion de tâches existante | `web/jobs.py` (`GestionnaireTaches`) | `yt2short/web/jobs.py` | table `taches` (`db.py`) |
| Processus enfants | non | oui (relance dans le venv) | oui (`uvicorn` en sous-processus) |

Conséquences :
- **Conflit de ports** : les 3 apps visent le port 8000. Le dashboard impose un port à chacune (§5.1).
- **Arguments différents** : la commande de lancement est configurée module par module (§5.1).
- **Arbre de processus** : pour arrêter un module, il faut tuer `main.py` **et tous ses descendants**, sinon `uvicorn` reste en vie et garde le port.
- **Code d'accès du Generator** : l'iframe ouverte depuis le téléphone affichera la page de code du Generator la première fois (cookie valable 30 jours). C'est acceptable. En revanche, la route d'état interrogée par le dashboard doit en être exemptée pour les appels locaux (§6.3).

---

## 3. Pile technique

Même pile que les autres apps, pour rester homogène :

| Élément | Choix |
|---|---|
| Serveur | Python 3.11–3.13, **FastAPI** + **uvicorn** |
| Gestion des processus | **psutil**, pour l'arbre de processus, l'adoption par PID et les ports ouverts, sous Windows comme sous Linux |
| Client HTTP (interrogation des modules) | **httpx** |
| Configuration | `modules.toml`, lu avec `tomllib` (bibliothèque standard) |
| Interface | React 19 + Vite + TypeScript, **Tailwind CSS v4**, **lucide-react**, polices Inter et Space Grotesk embarquées (cf. `style.md` §2) |
| Lancement | `python main.py` à la racine, sur le modèle d'AI-Video-Editor : crée `backend/.venv`, installe les dépendances, compile `frontend/dist` si besoin, puis démarre le serveur |

Plateforme cible : **Windows**. Le code doit aussi tourner sous Linux pour les tests (voir §5.3).

---

## 4. Arborescence

```
Dashboard/
├── main.py                    # point d'entrée (bibliothèque standard uniquement)
├── modules.toml               # configuration des modules (versionnée)
├── backend/
│   ├── requirements.txt       # fastapi, uvicorn, psutil, httpx
│   ├── requirements-dev.txt   # pytest, …
│   ├── dashboard/
│   │   ├── app.py             # routes /api/* + service de frontend/dist (repli SPA)
│   │   ├── config.py          # lecture de modules.toml
│   │   ├── processus.py       # lancer / arrêter / adopter un module
│   │   ├── etat.py            # machine à états + interrogation des modules
│   │   └── journal.py         # lecture de la fin des journaux
│   └── tests/
├── frontend/                  # React + Vite + Tailwind
├── etat/                      # (ignoré par git) <id>.json : PID, date de création, port
├── journaux/                  # (ignoré par git) <id>.log et <id>.log.1
└── docs/
    ├── design/style.md
    └── specs/
```

---

## 5. Gestion des processus

### 5.1 Configuration : `modules.toml`

```toml
[dashboard]
port = 8080          # un port différent de 8000, pour ne pas gêner un module lancé à la main

[[modules]]
id = "generator"
nom = "AI Video Generator"
description = "Mini-séries fruits IA : veille, scénario, prompts, montage."
emoji = "🍓"
dossier = "../AI-Video-Generator"
commande = ["main.py", "web", "--port", "{port}"]
port = 8101
gpu = true

[[modules]]
id = "yt2tiktok"
nom = "YouTube → TikTok"
description = "Découpe une vidéo YouTube en extraits verticaux et les publie."
emoji = "✂️"
dossier = "../AI-YouTube-to-TikTok"
commande = ["main.py", "web", "--host", "0.0.0.0", "--port", "{port}", "--no-browser"]
port = 8102
gpu = true

[[modules]]
id = "editor"
nom = "AI Video Editor"
description = "Montage IA."
emoji = "🎬"
dossier = "../AI-Video-Editor"
commande = ["main.py", "--port", "{port}"]
port = 8103
gpu = true
```

- `dossier` est relatif au dossier du dashboard.
- `{port}` est remplacé par le port du module.
- Le Python utilisé est, dans cet ordre : la clé optionnelle `python` du module, puis `<dossier>/.venv/Scripts/python.exe` (ou `bin/python`) s'il existe, puis `py -3` sous Windows (`python3` ailleurs). **Jamais le Python du venv du dashboard**, qui n'a pas les dépendances des modules.
- Au démarrage, le dashboard vérifie la config : ports distincts, dossier et `main.py` présents. Un module mal configuré s'affiche avec l'état `ERROR` et le message correspondant, sans empêcher les autres de fonctionner.

### 5.2 Lancement

`POST /api/modules/{id}/demarrer` :
1. Refusé (409) si le module n'est pas OFF ou ERROR, ou si son port est déjà occupé par un autre programme.
2. Le journal précédent est renommé en `<id>.log.1`.
3. `subprocess.Popen` est appelé avec :
   - `cwd = dossier`, et stdout + stderr redirigés vers `journaux/<id>.log` ;
   - les variables d'environnement `PYTHONUNBUFFERED=1`, `PYTHONIOENCODING=utf-8` et `DASHBOARD_URL=http://<ip>:8080` (réservée pour plus tard) ;
   - sous Windows, `creationflags = CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW | CREATE_BREAKAWAY_FROM_JOB` : pas de fenêtre de console, et le module **survit à l'arrêt du dashboard**. Si le « breakaway » est refusé, on relance sans ce drapeau et on écrit un avertissement dans le journal ;
   - sous Linux, `start_new_session=True`.
4. `etat/<id>.json` enregistre `{pid, create_time, port, lance_le}`, où `create_time` est la date de création du processus donnée par psutil.
5. Le module passe à `STARTING`. Le premier lancement peut durer plusieurs minutes (création du venv, `npm build`) : **pas de délai maximal**, le journal permet de suivre l'avancement.

### 5.3 Arrêt

`POST /api/modules/{id}/arreter` avec le corps `{ "force": false }` :
1. Si le module est WORKING ou WAITING et que `force` vaut `false` : réponse **409** avec la liste des tâches en cours. L'interface affiche alors la pop-up de confirmation (§7.4). C'est le serveur qui tranche, pour éviter une course : une tâche peut démarrer entre l'affichage et le clic.
2. Sinon, le module passe à `STOPPING`, puis :
   - on récupère l'arbre complet : `psutil.Process(pid).children(recursive=True)` + la racine ;
   - on appelle `terminate()` sur tous les processus, on attend jusqu'à 5 s, puis on appelle `kill()` sur les survivants. Sous Windows, `terminate()` est déjà un arrêt brutal (`TerminateProcess`) : c'est accepté, et la pop-up prévient de la perte de la tâche ;
   - en filet de sécurité, on tue aussi tout processus qui écoute encore sur le port du module ;
   - `etat/<id>.json` est supprimé et le module revient à `OFF`.

### 5.4 Adoption au démarrage du dashboard

Les modules continuent de tourner quand le dashboard s'arrête. Au démarrage, pour chaque module :
- si `etat/<id>.json` existe, et que le PID existe avec la même `create_time`, le processus est **adopté** ;
- sinon, si quelque chose écoute sur le port du module, on cherche son PID avec `psutil.net_connections()` et on l'adopte. Cela couvre un module lancé à la main avec `--port 810x` ;
- sinon, le module est OFF et le fichier d'état périmé est supprimé.

Le dashboard **n'allume jamais un module de lui-même** : ils sont OFF par défaut.

Limite connue : le journal d'un module adopté n'est complet que si le dashboard l'a lancé lui-même.

---

## 6. États et API d'état des modules

### 6.1 Machine à états

| État | Libellé affiché | Condition | Carte cliquable | Bouton alimentation |
|---|---|---|---|---|
| `OFF` | OFF | aucun processus | non | allumer |
| `STARTING` | Démarrage… | processus vivant, port pas encore joignable | non | désactivé (roue) |
| `ON` | ON | port joignable, aucune tâche | oui | éteindre |
| `WORKING` | WORKING | au moins une tâche en cours | oui | éteindre, avec confirmation |
| `WAITING` | WAITING | une tâche GPU en file, aucune en cours (§9) | oui | éteindre, avec confirmation |
| `STOPPING` | Arrêt… | arrêt demandé | non | désactivé (roue) |
| `ERROR` | ERROR | processus mort de façon inattendue, ou config invalide | non | relancer |

Les libellés restent en anglais (OFF / ON / WORKING / WAITING / ERROR), comme dans ta demande.

Passage d'un état à l'autre :
- la boucle de surveillance tourne toutes les **2 s** côté serveur ;
- le processus est-il vivant (psutil) ? le port répond-il (`GET http://127.0.0.1:<port>/api/dashboard/etat`, délai d'attente 1 s) ?
- processus mort alors qu'on n'a pas demandé l'arrêt → `ERROR`, avec le code de sortie et les 20 dernières lignes du journal ;
- l'app répond sur le port mais n'expose pas encore `/api/dashboard/etat` (404) → `ON`, avec la mention « état détaillé indisponible ». Le dashboard reste ainsi utilisable avant la modification des apps.

### 6.2 Contrat de la route d'état (à ajouter dans chaque app)

`GET /api/dashboard/etat`, en JSON :

```json
{
  "version": 1,
  "taches": [
    {
      "id": "a1b2",
      "libelle": "Génération du scénario",
      "etape": "Scène 3/6",
      "progression": 42,
      "gpu": true,
      "statut": "en_cours",
      "position_file": null,
      "debut": "2026-09-29T14:02:11Z"
    }
  ]
}
```

- `progression` : un entier de 0 à 100, ou `null` si inconnu (barre indéterminée).
- `statut` : `en_cours` ou `en_attente`. `position_file` n'est rempli que pour `en_attente` (1 = prochaine).
- Si la liste est vide, le module est `ON`. Au moins un `en_cours` : `WORKING`. Seulement des `en_attente` : `WAITING`.
- La route doit répondre en moins de 200 ms, sans calcul lourd.

### 6.3 Modifications à apporter aux 3 apps

Chaque modification fera l'objet d'une PR séparée dans le dépôt de l'app, après validation de cette spec :

| App | Travail |
|---|---|
| AI-Video-Generator | Route `/api/dashboard/etat` branchée sur `GestionnaireTaches`. La route est **exemptée du code d'accès pour les appels venant de 127.0.0.1** |
| AI-YouTube-to-TikTok | Route branchée sur `yt2short/web/jobs.py` |
| AI-Video-Editor | Route branchée sur la table `taches` |
| Les 3 | Vérifier que rien n'empêche l'affichage en iframe : pas d'en-tête `X-Frame-Options` ni `frame-ancestors`. Aucun trouvé à ce jour |

Les modules sont sur le même hôte que le dashboard, seul le port change : ils sont « same-site » pour le navigateur. Le cookie `SameSite=Lax` du Generator fonctionne donc dans l'iframe.

---

## 7. Interface

Toutes les classes viennent de `style.md`. Seuls les éléments propres au dashboard sont décrits ici.

### 7.1 Page d'accueil `/`

- Halo global (§4.6) et en-tête collant (§5.15) avec le logo : médaillon emoji + nom, le second mot en `texte-degrade` (voir la question ouverte n° 1).
- Conteneur `mx-auto max-w-6xl px-4 pt-6 pb-40`.
- En-tête de page : `h1` « Modules », avec en sous-titre un résumé (`text-sm text-doux`, ex. « 1 allumé · 1 au travail »).
- Grille `grid gap-4 md:grid-cols-2 lg:grid-cols-3`, avec cartes en cascade (`animate-apparition`, décalage de 60 ms).
- Pendant le premier chargement : 3 squelettes `squelette rounded-3xl h-56`. Si l'API ne répond pas : encart d'erreur avec « Réessayer ».
- Mise à jour : l'interface interroge `GET /api/modules` toutes les **1,5 s** tant que l'onglet est visible (`visibilitychange`).

### 7.2 Carte de module

```
┌──────────────────────────────────────────────┐
│ [🍓]  AI Video Generator             ( ⏻ )   │  médaillon, h2, bouton alimentation
│       ● WORKING                              │  badge d'état
│                                              │
│ Mini-séries fruits IA : veille, scénario…    │  description text-sm text-doux
│                                              │
│ ┌ TÂCHE EN COURS ──────────────────────────┐ │  zone interne bg-black/30 rounded-2xl
│ │ Génération du scénario · Scène 3/6       │ │
│ │ ▓▓▓▓▓▓▓▓░░░░░░░░░░  42 %                 │ │  barre dégradée
│ └──────────────────────────────────────────┘ │
│ En attente GPU · 2e dans la file              │  si WAITING
│ ▸ Voir le journal                             │  bloc dépliable
└──────────────────────────────────────────────┘
```

- Conteneur : `rounded-3xl border border-bord bg-surface p-5 sm:p-6`.
- **Cliquable** (ON / WORKING / WAITING) : c'est un lien vers `/module/<id>`, avec `transition duration-300 hover:-translate-y-1 hover:border-rose/40 hover:shadow-2xl hover:shadow-rose/10`.
- **Non cliquable** (OFF / STARTING / STOPPING / ERROR) : `aria-disabled="true"`, pas d'effet au survol, curseur par défaut. Un clic ne fait **rien**.
- Bordure selon l'état : `border-ok/25` si ON, `border-cyan/30` si WORKING, `border-attente/30` si WAITING, `border-ko/30` si ERROR, sinon `border-bord`. Une carte OFF est légèrement éteinte (médaillon et titre en `opacity-60`).
- Badge d'état (§5.7) :

| État | Classes |
|---|---|
| OFF | `bg-doux/15 text-doux ring-doux/25` |
| STARTING / STOPPING | `bg-doux/15 text-doux ring-doux/25` + point qui pulse |
| ON | `bg-ok/12 text-green-300 ring-ok/30` |
| WORKING | `bg-cyan/12 text-cyan ring-cyan/30` + point qui pulse |
| WAITING | `bg-attente/12 text-amber-300 ring-attente/30` + point qui pulse |
| ERROR | `bg-ko/12 text-red-300 ring-ko/30` |

- Bloc « tâche en cours » : visible seulement en WORKING. Sur-titre `text-xs font-semibold tracking-wide uppercase text-cyan`, libellé `· étape`, puis la barre de progression (§5.10). Si `progression` vaut `null`, la barre est pleine et pulse (`fond-degrade animate-pulse-doux`). S'il y a plusieurs tâches, une ligne par tâche.
- Ligne de file GPU : visible seulement en WAITING, `text-sm text-amber-300`, ex. « En attente du GPU · 2e dans la file ».
- ERROR : encart d'erreur (`border-ko/30 bg-ko/10 text-red-200`) avec le message et le code de sortie. Le journal est déplié par défaut.
- **Journal** : bloc dépliable (§5.13) « Voir le journal » / « Masquer le journal ». Il affiche les 200 dernières lignes (`pre` mono `text-[11px] bg-black/40 max-h-[40vh]`), défile automatiquement vers le bas et se rafraîchit toutes les 2 s **seulement quand il est déplié**. En STARTING, il est déplié par défaut. Le dépliage est mémorisé par module dans `localStorage`.
- Tous les éléments interactifs de la carte (bouton, journal) appellent `stopPropagation` + `preventDefault` pour ne pas déclencher l'ouverture du module.

### 7.3 Bouton d'alimentation

- Icône lucide **`Power`** (le symbole ⏻ : cercle ouvert traversé d'un trait), `size-5`.
- Forme : `grid size-11 shrink-0 place-items-center rounded-full transition-all duration-150 active:scale-95`.
- Selon l'état :
  - **OFF / ERROR** : `border border-bord bg-surface-2 text-doux hover:border-rose/50 hover:text-rose`, `aria-label="Allumer <nom>"` ;
  - **ON / WORKING / WAITING** : `bg-rose text-white shadow-lg shadow-rose/30 hover:bg-rose-fonce`, `aria-label="Éteindre <nom>"`. C'est le seul aplat rose de la carte, ce qui respecte la règle « un seul principal par zone » ;
  - **STARTING / STOPPING** : désactivé, icône remplacée par `Loader2 animate-spin`.
- `aria-pressed` vaut `true` quand le module est allumé.
- En cas d'échec de la requête : notification d'erreur (§5.18), ex. « Impossible d'allumer AI Video Generator : le port 8101 est déjà utilisé. »

### 7.4 Pop-up de confirmation d'arrêt

Elle s'affiche quand l'arrêt renvoie 409, c'est-à-dire quand le module est WORKING ou WAITING. Le guide de style n'a pas de recette de modale : on la construit avec les règles des éléments flottants.

- Voile : `fixed inset-0 z-50 grid place-items-center bg-black/60 backdrop-blur-sm px-4`.
- Boîte : `w-full max-w-md animate-apparition rounded-3xl border border-bord bg-surface/95 p-6 shadow-2xl shadow-black/60 backdrop-blur-xl`, avec `role="alertdialog"`, `aria-modal="true"` et `aria-labelledby`.
- Contenu :
  - `h2 text-xl font-bold` : « Arrêter AI Video Generator ? » ;
  - encart d'avertissement (`border-attente/30 bg-attente/10 text-amber-100` + `TriangleAlert`) : « Une tâche est en cours. Elle sera interrompue et perdue. » ;
  - liste des tâches (libellé · étape · progression) ;
  - boutons alignés à droite, `flex flex-wrap justify-end gap-2` : **« Annuler »** (`secondaire`, focus initial) et **« Arrêter quand même »** (`danger`, icône `Power`).
- Échap ou un clic sur le voile ferme la pop-up (= Annuler). Le focus reste piégé dans la boîte.
- « Arrêter quand même » envoie `POST …/arreter {force: true}` : le bouton affiche une roue, puis la pop-up se ferme.

### 7.5 Vue module `/module/<id>`

- Page pleine hauteur `h-dvh flex flex-col`.
- **Barre du haut** : flottante, translucide, fixe. Classes `h-12 shrink-0 border-b border-bord/70 bg-fond/75 backdrop-blur-xl px-3 flex items-center gap-3`, avec de gauche à droite :
  - lien retour `← Dashboard` (§5.1, lien retour) ;
  - médaillon emoji `size-7 rounded-lg` + nom `font-titre font-bold truncate` ;
  - badge d'état ;
  - si WORKING, un mini-libellé de la tâche + %, masqué sur téléphone ;
  - à droite : bouton icône `ExternalLink` (`aria-label="Ouvrir dans un nouvel onglet"`) et le bouton d'alimentation en petit (`size-9`), avec la même pop-up.
- En dessous : `<iframe class="min-h-0 flex-1 w-full border-0 bg-fond">`, avec `src = ${location.protocol}//${location.hostname}:${port}/`. L'URL fonctionne donc depuis le téléphone comme depuis le PC.
- Si le module est OFF ou ERROR à l'ouverture de l'URL : redirection vers `/`.
- Si le module s'arrête pendant qu'on le regarde : voile par-dessus l'iframe, « AI Video Generator est éteint », avec un bouton principal « Retour au dashboard ».
- La barre du haut suit l'état du module toutes les 1,5 s.

### 7.6 Ton

Tutoiement, verbes d'action (« Allumer », « Éteindre », « Arrêter quand même »), ellipse pour ce qui est en cours (« Démarrage… »), comme dans `style.md` §8. En STARTING, le texte explique la suite : « Premier lancement : compte quelques minutes (installation). Suis l'avancement dans le journal. »

---

## 8. API du dashboard

| Méthode | Route | Réponse |
|---|---|---|
| GET | `/api/modules` | liste des modules : `id, nom, description, emoji, port, gpu, etat, message, taches[], depuis` |
| GET | `/api/modules/{id}` | un module |
| POST | `/api/modules/{id}/demarrer` | 202 ; 409 si ce n'est pas possible (avec `detail`) |
| POST | `/api/modules/{id}/arreter` | corps `{force}` ; 202 ; **409 `{detail, taches}` si occupé et `force=false`** |
| GET | `/api/modules/{id}/journal?lignes=200` | `{lignes: [...]}` |
| GET | `/api/sante` | `{ok: true}` |

Les requêtes de démarrage ou d'arrêt envoyées en double pour un même module sont sérialisées par un verrou par module.

---

## 9. File d'attente GPU (à définir plus tard)

Ce qui est posé dès la v1, pour ne pas avoir à tout refaire :
- l'état `WAITING`, `position_file` dans le contrat d'état et l'affichage sur la carte ;
- la clé `gpu = true` par module.

Piste pour plus tard : le dashboard devient l'**arbitre du GPU**. Avant une tâche GPU, une app appelle `POST {DASHBOARD_URL}/api/gpu/jeton` et attend son tour, puis rend le jeton en fin de tâche. C'est pour cela que la variable `DASHBOARD_URL` est déjà transmise au lancement. Tout le reste (priorités, délais, que faire si le dashboard est absent) sera spécifié à part.

---

## 10. Sécurité

- Le dashboard écoute sur `0.0.0.0:8080`, **sans authentification**. Tout appareil du Wi-Fi peut allumer ou éteindre les modules : c'est un choix assumé pour un réseau domestique.
- Le serveur ne lance **que** les commandes de `modules.toml`. Aucune route n'accepte de commande, de chemin ou d'argument libre.
- L'identifiant `{id}` d'un module est validé contre la configuration.

---

## 11. Démarrage automatique (plus tard)

Prévu : une tâche du Planificateur de tâches Windows, déclenchée à l'ouverture de session, qui lance `main.py` sans fenêtre (`pythonw.exe` ou `--sans-console`). Ce sera spécifié à part.

---

## 12. Tests

- **Serveur (pytest)** : un faux module (`tests/faux_module.py`) ouvre un petit serveur HTTP sur un port libre, expose `/api/dashboard/etat` avec des tâches pilotables et lance un processus enfant. Cas testés :
  - allumer, puis STARTING → ON ;
  - éteindre : tout l'arbre meurt et le port est libéré ;
  - refus 409 si WORKING sans `force`, et arrêt avec `force` ;
  - adoption après le redémarrage du dashboard ;
  - mort inattendue → ERROR ;
  - app sans route d'état → ON « état détaillé indisponible » ;
  - config invalide.
- **Interface** : vérification manuelle à 375 px et sur PC, avec la liste de contrôle de `style.md` §10.
- **Validation finale sous Windows** : allumer et éteindre les 3 vrais modules, fermer le dashboard pendant une tâche, le rouvrir et vérifier l'adoption.

---

## 13. Découpage des livraisons

1. Squelette : `main.py`, serveur, `modules.toml`, lancement, arrêt et adoption des processus, tests.
2. Interface : accueil, cartes, bouton d'alimentation, journal, pop-up.
3. Vue module : iframe + barre de retour.
4. Route `/api/dashboard/etat` dans chacune des 3 apps : une PR par dépôt.
5. *(plus tard)* File GPU.
6. *(plus tard)* Démarrage avec Windows.

---

## 14. Questions ouvertes

1. **Nom et emoji du dashboard.** Proposition : « Studio **Hub** » avec 🎛️. Le second mot est en dégradé.
2. **Ports.** Dashboard sur 8080, modules sur 8101, 8102 et 8103 : ça te va ?
3. **Noms des dossiers sur le disque.** Sont-ils exactement `AI-Video-Generator`, `AI-YouTube-to-TikTok` et `AI-Video-Editor`, à côté de `Dashboard` ?
4. **Emojis et descriptions des cartes.** 🍓, ✂️, 🎬 : à ajuster.
5. **Code d'accès du Generator** : l'iframe te le demandera une fois par appareil. Si tu préfères, on peut le désactiver quand l'app est lancée par le dashboard.
