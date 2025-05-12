import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000, // Port pour le serveur de développement Vite
    proxy: {
      // Proxy pour les appels API vers le backend Nginx/Gateway
      // Toutes les requêtes commençant par /api seront redirigées
      '/api': {
        target: 'http://localhost:80', // Nginx écoute sur le port 80
        changeOrigin: true,
        // Pas besoin de rewrite ici car Nginx gère déjà le rewrite /api -> /
      },
    },
  },
  build: {
    outDir: 'build', // Spécifier le répertoire de sortie pour la construction
  },
});
