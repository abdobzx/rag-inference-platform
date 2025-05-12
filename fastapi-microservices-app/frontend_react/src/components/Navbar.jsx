import React from 'react';
import { Link, NavLink } from 'react-router-dom';

const Navbar = () => {
  return (
    <nav className="bg-gray-800 shadow-lg">
      <div className="container mx-auto px-6 py-3">
        <div className="flex items-center justify-between">
          <div>
            <Link to="/" className="text-white text-2xl font-bold hover:text-primary">
              SothemaAI
            </Link>
          </div>
          <div className="flex items-center">
            <NavLink 
              to="/" 
              className={({ isActive }) => 
                `text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium ${isActive ? 'text-white bg-primary' : ''}`
              }
            >
              Accueil
            </NavLink>
            <NavLink 
              to="/login" 
              className={({ isActive }) => 
                `text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium ${isActive ? 'text-white bg-primary' : ''}`
              }
            >
              Connexion
            </NavLink>
            <NavLink 
              to="/register" 
              className={({ isActive }) => 
                `text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium ${isActive ? 'text-white bg-primary' : ''}`
              }
            >
              Inscription
            </NavLink>
            {/* Plus de liens ici si l'utilisateur est connecté, par exemple un lien de déconnexion ou vers un tableau de bord */}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
