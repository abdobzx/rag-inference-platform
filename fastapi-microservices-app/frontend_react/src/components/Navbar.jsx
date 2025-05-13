import React from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';

const Navbar = () => {
  const navigate = useNavigate();
  const accessToken = localStorage.getItem('accessToken');

  const handleLogout = () => {
    localStorage.removeItem('accessToken');
    navigate('/login');
    window.location.reload();
  };

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
            {accessToken ? (
              <>
                <NavLink
                  to="/api-docs"
                  className={({ isActive }) =>
                    `text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium ${isActive ? 'text-white bg-primary' : ''}`
                  }
                >
                  Documentation API
                </NavLink>
                <button
                  onClick={handleLogout}
                  className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium"
                >
                  Déconnexion
                </button>
              </>
            ) : (
              <>
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
              </>
            )}
            {/* Plus de liens ici si l'utilisateur est connecté, par exemple un lien de déconnexion ou vers un tableau de bord */}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
