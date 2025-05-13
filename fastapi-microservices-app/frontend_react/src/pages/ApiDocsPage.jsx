import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api'; // Assurez-vous que api.js est configuré pour le gateway

const ApiDocsPage = () => {
  const [docs, setDocs] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const accessToken = localStorage.getItem('accessToken');
    if (!accessToken) {
      navigate('/login'); // Rediriger si non connecté
      return;
    }

    const fetchDocs = async () => {
      setLoading(true);
      try {
        // Cet endpoint sera créé dans le gateway et proxy vers auth_service "/"
        const response = await apiService.get('/auth/info', {
          headers: {
            'Authorization': `Bearer ${accessToken}`, // Bonne pratique, même si la cible est publique
          },
        });
        setDocs(response.data);
        setError('');
      } catch (err) {
        console.error('Failed to load API documentation:', err);
        setError('Impossible de charger la documentation API. Veuillez réessayer plus tard.');
        if (err.response?.status === 401 || err.response?.status === 403) {
            // Gérer le cas où le token est invalide ou expiré
            localStorage.removeItem('accessToken');
            navigate('/login');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchDocs();
  }, [navigate]);

  if (loading) {
    return (
      <div className="container mx-auto p-4 text-center">
        <p>Chargement de la documentation...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-4 text-center text-red-500">
        <p>{error}</p>
      </div>
    );
  }

  if (!docs) {
    return (
      <div className="container mx-auto p-4 text-center">
        <p>Aucune documentation disponible.</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 bg-white shadow-lg rounded-lg mt-5">
      <h1 className="text-3xl font-bold mb-6 text-gray-800 border-b pb-2">{docs.message || "Documentation du Service d'Authentification"}</h1>
      
      <section className="mb-6">
        <h2 className="text-2xl font-semibold text-gray-700 mb-3">Description</h2>
        <p className="text-gray-600 leading-relaxed">{docs.description}</p>
      </section>

      {docs.routes_summary && (
        <section className="mb-6">
          <h2 className="text-2xl font-semibold text-gray-700 mb-3">Résumé des Routes</h2>
          <div className="space-y-2">
            {Object.entries(docs.routes_summary).map(([route, desc]) => (
              <div key={route} className="p-3 bg-gray-50 rounded-md">
                <p className="font-mono text-sm text-blue-600">{route}</p>
                <p className="text-gray-600 text-sm">{desc}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {docs.notes_on_ai_models && (
        <section className="mb-6">
          <h2 className="text-2xl font-semibold text-gray-700 mb-3">Notes sur les Modèles d'IA</h2>
          <p className="text-gray-600 leading-relaxed bg-blue-50 p-3 rounded-md">{docs.notes_on_ai_models}</p>
        </section>
      )}

      {docs.related_services && docs.related_services.inference_service && (
         <section>
            <h2 className="text-2xl font-semibold text-gray-700 mb-3">Services Connexes</h2>
            <div className="bg-green-50 p-3 rounded-md">
                <h3 className="font-semibold text-green-700">Service d'Inférence</h3>
                <p className="text-gray-600 leading-relaxed">{docs.related_services.inference_service}</p>
            </div>
        </section>
      )}
    </div>
  );
};

export default ApiDocsPage;
