/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#1D4ED8', // Bleu foncé
        secondary: '#1F2937', // Gris foncé (pour le texte)
        accent: '#F59E0B',    // Ambre (pour les accents)
        background: '#F3F4F6', // Gris clair (pour le fond)
        surface: '#FFFFFF', // Blanc (pour les cartes, etc.)
      },
    },
  },
  plugins: [],
}