import React from 'react';

const HomePage = () => {
  return (
    <div className="text-center py-10">
      <h1 className="text-5xl font-bold text-gray-800 mb-6">
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
      {/* Vous pouvez ajouter plus de contenu ici, comme des fonctionnalités clés, des témoignages, etc. */}
    </div>
  );
};

export default HomePage;
