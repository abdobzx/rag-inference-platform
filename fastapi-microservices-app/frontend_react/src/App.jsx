import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ApiDocsPage from './pages/ApiDocsPage';

function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-grow container mx-auto px-4 py-8">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/api-docs" element={<ApiDocsPage />} />
        </Routes>
      </main>
      <footer className="bg-gray-800 text-white text-center p-4">
        <p>&copy; 2025 SothemaAI. Tous droits réservés.</p>
      </footer>
    </div>
  );
}

export default App;
