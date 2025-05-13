import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';

const RegisterPage = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  
  const [verificationCode, setVerificationCode] = useState('');
  const [isCodeSent, setIsCodeSent] = useState(false);
  const [isEmailValid, setIsEmailValid] = useState(false);

  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const emailDomain = '@mysothemalab.com';

  useEffect(() => {
    if (email.endsWith(emailDomain)) {
      setIsEmailValid(true);
    } else {
      setIsEmailValid(false);
    }
  }, [email]);

  const handleSendCodeSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');
    setLoading(true);

    if (!isEmailValid) {
      setError(`L'adresse e-mail doit se terminer par ${emailDomain}`);
      setLoading(false);
      return;
    }

    const userData = {
      username,
      email,
      password,
      full_name: fullName || undefined,
    };

    try {
      const response = await apiService.post('/auth/register', userData);
      console.log('Registration initiated:', response.data);
      setSuccessMessage(response.data.message || 'Code de vérification envoyé. Veuillez vérifier votre e-mail.');
      setIsCodeSent(true);
    } catch (err) {
      console.error('Send code error:', err.response ? err.response.data : err.message);
      let errorMessage = 'Échec de l\'envoi du code.';
      if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === 'string') {
          errorMessage = err.response.data.detail;
        } else if (Array.isArray(err.response.data.detail)) {
          errorMessage = err.response.data.detail.map(d => `${d.loc.join(' > ')}: ${d.msg}`).join('\n');
        } else {
          errorMessage = JSON.stringify(err.response.data.detail);
        }
      }
      setError(errorMessage);
    }
    setLoading(false);
  };

  const handleVerifyCodeSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');
    setLoading(true);

    try {
      const response = await apiService.post('/auth/verify-email', { email, code: verificationCode });
      console.log('Verification successful:', response.data);
      setSuccessMessage(response.data.message || 'Vérification réussie ! Vous pouvez maintenant vous connecter.');
      alert('Inscription finalisée avec succès ! Vous allez être redirigé vers la page de connexion.');
      navigate('/login');
    } catch (err) {
      console.error('Verification error:', err.response ? err.response.data : err.message);
      let errorMessage = 'Échec de la vérification du code.';
      if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      }
      setError(errorMessage);
    }
    setLoading(false);
  };

  return (
    <div className="max-w-md mx-auto mt-10 bg-surface p-8 rounded-xl shadow-xl">
      <h2 className="text-3xl font-bold text-center text-gray-800 mb-8">
        {isCodeSent ? 'Vérifier votre Email' : 'Créer un compte'}
      </h2>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
          <strong className="font-bold">Erreur !</strong>
          <span className="block sm:inline"> {error.split('\n').map((line, i) => (<React.Fragment key={i}>{line}<br/></React.Fragment>))}</span>
        </div>
      )}
      {successMessage && !error && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative mb-4" role="alert">
          <span className="block sm:inline">{successMessage}</span>
        </div>
      )}

      {!isCodeSent ? (
        <form onSubmit={handleSendCodeSubmit} className="space-y-6">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700">Nom d'utilisateur</label>
            <input id="username" name="username" type="text" required value={username} onChange={(e) => setUsername(e.target.value)}
              className="mt-1 block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
              placeholder="Votre nom d'utilisateur"/>
          </div>
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">Adresse Email Sothema</label>
            <input id="email" name="email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)}
              className={`mt-1 block w-full px-4 py-3 border rounded-lg shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm ${isEmailValid ? 'border-green-500' : 'border-gray-300'}`}
              placeholder={`vous${emailDomain}`}/>
            {!isEmailValid && email.length > 0 && (
              <p className="text-xs text-red-600 mt-1">L'email doit se terminer par {emailDomain}</p>
            )}
          </div>
          <div>
            <label htmlFor="fullName" className="block text-sm font-medium text-gray-700">Nom complet (Optionnel)</label>
            <input id="fullName" name="fullName" type="text" value={fullName} onChange={(e) => setFullName(e.target.value)}
              className="mt-1 block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
              placeholder="Votre nom complet"/>
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">Mot de passe</label>
            <input id="password" name="password" type="password" autoComplete="new-password" required value={password} onChange={(e) => setPassword(e.target.value)}
              className="mt-1 block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
              placeholder="Choisissez un mot de passe sécurisé"/>
          </div>
          <div>
            <button type="submit" disabled={loading || !isEmailValid}
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-primary hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50">
              {loading ? 'Envoi en cours...' : 'Envoyer le code de vérification'}
            </button>
          </div>
        </form>
      ) : (
        <form onSubmit={handleVerifyCodeSubmit} className="space-y-6">
          <div>
            <label htmlFor="verificationCode" className="block text-sm font-medium text-gray-700">Code de vérification</label>
            <input id="verificationCode" name="verificationCode" type="text" required value={verificationCode} onChange={(e) => setVerificationCode(e.target.value)}
              className="mt-1 block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
              placeholder="Entrez le code reçu par e-mail"/>
          </div>
          <div>
            <button type="submit" disabled={loading}
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-primary hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50">
              {loading ? 'Vérification en cours...' : 'Vérifier et Finaliser l\'inscription'}
            </button>
          </div>
        </form>
      )}
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
