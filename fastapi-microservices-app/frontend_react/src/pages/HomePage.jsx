import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';

const HomePage = () => {
  const navigate = useNavigate();
  const [apiKeys, setApiKeys] = useState([]);
  const [newApiKey, setNewApiKey] = useState(null); // Pour stocker la clé complète temporairement
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');
  const [loadingKeys, setLoadingKeys] = useState(false);
  const [loadingGenerate, setLoadingGenerate] = useState(false);
  const [showKeyModal, setShowKeyModal] = useState(false);

  const isLoggedIn = !!localStorage.getItem('accessToken');

  const fetchApiKeys = useCallback(async () => {
    if (!isLoggedIn) return;
    setLoadingKeys(true);
    setError('');
    try {
      const response = await apiService.get('/auth/apikeys');
      setApiKeys(response.data || []);
    } catch (err) {
      console.error('Error fetching API keys:', err.response ? err.response.data : err.message);
      setError(err.response?.data?.detail || 'Erreur lors de la récupération des clés API.');
      if (err.response?.status === 401) {
        localStorage.removeItem('accessToken');
        navigate('/login');
      }
    }
    setLoadingKeys(false);
  }, [isLoggedIn, navigate]);

  useEffect(() => {
    if (isLoggedIn) {
      fetchApiKeys();
    }
  }, [isLoggedIn, fetchApiKeys]);

  const handleGenerateKey = async (e) => {
    e.preventDefault();
    if (!description.trim()) {
      setError('La description est requise pour créer une clé API.');
      return;
    }
    setLoadingGenerate(true);
    setError('');
    setNewApiKey(null);
    try {
      const response = await apiService.post('/auth/apikeys', { description });
      setNewApiKey(response.data.full_key); // Supposons que le backend retourne `full_key`
      setDescription(''); // Réinitialiser la description
      fetchApiKeys(); // Recharger la liste des clés
      setShowKeyModal(true); // Afficher le modal avec la nouvelle clé
    } catch (err) {
      console.error('Error generating API key:', err.response ? err.response.data : err.message);
      setError(err.response?.data?.detail || 'Erreur lors de la génération de la clé API.');
    }
    setLoadingGenerate(false);
  };

  const handleRevokeKey = async (keyPrefix) => {
    if (!window.confirm(`Êtes-vous sûr de vouloir révoquer la clé commençant par ${keyPrefix} ?`)) {
      return;
    }
    setError('');
    try {
      await apiService.delete(`/auth/apikeys/${keyPrefix}`);
      fetchApiKeys(); // Recharger la liste des clés
    } catch (err) {
      console.error('Error revoking API key:', err.response ? err.response.data : err.message);
      setError(err.response?.data?.detail || 'Erreur lors de la révocation de la clé API.');
    }
  };

  if (!isLoggedIn) {
    return (
      <div className="text-center py-10 bg-background min-h-screen flex flex-col justify-center items-center">
        <div className="max-w-2xl p-8">
          <h1 className="text-5xl font-bold text-text mb-6">
            Bienvenue sur la Plateforme LLM de SothemaAI
          </h1>
          <p className="text-xl text-secondary mb-8">
            Accédez à des modèles de langage open-source puissants via notre interface sécurisée et intuitive.
          </p>
          <div className="space-x-4">
            <a
              href="/register"
              className="bg-primary text-white font-semibold px-8 py-3 rounded-lg shadow-md hover:bg-blue-700 transition duration-300"
            >
              Commencer
            </a>
            <a
              href="/login"
              className="bg-gray-200 text-gray-800 font-semibold px-8 py-3 rounded-lg shadow-md hover:bg-gray-300 transition duration-300"
            >
              Se connecter
            </a>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-4xl font-bold text-text text-center mb-10">Gestion des Clés API</h1>

        {error && <p className="text-red-500 text-center mb-4 bg-red-100 p-3 rounded-md">{error}</p>}

        {showKeyModal && newApiKey && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-surface p-6 rounded-lg shadow-xl max-w-md w-full">
              <h3 className="text-2xl font-semibold text-text mb-4">Nouvelle Clé API Générée</h3>
              <p className="text-secondary mb-2">Veuillez copier cette clé. Elle ne sera plus affichée.</p>
              <div className="bg-gray-100 p-3 rounded-md mb-4 break-all">
                <code className="text-sm text-gray-700">{newApiKey}</code>
              </div>
              <button
                onClick={() => {
                  setShowKeyModal(false);
                  setNewApiKey(null); // Effacer la clé après la fermeture du modal
                }}
                className="w-full bg-primary text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition duration-300"
              >
                Fermer
              </button>
            </div>
          </div>
        )}

        <div className="bg-surface p-8 rounded-xl shadow-xl mb-10">
          <h2 className="text-2xl font-semibold text-text mb-6">Générer une Nouvelle Clé API</h2>
          <form onSubmit={handleGenerateKey} className="space-y-4">
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                Description de la clé
              </label>
              <input
                id="description"
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                required
                className="mt-1 block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
                placeholder="Ex: Clé pour projet Alpha"
              />
            </div>
            <button
              type="submit"
              disabled={loadingGenerate}
              className="w-full bg-primary text-white font-semibold py-3 px-4 rounded-lg shadow-md hover:bg-blue-700 transition duration-300 disabled:opacity-50"
            >
              {loadingGenerate ? 'Génération en cours...' : 'Générer la clé'}
            </button>
          </form>
        </div>

        <div className="bg-surface p-8 rounded-xl shadow-xl">
          <h2 className="text-2xl font-semibold text-text mb-6">Vos Clés API</h2>
          {loadingKeys ? (
            <p className="text-center text-secondary">Chargement des clés...</p>
          ) : apiKeys.length === 0 ? (
            <p className="text-center text-secondary">Vous n'avez aucune clé API pour le moment.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Préfixe
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Description
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Créée le
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {apiKeys.map((key) => (
                    <tr key={key.key_prefix}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{key.key_prefix}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{key.description}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(key.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => handleRevokeKey(key.key_prefix)}
                          className="text-red-600 hover:text-red-800 transition duration-150"
                        >
                          Révoquer
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HomePage;
