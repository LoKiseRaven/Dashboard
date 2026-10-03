# HANDOVER — Dashboard

Passation de la session du 2026-09-29. Branche : `claude/fervent-cray-gczk5v` → PR [LoKiseRaven/Dashboard#1](https://github.com/LoKiseRaven/Dashboard/pull/1) (tout commit poussé sur la branche la met à jour ; ne pas en ouvrir une autre).

> **Règle** : ce fichier est mis à jour **avant chaque commit** (voir `CLAUDE.md`).

Documents de référence :
- spec validée (v1.3) : `docs/specs/2026-09-29-dashboard-design.md` ;
- guide de style (copie de `AI-Video-Editor/docs/design/style.md`) : `docs/design/style.md`.

---

## 0. Tests sous Windows : validés

L'utilisateur a lancé les 24 tests du serveur sur son PC Windows le 2026-09-29 : **tous passent**. Commandes, depuis `Dashboard\` :

```
python main.py                     # crée backend\.venv (Ctrl+C une fois le serveur démarré)
cd backend
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m pytest
```

À refaire sous Windows après chaque modification de `backend/dashboard/processus.py`, dont les branches `if WINDOWS:` (l. 105-117) ne tournent pas sous Linux.

---

## 1. Ce qui a été fait

### 1.1 Commits (du plus ancien au plus récent)

| Commit | Contenu |
|---|---|
| `93d5a79` | Spec v1 + copie du guide de style |
| `33f8089` | Spec v1.1 : code d'accès retiré du Generator, mis sur le dashboard |
| `cac0247` | Spec : liste des fichiers du Generator touchés par ce retrait |
| `5def53d` | Spec v1.2 : nom « Dashboard » 🤓, cartes au nom et à l'emoji de chaque app, sans description |
| `fc021a4` | Spec v1.3 validée : ports 8080 (dashboard), 8081 à 8083 (modules) |
| `d69cf29` | Étape 1 : serveur (processus, états, code d'accès) + 24 tests |
| `aae0eb8` | `HANDOVER.md`, `CLAUDE.md`, commandes de test Windows dans `README.md`, note `.venv` dans la spec §5.1 |
| `2628a52` | Étape 2 : interface `frontend/` (connexion, accueil, cartes, bouton ⏻, journal, pop-up d'arrêt). Spec §7.2 : suppression d'`aria-disabled` sur la carte, lien étiré |
| `0bf31f1` | Étape 3 : vue module `/module/:id` (barre + iframe, voile quand le module s'éteint). ⏻ « petit » en `size-10`. Option `--host` du faux module. Spec §7.5 précisée |
| (ce commit) | Étape 4 livrée dans les 3 dépôts d'apps (voir §1.4) ; spec §6.3 et HANDOVER à jour |

### 1.2 Fichiers

**Point d'entrée** : `main.py` à la racine, qui n'utilise que la bibliothèque standard. Il fait, dans l'ordre :
1. vérifie Python 3.11–3.13 ;
2. crée `backend/.venv` et installe `backend/requirements.txt` (le marqueur `backend/.venv/.installe` évite de réinstaller) ;
3. compile `frontend/` (`npm install` puis `npm run build`) si `frontend/dist/index.html` manque ou est plus ancien que les sources. Il faut Node.js ;
4. lit le code d'accès (`DASHBOARD_ACCESS_CODE`, sinon `config.local.toml`). S'il n'y en a pas et qu'on est dans une console, il le demande deux fois avec `getpass` et l'écrit dans `config.local.toml`. Sans code, il écoute sur 127.0.0.1 seulement ;
5. lance `uvicorn --factory dashboard.app:creer_app_defaut` avec `cwd=backend`.

**Serveur** (`backend/dashboard/`) :

| Fichier | Rôle |
|---|---|
| `config.py` | `charger()` lit `modules.toml` et renvoie un `Config` (dataclass figée). `Module.erreur` contient le problème de config (dossier ou `main.py` absent, port en double) : le module reste listé, en `ERROR`. `lire_code_acces()` (l. 57) |
| `processus.py` | `lancer()` (l. 97) : `Popen` détaché, sortie vers `journaux/<id>.log`, écriture de `etat/<id>.json` (`pid`, `create_time`, `port`, `lance_le`). `adopter()` (l. 126) : par le fichier d'état, sinon par le port. `processus_du_module_sur_port()` (l. 147) : n'accepte que des processus dont le `cwd` est dans le dossier du module. `racine_du_module()` (l. 169) : remonte les parents Python du même dossier. `arreter()` (l. 211) : `terminate` de l'arbre, attente de `delai_arret` (5 s), `kill`, puis filet par le port |
| `etat.py` | `Etat` (enum de 7 états), `Suivi` (état d'un module, avec un `asyncio.Lock` par module), `Superviseur` : boucle toutes les `config.intervalle` s (2 s), `allumer()` (l. 194), `eteindre()` (l. 211) qui revérifie les tâches auprès du module avant de refuser ou d'accepter, puis `_eteindre()` en tâche de fond |
| `acces.py` | Cookie `dashboard_acces` = HMAC-SHA256(code, `etat/secret.bin`), 30 jours. `est_local()`, `LimiteurEchecs` (5 échecs, puis 2 s de pause). Copié du `web/auth.py` du Generator |
| `journal.py` | `tourner()` (`.log` → `.log.1`), `fin()` (lit les 256 derniers Ko, garde le dernier état des lignes réécrites par `\r`) |
| `app.py` | `creer_app(config, superviseur=None, dossier_front=None)`. Middleware 401 sur `/api/*` sauf `/api/sante`, `/api/session`, `/api/connexion`. Routes de la spec §8. Repli SPA sur `frontend/dist/index.html` (404 JSON « Interface non compilée » tant que le dossier n'existe pas) |

**Interface** (`frontend/src/`, React 19 + Vite 8 + TS + Tailwind v4 + lucide-react + react-router 7 ; même `package.json` et même `styles.css` qu'AI-Video-Editor) :

| Fichier | Rôle |
|---|---|
| `main.tsx` | Routes : `/connexion` (hors cadre), puis `Protege` (renvoie vers `/connexion?suite=…` si `session.connecte` est faux) → `/module/:id` (pleine page) et `Cadre` (halo + en-tête) → `/` et `*`. `<Toasts />` est hors des routes |
| `api.ts` | `requete()` : sur une réponse 401 (sauf `/api/connexion`), émet l'événement `dashboard:deconnecte`, qui fait repasser la session à non connectée. `tachesDuRefus(e)` extrait les tâches d'un 409. `adresseModule(m)` = `${protocol}//${hostname}:${port}/`. `decouperNom()` isole le dernier mot du nom |
| `types.ts` | `Module`, `Tache`, `Session`, listes `ALLUMES`, `OCCUPES`, `EN_TRANSITION` |
| `hooks/contexte.tsx` | Contextes `useToasts` (3 au plus, 2 s / 6 s) et `useSession` (`GET /api/session` au démarrage) |
| `hooks/sondage.ts` | `useSondage(charger, intervalle, actif)` : appel immédiat puis périodique, **en pause quand l'onglet est caché**, jamais deux requêtes en parallèle, `recharger()` pour forcer |
| `composants/ui.tsx` | `Bouton`/`classesBouton` (guide §5.1, accepte `ref`), `BadgeEtat` (libellés et couleurs de la spec §7.2), `NomDegrade`, `Progression` (`pct` null → barre pleine qui pulse), `Encart`, `Halo` |
| `composants/cadre.tsx` | `EnTete` (🤓 « Dash**board** », bouton `LogOut` masqué si `session.local`), `Toasts` |
| `composants/Alimentation.tsx` | `BoutonAlimentation` (bouton rond `size-11`, ou `size-10` en `petit` ; icône `Power`, rose si allumé) : `demarrer` ou `arreter` ; sur un 409 avec `taches`, ouvre `PopupArret` (**portail** vers `document.body`, `role="alertdialog"`, focus initial sur « Annuler », Échap et clic sur le voile ferment, Tab piégé) qui renvoie `arreter(id, true)`. Réutilisé en `petit` dans la barre de la vue module |
| `composants/CarteModule.tsx` | Carte (spec §7.2). Si allumée : un `<Link>` étiré (`absolute inset-0 z-0`) ; le bouton et le journal sont en `relative z-10` |
| `composants/Journal.tsx` | Journal dépliable, 200 lignes, sondage de 2 s seulement s'il est déplié ; le choix est retenu dans `localStorage` (`journal-ouvert:<id>`), sinon il est déplié par défaut en STARTING et ERROR ; défilement automatique sauf si l'on est remonté. Masqué quand le module est OFF |
| `composants/taches.tsx` | `LigneTache`, `resumeTache`, `texteFile` (« En attente du GPU · 2e dans la file ») |
| `pages/Connexion.tsx` | Guide §5.21. `suite` n'accepte qu'un chemin interne (`/…`, pas `//…`) |
| `pages/Accueil.tsx` | `h1` « Modules », résumé (« 1 allumé · 1 au travail · 1 en erreur »), grille `md:grid-cols-2 lg:grid-cols-3`, 3 squelettes au chargement, encart d'erreur avec « Réessayer » |
| `pages/VueModule.tsx` | Vue module (spec §7.5), route **hors de `Cadre`** mais sous `Protege`. Barre `h-12` : lien retour (flèche seule sous `sm`), médaillon, nom (tronqué), `BadgeEtat`, mini-libellé de tâche (masqué sous `md`), lien `ExternalLink` (`target="_blank"`) et `BoutonAlimentation petit`. En dessous, `<iframe key={session} src={adresseModule(m)}>`. Sondage de `GET /api/modules/<id>` toutes les 1,5 s ; un 404 est transformé en `"inconnu"` → redirection. `ouvert` (état au premier chargement) : si le module n'était pas allumé, redirection vers `/`. Ensuite, s'il s'éteint : voile (« Arrêt de… », « … est éteint », « … s'est arrêté ») ; s'il est rallumé depuis la barre, `session` est incrémenté, ce qui recharge l'iframe. Titre de l'onglet : « <nom> · Dashboard » |

`vite.config.ts` relaie `/api` vers `http://localhost:8080` en mode `npm run dev`.

**Configuration** : `modules.toml` (versionné). Les fichiers locaux ignorés par git sont `config.local.toml`, `etat/`, `journaux/`, `backend/.venv/`, `frontend/node_modules/` et `frontend/dist/`.

**Tests** (`backend/tests/`) :
- `faux_module.py` est copié en `main.py` dans un dossier temporaire. Ses options sont `--port`, `--host` (défaut 127.0.0.1), `--enfant`, `--retard S` et `--mourir` (qui sort avec le code 3). Il lit `taches.json` et `sans_etat` dans son dossier courant ;
- `conftest.py` : la classe `Installation` fabrique un faux `Dashboard/` et ses modules voisins, avec `intervalle=0.1` et `delai_arret=2`. Les adresses `LOCAL` (127.0.0.1) et `DISTANT` (192.168.1.20) sont passées à `TestClient(client=...)`. En fin de test, un nettoyage tue tous les faux modules ;
- `test_modules.py` (15 tests), `test_acces.py` (8 tests), `test_journal.py` (1 test).

### 1.3 Vérifications faites

- `pytest` : `24 passed` trois fois de suite (`-p no:randomly`), environ 8,5 s.
- `ruff check . ../main.py` : `All checks passed!`.
- `python3 main.py < /dev/null` lancé pour de vrai : création du venv et installation OK, message « Aucun code d'accès défini : le dashboard n'est accessible que depuis ce PC. », `GET /api/modules` répond, et les 3 modules sont en `ERROR` avec « Dossier introuvable : /home/user/AI-Video-Generator ». C'est normal : dans le conteneur, les clones s'appellent `ai-video-generator` en minuscules.
- Étape 2 : `npx tsc -b --noEmit` OK, `npm run build` OK (JS de 288 Ko, 92 Ko compressé).
- Étape 2, dans Chromium avec Playwright, sur PC (1280 px) et téléphone (375 px). Serveur de démo avec 4 faux modules (WORKING avec `taches.json`, STARTING avec `--retard 900`, OFF, ERROR de config) et code `1234`, ouvert via l'IP du conteneur pour que le code soit demandé. Vérifié :
  - redirection vers `/connexion` ; « Code incorrect. » affiché ; entrée avec le bon code ;
  - le clic sur ⏻ d'un module WORKING ouvre la pop-up, avec le focus sur « Annuler » ; Échap la ferme ;
  - un clic sur une carte OFF ne change pas d'URL ; allumer un module l'amène à ON ; un clic sur la carte allumée ouvre `/module/editor` ;
  - **défilement horizontal à 375 px : 0 px**, après correction : les cartes débordaient de 5 px à cause d'un long chemin dans l'encart d'erreur. Corrigé avec `min-w-0` sur l'`<article>` (élément de grille).
- Étape 3, Playwright, même serveur de démo mais faux modules lancés avec `--host 0.0.0.0` (sinon l'iframe, ouverte par l'IP du conteneur, ne les joint pas). 12 vérifications OK :
  - clic sur le titre d'une carte allumée → `/module/editor`, iframe avec le contenu du module, titre d'onglet « Montage IA · Dashboard », pas d'en-tête du dashboard ;
  - ⏻ de la barre → voile « Montage IA est éteint » ; rallumer → le voile disparaît et l'iframe réaffiche le module ;
  - « ← Dashboard » ramène à `/` ; mini-libellé « Génération du scénario · Scène 3/6 · 42 % » ; ⏻ sur un module WORKING → pop-up, Échap la ferme ;
  - `/module/yt2tiktok` (éteint) et `/module/inexistant` → redirection vers `/` ;
  - à 375 px : 0 px de débordement, cibles de la barre à 40 px.
- Défaut trouvé et corrigé pendant ces essais : `aria-disabled="true" sur la carte (demandé par la spec v1.3) s'étendait au bouton ⏻, qui était annoncé comme désactivé. L'attribut est retiré et la spec §7.2 corrigée.
- Vrai Generator branché le temps d'un essai, avec un lien symbolique supprimé ensuite : `STARTING` puis `ERROR`, code 1, et le journal affiché `ModuleNotFoundError: No module named 'dotenv'`. C'est normal ici, puisque le conteneur n'avait pas son `.venv`. Le chemin « mort inattendue » fonctionne donc avec une vraie app.

---

### 1.4 Étape 4 : route d'état dans les 3 apps (une PR par dépôt)

Essai réel des étapes 1 à 3 sur le PC Windows : **validé par l'utilisateur** le 2026-09-29 (« ça fonctionne bien »).

| App | PR | Branche | Contenu | Vérifié (conteneur Linux) |
|---|---|---|---|---|
| Verger Drama | [LoKiseRaven/AI-Video-Generator#3](https://github.com/LoKiseRaven/AI-Video-Generator/pull/3) | `claude/dashboard-etat` | Route `api_etat_dashboard` (`web/server.py`) : tâche en cours, `gpu` vrai pour `assemblage`, `progression` toujours `null`. **Code d'accès supprimé** : `web/auth.py`, `/api/login`, `/api/session`, `WEB_ACCESS_CODE`, page `Connexion.tsx`, redirection 401 ; `create_app(taches=None)` ; `web/static/dist` recompilé | `pytest` 120 passed (126 avant) ; vrai serveur : démarre sans code, route OK, `/api/login` en 404 |
| Short Studio | [LoKiseRaven/AI-YouTube-to-TikTok#1](https://github.com/LoKiseRaven/AI-YouTube-to-TikTok/pull/1) | `claude/dashboard-etat` | Route dans `yt2short/web/server.py` : `progression` = `fait / total` en %, `gpu` vrai pour `decoupage` | `pytest --ignore=tests/test_clipper.py` 27 passed (25 avant ; `test_clipper` exige PyTorch CUDA) ; vrai serveur avec la commande du Dashboard : route OK par l'IP réseau |
| Montage IA | [LoKiseRaven/AI-Video-Editor#2](https://github.com/LoKiseRaven/AI-Video-Editor/pull/2) | `claude/dashboard-etat` | Routeur `backend/montage/api/dashboard.py` : tâches `en_cours` (progression %) **et `en_attente` (`position_file`)**, `gpu` vrai pour `analyse`. Registre `File.actives()` en mémoire dans `montage/taches.py`, car `Contexte.progres()` ne persiste pas la progression | `pytest` 44 passed, 14 skipped (ffmpeg absent) ; vrai serveur : route OK |

Chaque dépôt documente la route dans son README (Verger Drama §3 ter, Short Studio « Depuis le Dashboard », Montage IA « Dashboard »). Short Studio et Montage IA ont aussi une entrée dans leur HANDOVER.

**Test d'ensemble (2026-10-03, après l'ouverture des PR, qui aurait dû le précéder)** : le Dashboard pilotait les 3 vraies apps sur leurs branches `claude/dashboard-etat`, avec les commandes de `modules.toml` et `ffmpeg` installé par `apt` dans le conteneur. Résultats :
- les 3 apps passent à ON en environ 18 s, avec `detail_disponible = true` pour chacune ;
- Montage IA, deux vrais imports à la suite : WORKING « Import de video1.mp4 » 0 → 34 → 80 %, avec « Import de video2.mp4 » `en_attente` en position 1, puis la 2ᵉ en cours, puis ON ;
- Montage IA, une vraie analyse : WORKING avec `gpu = true`. Elle échoue ensuite sur « 403 Forbidden », car le téléchargement du modèle Whisper est bloqué dans le conteneur ; ce n'est pas un bug ;
- dans le navigateur, pendant l'import d'une vidéo de 10 min : la carte affiche la vraie tâche. ⏻ ouvre la pop-up qui la liste, « Arrêter quand même » mène à OFF, et **aucun processus survivant** n'est trouvé dans `ai-video-editor` (port 8083 libre) ;
- vue module : Verger Drama s'affiche directement, **sans écran de code** ; Short Studio s'affiche aussi ;
- avec ffmpeg, les suites complètes passent : Montage IA 58 passed (0 skipped), Verger Drama 120 passed ;
- non testé : une vraie tâche dans Short Studio (le découpage demande YouTube) et dans Verger Drama (la génération demande Claude Code). Le chemin d'affichage est le même que pour Montage IA.

Aucune modification du Dashboard lui-même n'a été nécessaire : il affiche déjà WORKING, WAITING, la progression et la file dès que la route répond (`detail_disponible` passe à `true`).

---

## 2. Décisions de conception (et pourquoi)

| Décision | Pourquoi |
|---|---|
| Ports 8080 (dashboard), 8081 à 8083 | Les 3 apps visent toutes 8000 par défaut. Ports choisis par l'utilisateur |
| Commande par module dans `modules.toml` | Les arguments diffèrent : Generator `main.py web --port`, YouTube-to-TikTok `main.py web --host 0.0.0.0 --port --no-browser` (sinon il écoute sur 127.0.0.1 et ouvre un navigateur), Editor `main.py --port` |
| Python du module = son `.venv` en priorité | L'utilisateur a confirmé que les 3 dépôts ont un `.venv` à la racine. Ne **jamais** utiliser le venv du dashboard, qui n'a pas leurs dépendances |
| Arrêt de tout l'arbre de processus | Editor lance `uvicorn` en sous-processus, et YouTube-to-TikTok se relance dans son venv. Tuer seulement `main.py` laisserait le port occupé |
| Modules détachés, puis adoptés au redémarrage | Choix de l'utilisateur : une génération en cours ne doit pas mourir si le dashboard s'arrête |
| Adoption par port **seulement si le `cwd` du processus est dans le dossier du module** | Sinon, un programme étranger qui occupe le port serait repris, puis tué à l'arrêt. Test : `test_programme_etranger_sur_le_port_n_est_jamais_adopte` |
| `racine_du_module` ne remonte que par des parents `python*`/`py*` | Ne jamais attraper le terminal depuis lequel un module a été lancé à la main |
| Refus 409 décidé par le serveur, qui revérifie auprès du module | Évite une course : une tâche peut démarrer entre l'affichage et le clic. Test : `test_refus_si_une_tache_demarre_juste_avant_l_arret` |
| App sans route `/api/dashboard/etat` (404, 401…) → `ON` + « État détaillé indisponible. » | Le dashboard reste utilisable avant l'étape 4 |
| Code d'accès sur le dashboard, **retiré du Generator**, modules non protégés | Choix de l'utilisateur (réseau domestique). Le cookie s'appelle `dashboard_acces` car les cookies sont partagés entre ports |
| Pas de code depuis 127.0.0.1 / ::1 | Pratique sur le PC. Servira aussi à la future API de file GPU appelée par les apps |
| Vue module en iframe sous une barre du dashboard | Choix de l'utilisateur : même onglet, avec un bouton retour. Aucune modif des apps |
| Carte allumée = lien étiré (`absolute inset-0`), pas un `<a>` autour de la carte | Un `<button>` (⏻, journal) ne peut pas être placé dans un `<a>`. Le lien étiré évite aussi que les clics de la pop-up, rendue dans un portail, remontent jusqu'à un lien |
| Pop-up en portail vers `document.body` | La carte a une transformation au survol (`hover:-translate-y-1`), qui fausserait le `position: fixed` d'un enfant |
| Sondage HTTP (1,5 s) plutôt que SSE | Plus simple, et suffisant pour 3 modules ; le sondage se met en pause quand l'onglet est caché |

---

## 3. Bugs et incertitudes

1. **Tant que [LoKiseRaven/AI-Video-Generator#3](https://github.com/LoKiseRaven/AI-Video-Generator/pull/3) n'est pas fusionnée**, le Generator plante s'il est lancé sans `WEB_ACCESS_CODE`. Dans `AI-Video-Generator/web/server.py:300-305`, `lancer()` lève `AppError("WEB_ACCESS_CODE est vide dans .env : choisis un code avant d'ouvrir l'interface au réseau …")` quand l'option `--local` est absente. Tant que l'étape 4 n'est pas faite, il faut donc **garder `WEB_ACCESS_CODE` rempli** dans le `.env` du Generator, sinon le dashboard l'affiche en `ERROR`. Avec le code rempli, sa route d'état répondra 401, et le dashboard l'affichera `ON` avec « État détaillé indisponible. », ce qui est attendu.
2. Windows : tests validés (§0), mais le **lancement réel des 3 apps** depuis le dashboard n'a pas encore été essayé sur le PC.
3. `psutil.Process.cwd()` peut lever `AccessDenied` pour un processus d'un autre utilisateur ou lancé en administrateur. Dans ce cas, l'adoption par port échoue proprement : le module reste `OFF` et `demarrer` répond 409 « le port … est déjà utilisé ».
4. Sous Windows, `terminate()` est brutal : les apps ne peuvent pas faire de ménage à l'arrêt. C'est accepté par la spec §5.3, la pop-up prévient.
5. En l'état `ON` + « Ne répond plus. » (le processus vit, mais le port ne répond plus), rien ne repasse en `ERROR`. C'est voulu, mais à surveiller à l'usage.
6. L'avertissement `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2` est filtré dans `backend/pyproject.toml`. Il faudra passer à `httpx2` si une future version de Starlette retire la prise en charge.
7. Un module en ERROR à cause de sa **configuration** (dossier absent…) affiche quand même le journal, qui dit « Journal vide. ». C'est sans gravité ; si c'est gênant, il faudra que l'API distingue une erreur de config d'un plantage.
8. Des erreurs 401 ou 409 apparaissent dans la console du navigateur quand le code est faux ou quand un arrêt est refusé : c'est **normal**, ce sont des réponses attendues de l'API.

---

## 4. Prochaines étapes, dans l'ordre

1. **Relire et fusionner les 3 PR** (§1.4, test d'ensemble fait dans le conteneur). Sur le PC, dans chaque dépôt, après la fusion : `git pull`, puis relancer la suite de tests complète, qui n'a pas pu tourner en entier dans le conteneur :
   - Short Studio : `test_clipper.py`, qui demande CUDA ;
   - Montage IA : les 14 tests qui demandent ffmpeg ;
   - Verger Drama : la suite complète avec les paquets NVIDIA.
2. **Essai réel avec le Dashboard** : lancer une vraie tâche dans chaque app et vérifier que la carte passe à WORKING, avec l'étape et le pourcentage (Short Studio, Montage IA). Dans Montage IA, lancer deux tâches pour voir WAITING et « prochain dans la file ». Verger Drama doit démarrer même sans `WEB_ACCESS_CODE`, et l'iframe ne doit plus demander de code.
3. *(plus tard)* File GPU (spec §9) : c'est le prochain gros chantier. À spécifier avec l'utilisateur :
   - qui arbitre (le Dashboard, via `DASHBOARD_URL`, déjà transmis aux modules) ;
   - la priorité entre apps ;
   - que faire si le Dashboard est éteint ;
   - la granularité : la tâche entière ou seulement les étapes GPU (la transcription Whisper par exemple).
4. *(plus tard)* Démarrage avec Windows (spec §11).

### Reproduire l'essai visuel (conteneur Linux)

1. Créer un dossier avec `Dashboard/modules.toml`, `Dashboard/config.local.toml` (`code_acces = "1234"`) et des dossiers voisins contenant chacun une copie de `backend/tests/faux_module.py` nommée `main.py`. Chaque module a `python = "<chemin>/backend/.venv/bin/python"` et `commande = ["main.py", "--host", "0.0.0.0", "--port", "{port}"]`.
2. Lancer `uvicorn.run(creer_app(charger(Path(".../modules.toml")), dossier_front=Path("frontend/dist")), host="0.0.0.0", port=8080)`.
3. Utiliser Playwright (paquet npm `playwright`, `executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"`), en visant l'IP du conteneur (`hostname -I`) et non 127.0.0.1, sinon le code n'est pas demandé.
4. Mesurer le débordement : `document.documentElement.scrollWidth - innerWidth` doit valoir 0 à 375 px.

---

## 5. À ne surtout PAS faire

- **Ne pas lancer un module avec le Python du dashboard** (`sys.executable` du serveur), qui n'a pas ses dépendances. Passer par `processus.python_module()`.
- **Ne pas assouplir le contrôle de `cwd`** dans `processus_du_module_sur_port()` : c'est ce qui empêche de tuer un programme étranger.
- **Ne pas remplacer l'arrêt de l'arbre par un simple `proc.terminate()`** sur `main.py` : `uvicorn` survivrait et garderait le port.
- **Ne pas mettre `DETACHED_PROCESS`** à la place de `CREATE_NO_WINDOW` sous Windows : les enfants des modules (npm, ffmpeg…) ouvriraient chacun une fenêtre de console.
- **Ne pas renommer le cookie `dashboard_acces`** en `acces` : c'est le nom du cookie du Generator, et les cookies sont partagés entre ports.
- **Ne pas faire allumer un module par le dashboard au démarrage** : ils sont OFF par défaut (demande explicite).
- **Ne pas utiliser `pkill -f "…dashboard.app…"` dans un shell d'outil** : le motif correspond à la ligne de commande du shell lui-même, qui se tue (exit 144). Pour arrêter un serveur de test, chercher son PID par le port avec psutil.
- **Ne pas ajouter de thème clair** (style.md §3).
- **Ne pas remettre `aria-disabled` sur `<article>`** dans `CarteModule.tsx` : il désactive aussi, pour l'accessibilité, le bouton ⏻ qu'il contient.
- **Ne pas enlever `min-w-0`** de l'`<article>` : sans lui, un long message dans une carte fait déborder la page sur téléphone.
- **Ne pas sortir `PopupArret` du portail** (`createPortal(…, document.body)`).
- **Ne pas retirer `key={session}` de l'iframe** dans `VueModule.tsx` : sans lui, après un rallumage, l'iframe garde la page d'erreur de connexion chargée pendant l'arrêt.
- **Ne pas remettre `/module/:id` sous `Cadre`** : la vue doit occuper toute la hauteur (`h-dvh`), sans l'en-tête du dashboard.
- **Ne pas descendre sous `size-10`** pour les boutons icônes (guide §7 : 40 px au minimum).
- Dans Playwright, pour ouvrir un module, cliquer sur le titre de la carte (`h2`, `force: true`) et non au centre du lien étiré : le bouton du journal, placé au-dessus, intercepte le clic (comportement voulu).
- **Dans Playwright, ne pas attendre un état avec `text=ON`** : c'est une recherche insensible à la casse, et « M**on**tage » la satisfait. Utiliser `text="ON"` (entre guillemets).
- Ne pas modifier les 3 apps depuis ce dépôt : chaque changement passe par une PR dans le dépôt de l'app.
- **Ne pas ouvrir de PR dans une app avant le test d'ensemble avec le Dashboard** (§1.4) : tests unitaires de l'app, puis Dashboard + vraie app lancée par `modules.toml`, avec au moins une vraie tâche observée. Pour lancer Montage IA sans réinstaller : lien `backend/.venv` vers un venv déjà prêt + `touch <venv>/.installe`, à retirer ensuite.
- **Ne pas changer le contrat de `/api/dashboard/etat`** (spec §6.2) d'un seul côté : les 3 apps et `backend/dashboard/etat.py` (`_taches_valides`, `etat_selon_taches`) doivent rester d'accord.
- Dans un clone superficiel d'une app (`git clone --depth 1`), `git push --force-with-lease` sur une branche est refusé (« stale info ») car seul `main` est suivi : passer le SHA attendu, `--force-with-lease=<branche>:<sha>`.
