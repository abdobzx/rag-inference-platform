import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api'; // Assurez-vous que ce chemin est correct

const RegisterPage = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const userData = {
      username,
      email,
      password,
      full_name: fullName || undefined, // N'envoyez que si défini
    };

    try {
      const response = await apiService.post('/auth/register', userData);
      console.log('Registration successful:', response.data);
      alert('Inscription réussie ! Veuillez vous connecter.');
      navigate('/login');
    } catch (err) {
      console.error('Registration error:', err.response ? err.response.data : err.message);
      let errorMessage = 'Échec de l\'inscription.';
      if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === 'string') {
          errorMessage = err.response.data.detail;
        } else if (Array.isArray(err.response.data.detail)) {
          // Pour les erreurs de validation FastAPI
          errorMessage = err.response.data.detail.map(d => `${d.loc.join(' > ')}: ${d.msg}`).join('\n');
        } else {
            errorMessage = JSON.stringify(err.response.data.detail);
        }
      }
      setError(errorMessage);
    }
    setLoading(false);
  };

  return (
    <div className="max-w-md mx-auto mt-10 bg-surface p-8 rounded-xl shadow-xl">
      <h2 className="text-3xl font-bold text-center text-gray-800 mb-8">Créer un compte</h2>
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
          <strong className="font-bold">Erreur !</strong>
          <span className="block sm:inline"> {error.split('\n').map((line, i) => (<React.Fragment key={i}>{line}<br/></React.Fragment>))}</span>
        </div>
      )}
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="username" className="block text-sm font-medium text-gray-700">
            Nom d'utilisateur
          </label>
          <input
            id="username"
            name="username"
            type="text"
            required
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="mt-1 block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
            placeholder="Votre nom d'utilisateur"
          />
        </div>

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
          <label htmlFor="fullName" className="block text-sm font-medium text-gray-700">
            Nom complet (Optionnel)
          </label>
          <input
            id="fullName"
            name="fullName"
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className="mt-1 block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
            placeholder="Votre nom complet"
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
            autoComplete="new-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
            placeholder="Choisissez un mot de passe sécurisé"
          />
        </div>

        <div>
          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-primary hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50"
          >
            {loading ? 'Inscription en cours...' : 'S\'inscrire'}
          </button>
        </div>
      </form>
      <p className="mt-6 text-center text-sm text-gray-600">
        Déjà un compte?{' '}
        <a href="/login" className="font-medium text-primary hover:text-blue-700">
          Connectez-vous
        </a>
      </p>
    </div>
  );
};

export default RegisterPage;
