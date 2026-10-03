# Consignes pour les sessions de code

- **Avant chaque commit, mettre à jour `HANDOVER.md`** : commits, fichiers, décisions, bugs et prochaines étapes. Le commit qui modifie le code contient aussi la mise à jour du HANDOVER.
- Lire `HANDOVER.md` en début de session. La spec de référence est `docs/specs/2026-09-29-dashboard-design.md`, et l'interface suit `docs/design/style.md` à la lettre.
- Tests : `cd backend && .venv/bin/python -m pytest` (sous Windows : `.venv\Scripts\python -m pytest`). Lint : `ruff check . ../main.py`.
- Textes, commentaires et noms en français, comme dans les autres apps.
