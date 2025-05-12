import axios from 'axios';

// Crée une instance Axios avec une URL de base pour vos appels API.
// Le proxy dans vite.config.js gérera la redirection vers le bon backend en développement.
// En production, Nginx gérera cela.
const apiClient = axios.create({
  baseURL: '/api', // Ce préfixe sera utilisé par le proxy Vite
  headers: {
    'Content-Type': 'application/json',
  },
});

// Vous pouvez ajouter des intercepteurs ici si nécessaire, par exemple pour ajouter
// automatiquement le token JWT aux requêtes authentifiées.
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default {
  get(resource, params) {
    return apiClient.get(resource, { params });
  },
  post(resource, data, config) {
    return apiClient.post(resource, data, config);
  },
  put(resource, data) {
    return apiClient.put(resource, data);
  },
  delete(resource) {
    return apiClient.delete(resource);
  },
  // Vous pouvez ajouter d'autres méthodes HTTP utiles ici (patch, etc.)
};
