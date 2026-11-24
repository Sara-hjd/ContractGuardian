// Configuration de Vite (serveur de développement de l'interface, F6).
// Les appels à /api sont relayés vers l'API FastAPI (port 8000) : pas de problème de CORS.
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': { target: 'http://127.0.0.1:8000', rewrite: (chemin) => chemin.replace(/^\/api/, '') } },
  },
})
