# Dashboard 🤓

Page d'accueil pour piloter mes applications locales : chaque module a une carte, un bouton d'alimentation et un état (OFF, STARTING, ON, WORKING, WAITING, STOPPING, ERROR).

| Carte | Dossier | Port |
|---|---|---|
| 🍓 Verger Drama | `../AI-Video-Generator` | 8081 |
| ✂️ Short Studio | `../AI-YouTube-to-TikTok` | 8082 |
| 🎬 Montage IA | `../AI-Video-Editor` | 8083 |

Spec : `docs/specs/2026-09-29-dashboard-design.md`. Guide de style : `docs/design/style.md`.

## Lancer

```
python main.py
```

- Il faut Python 3.11 à 3.13 et Node.js (pour compiler l'interface). Le premier lancement crée `backend/.venv`, installe les dépendances et compile `frontend/` ; il recompile ensuite l'interface dès que ses sources changent.
- Au premier lancement, choisis le **code d'accès** du dashboard. Il est enregistré dans `config.local.toml`, qui n'est pas versionné. La variable `DASHBOARD_ACCESS_CODE` a priorité sur ce fichier.
- Adresse : http://localhost:8080. L'adresse pour le téléphone (même Wi-Fi) s'affiche dans la console.
- Sur le PC lui-même, aucun code n'est demandé.
- Les modules allumés continuent de tourner quand le dashboard s'arrête. Au redémarrage, il les retrouve.

## Configuration

`modules.toml` décrit les modules : dossier, commande, port, emoji. Le Python utilisé pour un module est, dans l'ordre :
1. la clé `python` du module ;
2. sinon, le `.venv` du module ;
3. sinon, le Python du système.

Journaux des modules : `journaux/<id>.log` (lancement en cours) et `<id>.log.1` (lancement précédent).

## Développer l'interface

Avec le serveur lancé (`python main.py`), dans un autre terminal :

```
cd frontend
npm run dev
```

Vite relaie `/api` vers le port 8080. Vérification des types : `npm run verifier`.

## Tests

Depuis le dossier `backend/`. Le premier `python main.py` a créé `backend/.venv` ; installe ensuite les outils de test une fois :

**Windows (PowerShell ou cmd) :**

```
cd backend
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m pytest
```

**Linux / macOS :**

```
cd backend
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest
```

Résultat attendu : `24 passed`. Les tests lancent de faux modules (`tests/faux_module.py`) sur des ports libres : ils ne touchent pas aux vrais modules.
