import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api'; // Assurez-vous que ce chemin est correct

const LoginPage = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState(''); // Ajout de l'état pour le message de succès
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMessage(''); // Réinitialiser le message de succès
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
      setSuccessMessage('Connexion réussie ! Vous allez être redirigé...'); // Définir le message de succès
      
      setTimeout(() => {
        navigate('/'); 
      }, 1500); // Rediriger après 1.5 secondes

    } catch (err) {
      console.error('Login error:', err.response ? err.response.data : err.message);
      setError(err.response?.data?.detail || 'Échec de la connexion. Veuillez vérifier vos identifiants.');
    }
    setLoading(false);
  };

  return (
    <div className="max-w-md mx-auto mt-10 bg-surface p-8 rounded-xl shadow-xl">
      <h2 className="text-3xl font-bold text-center text-gray-800 mb-8">Connexion</h2>
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
          <strong className="font-bold">Erreur !</strong>
          <span className="block sm:inline"> {error}</span>
        </div>
      )}
      {successMessage && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative mb-4" role="alert">
          <span className="block sm:inline">{successMessage}</span>
        </div>
      )}
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
