# Interface de ContractGuardian (F6)

Application React (Vite) : importer un contrat PDF, lire ses clauses (F2), poser des questions (F5),
voir les points à vérifier entre clauses (F3, **expérimental**) et tester une hypothèse (F4).
Chaque passage cité affiche sa page et ses positions. Un bandeau rappelle en permanence que l'outil
**ne donne pas d'avis juridique**.

```bash
cd frontend
npm install          # une seule fois
npm run dev          # http://localhost:5173 (l'API doit tourner sur le port 8000)
```

Les appels `/api/...` sont relayés vers l'API FastAPI par le serveur de Vite (`vite.config.js`).
Code : `src/App.jsx` (composants `Clauses`, `Questions`, `Alertes`, `Nli`), styles : `src/App.css`.
