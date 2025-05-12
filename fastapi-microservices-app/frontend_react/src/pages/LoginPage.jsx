import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api'; // Assurez-vous que ce chemin est correct

const LoginPage = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Le formulaire OAuth2PasswordRequestForm attend les données en `application/x-www-form-urlencoded`
      const formData = new URLSearchParams();
      formData.append('username', email); // FastAPI OAuth2PasswordRequestForm s'attend à `username` pour l'email/identifiant
      formData.append('password', password);

      const response = await apiService.post('/token', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      
      console.log('Login successful:', response.data);
      // Stocker le token (par exemple, dans localStorage) et rediriger
      localStorage.setItem('accessToken', response.data.access_token);
      // Rediriger vers une page protégée, par exemple un tableau de bord
      navigate('/'); // Pour l'instant, retour à l'accueil
      alert('Connexion réussie!'); // Ou une notification plus élégante

    } catch (err) {
      console.error('Login error:', err.response ? err.response.data : err.message);
      setError(err.response?.data?.detail || 'Échec de la connexion. Veuillez vérifier vos identifiants.');
    }
    setLoading(false);
  };

  return (
    <div className="max-w-md mx-auto mt-10 bg-surface p-8 rounded-xl shadow-xl">
      <h2 className="text-3xl font-bold text-center text-gray-800 mb-8">Connexion</h2>
      {error && <p className="text-red-500 text-center mb-4">{error}</p>}
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700">
            Adresse Email
          </label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
            placeholder="vous@exemple.com"
          />
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-medium text-gray-700">
            Mot de passe
          </label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
            placeholder="Votre mot de passe"
          />
        </div>

        <div>
          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-primary hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50"
          >
            {loading ? 'Connexion en cours...' : 'Se connecter'}
          </button>
        </div>
      </form>
      <p className="mt-6 text-center text-sm text-gray-600">
        Pas encore de compte?{' '}
        <a href="/register" className="font-medium text-primary hover:text-blue-700">
          Inscrivez-vous
        </a>
      </p>
    </div>
  );
};

export default LoginPage;
