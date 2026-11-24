# `src/cg/api/` — API FastAPI (F6)

Rôle : façade HTTP de l'application, utilisée par l'interface React (`frontend/`). Toute la logique
est dans `services.py`, qui réutilise F1 à F5. **Chaque réponse contient un `avertissement`** (pas
d'avis juridique) et **chaque citation porte sa page et ses positions** (règle 1).

| Route | Rôle | Fonctionnalité |
|---|---|---|
| `GET /sante` | Base joignable, modèle de langage configuré | — |
| `GET /contrats` | Contrats importés | — |
| `POST /contrats` | Importer un PDF : extraction par blocs, segments, vecteurs, clauses, traçabilité vérifiée en SQL | F1, F2, F5, F7 |
| `GET /contrats/{id}/clauses` | Clauses détectées, avec citation exacte | F2 (D-012, D-013) |
| `POST /contrats/{id}/questions` | `{"question", "mode": "rag" \| "extractif"}` : réponse citée ou abstention | F5 (D-015 à D-017) |
| `GET /contrats/{id}/alertes` | Points à vérifier entre clauses — **expérimental** | F3 (D-018) |
| `POST /contrats/{id}/nli` | `{"hypothese"}` : implique / contredit / non mentionné + évidences | F4 (D-014) |

## Lancer

```bash
open -a Docker && docker compose up -d                       # base
open -a Ollama                                               # LLM local (D-016)
PYTHONPATH=src .venv/bin/python -m uvicorn cg.api.app:app --port 8000
# documentation interactive : http://127.0.0.1:8000/docs
```

Les modèles entraînés doivent être dans `models/` (voir le README principal, « Installation »).
