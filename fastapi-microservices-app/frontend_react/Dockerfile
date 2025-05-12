# Étape 1: Construire l'application React
FROM node:20-alpine as builder

WORKDIR /app

# Copier package.json et package-lock.json (ou yarn.lock)
COPY package.json package-lock.json* ./

# Installer les dépendances
RUN npm install

# Copier le reste du code source de l'application
COPY . .

# Construire l'application pour la production
RUN npm run build

# Étape 2: Servir l'application avec Nginx
FROM nginx:1.25-alpine

# Copier les fichiers construits de l'étape précédente vers le répertoire de service de Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Copier une configuration Nginx personnalisée (si nécessaire, sinon Nginx servira index.html par défaut)
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# Exposer le port 80
EXPOSE 80

# Commande pour démarrer Nginx
CMD ["nginx", "-g", "daemon off;"]
