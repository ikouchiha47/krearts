/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Noir comic theme - dark, moody, high contrast
        surfaceSoft: '#0a0e1a',        // Deep noir background
        surfaceStrong: '#141824',      // Slightly lighter noir surface
        borderStrong: '#2a3142',       // Muted border for noir aesthetic
        accentSoft: '#4a5568',         // Muted accent
        accentStrong: '#6366f1',       // Bright accent for CTAs
        textMuted: '#9ca3af',          // Muted text
        canvasBg: '#020617',           // Canvas dark background
        canvasInner: '#0f1419',        // Canvas inner area
        canvasCard: '#1a1f2e',         // Card background in canvas
        
        // Additional noir colors
        noirHighlight: '#e5e7eb',      // High contrast text
        noirShadow: '#030712',         // Deep shadows
        noirAccent: '#fbbf24',         // Amber accent (like streetlights)
      },
      boxShadow: {
        cardSoft: '0 4px 6px -1px rgba(0, 0, 0, 0.5), 0 2px 4px -1px rgba(0, 0, 0, 0.3)',
        chip: '0 2px 4px rgba(0, 0, 0, 0.4)',
        noir: '0 10px 25px -5px rgba(0, 0, 0, 0.7), 0 10px 10px -5px rgba(0, 0, 0, 0.4)',
      },
      borderRadius: {
        brutal: '0.25rem',  // Sharper corners for comic aesthetic
      },
      backgroundImage: {
        'noir-gradient': 'linear-gradient(to bottom, #0a0e1a, #020617)',
        'comic-texture': 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.03) 2px, rgba(255,255,255,0.03) 4px)',
      },
    },
  },
  plugins: [],
};
