# HANDOVER — Dashboard

Passation de la session du 2026-09-29. Branche : `claude/fervent-cray-gczk5v`. Aucune PR n'est ouverte pour l'instant.

> **Règle** : ce fichier est mis à jour **avant chaque commit** (voir `CLAUDE.md`).

Documents de référence :
- spec validée (v1.3) : `docs/specs/2026-09-29-dashboard-design.md` ;
- guide de style (copie de `AI-Video-Editor/docs/design/style.md`) : `docs/design/style.md`.

---

## 0. À faire en premier : tester sous Windows

Les 24 tests n'ont tourné que sous **Linux** (conteneur cloud, Python 3.11.15). Le PC cible est sous **Windows** et le code a des branches propres à Windows qui n'ont **jamais été exécutées** :
- `backend/dashboard/processus.py:105-117`, drapeaux `CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW | CREATE_BREAKAWAY_FROM_JOB`, avec un repli sans `BREAKAWAY` en cas d'`OSError` ;
- `processus.py:29-38`, choix du Python (`.venv\Scripts\python.exe`) ;
- `psutil.Process.cwd()` et `psutil.net_connections()` sous Windows (`processus.py:82-94`, `147-186`).

Commandes à lancer sur le PC Windows, depuis `Dashboard\` :

```
python main.py                     # crée backend\.venv ; Ctrl+C une fois le serveur démarré
cd backend
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m pytest
```

Résultat attendu : `24 passed`. Si un test échoue, corriger **avant** d'attaquer l'étape 2, et noter la cause ici.

Points à surveiller sous Windows :
- `test_le_module_survit_au_dashboard_et_est_adopte` (`backend/tests/test_modules.py`) : c'est le test qui vérifie que le détachement (`BREAKAWAY`) fonctionne ;
- `test_allumer_puis_eteindre_tout_l_arbre` : vérifie que `terminate()` (qui vaut `TerminateProcess` sous Windows) tue bien l'enfant lancé par `--enfant` ;
- si le « breakaway » est refusé, le journal du module contient `⚠  [dashboard] Détachement refusé par Windows`.

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
| (ce commit) | `HANDOVER.md`, `CLAUDE.md`, commandes de test Windows dans `README.md`, note `.venv` dans la spec §5.1 |

### 1.2 Fichiers

**Point d'entrée** : `main.py` à la racine, qui n'utilise que la bibliothèque standard. Il fait, dans l'ordre :
1. vérifie Python 3.11–3.13 ;
2. crée `backend/.venv` et installe `backend/requirements.txt` (le marqueur `backend/.venv/.installe` évite de réinstaller) ;
3. compile `frontend/` **seulement si `frontend/package.json` existe** : ce n'est pas encore le cas ;
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

**Configuration** : `modules.toml` (versionné). Les fichiers locaux ignorés par git sont `config.local.toml`, `etat/`, `journaux/` et `backend/.venv/`.

**Tests** (`backend/tests/`) :
- `faux_module.py` est copié en `main.py` dans un dossier temporaire. Ses options sont `--port`, `--enfant`, `--retard S` et `--mourir` (qui sort avec le code 3). Il lit `taches.json` et `sans_etat` dans son dossier courant ;
- `conftest.py` : la classe `Installation` fabrique un faux `Dashboard/` et ses modules voisins, avec `intervalle=0.1` et `delai_arret=2`. Les adresses `LOCAL` (127.0.0.1) et `DISTANT` (192.168.1.20) sont passées à `TestClient(client=...)`. En fin de test, un nettoyage tue tous les faux modules ;
- `test_modules.py` (15 tests), `test_acces.py` (8 tests), `test_journal.py` (1 test).

### 1.3 Vérifications faites

- `pytest` : `24 passed` trois fois de suite (`-p no:randomly`), environ 8,5 s.
- `ruff check . ../main.py` : `All checks passed!`.
- `python3 main.py < /dev/null` lancé pour de vrai : création du venv et installation OK, message « Aucun code d'accès défini : le dashboard n'est accessible que depuis ce PC. », `GET /api/modules` répond, et les 3 modules sont en `ERROR` avec « Dossier introuvable : /home/user/AI-Video-Generator ». C'est normal : dans le conteneur, les clones s'appellent `ai-video-generator` en minuscules.
- Vrai Generator branché le temps d'un essai, avec un lien symbolique supprimé ensuite : `STARTING` puis `ERROR`, code 1, et le journal affiché `ModuleNotFoundError: No module named 'dotenv'`. C'est normal ici, puisque le conteneur n'avait pas son `.venv`. Le chemin « mort inattendue » fonctionne donc avec une vraie app.

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

---

## 3. Bugs et incertitudes

1. **Le Generator plante s'il est lancé sans `WEB_ACCESS_CODE`.** Dans `AI-Video-Generator/web/server.py:300-305`, `lancer()` lève `AppError("WEB_ACCESS_CODE est vide dans .env : choisis un code avant d'ouvrir l'interface au réseau …")` quand l'option `--local` est absente. Tant que l'étape 4 n'est pas faite, il faut donc **garder `WEB_ACCESS_CODE` rempli** dans le `.env` du Generator, sinon le dashboard l'affiche en `ERROR`. Avec le code rempli, sa route d'état répondra 401, et le dashboard l'affichera `ON` avec « État détaillé indisponible. », ce qui est attendu.
2. **Windows non testé** : voir §0.
3. `psutil.Process.cwd()` peut lever `AccessDenied` pour un processus d'un autre utilisateur ou lancé en administrateur. Dans ce cas, l'adoption par port échoue proprement : le module reste `OFF` et `demarrer` répond 409 « le port … est déjà utilisé ».
4. Sous Windows, `terminate()` est brutal : les apps ne peuvent pas faire de ménage à l'arrêt. C'est accepté par la spec §5.3, la pop-up prévient.
5. En l'état `ON` + « Ne répond plus. » (le processus vit, mais le port ne répond plus), rien ne repasse en `ERROR`. C'est voulu, mais à surveiller à l'usage.
6. L'avertissement `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2` est filtré dans `backend/pyproject.toml`. Il faudra passer à `httpx2` si une future version de Starlette retire la prise en charge.

---

## 4. Prochaines étapes, dans l'ordre

1. **Faire tourner les tests sous Windows** (§0) et corriger ce qui casse.
2. **Étape 2 : interface** (`frontend/`, React 19 + Vite + TS + Tailwind v4 + lucide-react + `@fontsource-variable/inter` et `space-grotesk`), selon la spec §7.0 à §7.4 et `docs/design/style.md` à la lettre :
   - `/connexion` (style.md §5.21, médaillon 🤓, « Dash**board** ») ;
   - `/` : grille de cartes, sondage de `GET /api/modules` toutes les 1,5 s tant que l'onglet est visible ;
   - carte : médaillon emoji, `h2` avec le dernier mot du nom en `texte-degrade`, badge d'état, bouton `Power` (lucide), bloc tâche + progression, ligne file GPU, journal dépliable (sondage de `/journal` toutes les 2 s seulement s'il est déplié) ;
   - pop-up d'arrêt déclenchée par une réponse **409 avec `taches`** de `POST /arreter`, puis renvoi avec `{force: true}` ;
   - `main.py` compile déjà `frontend/` dès que `frontend/package.json` existe.
3. **Étape 3 : vue module** `/module/<id>` (spec §7.5) : barre de 48 px + iframe `${location.protocol}//${location.hostname}:${port}/`.
4. **Étape 4 : une PR par app** (spec §6.3) : route `GET /api/dashboard/etat` (contrat §6.2). Dans le Generator, supprimer aussi le code d'accès (`web/auth.py`, `web/server.py`, `common/config.py`, `.env.example`, `README.md`, `main.py doctor`, `tests/test_jobs_auth.py`, `tests/test_server_api.py`).
5. *(plus tard)* File GPU (spec §9).
6. *(plus tard)* Démarrage avec Windows (spec §11).

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
- Ne pas modifier les 3 apps depuis ce dépôt : chaque changement passe par une PR dans le dépôt de l'app (étape 4).
