/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#374151',
          800: '#1f2937',
          900: '#111827',
          950: '#030712',
        },
        pastel: {
          blue: '#a5b4fc',
          indigo: '#c7d2fe',
          purple: '#d8b4fe',
          pink: '#f9a8d4',
          rose: '#fda4af',
          orange: '#fdba74',
          yellow: '#fcd34d',
          green: '#86efac',
          teal: '#5eead4',
          cyan: '#67e8f9',
          lavender: '#e9d5ff',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['Fira Code', 'monospace'],
      },
      boxShadow: {
        'glow-blue': '0 0 30px rgba(165, 180, 252, 0.4)',
        'glow-purple': '0 0 30px rgba(216, 180, 254, 0.4)',
        'glow-pink': '0 0 30px rgba(249, 168, 212, 0.4)',
        'glow-green': '0 0 30px rgba(134, 239, 172, 0.4)',
        'glow-teal': '0 0 30px rgba(94, 234, 212, 0.4)',
        sm: '0 1px 2px 0 rgba(0, 0, 0, 0.3)',
        md: '0 4px 12px 0 rgba(0, 0, 0, 0.4)',
        lg: '0 10px 25px 0 rgba(0, 0, 0, 0.5)',
      },
      borderRadius: {
        lg: '0.5rem',
        xl: '0.75rem',
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
      backgroundImage: {
        'gradient-pastel': 'linear-gradient(135deg, #a5b4fc 0%, #d8b4fe 50%, #f9a8d4 100%)',
        'gradient-soft': 'linear-gradient(135deg, #67e8f9 0%, #86efac 100%)',
        'gradient-dark': 'linear-gradient(135deg, #1f2937 0%, #111827 100%)',
        'gradient-card': 'linear-gradient(135deg, rgba(36, 43, 61, 0.8) 0%, rgba(45, 53, 72, 0.7) 100%)',
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 3s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite',
        'slide-in': 'slide-in 0.3s ease-out',
        'fade-in': 'fade-in 0.3s ease-out',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { boxShadow: '0 0 20px rgba(165, 180, 252, 0.3)' },
          '50%': { boxShadow: '0 0 40px rgba(165, 180, 252, 0.6)' },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-8px)' },
        },
        'glow': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
        'slide-in': {
          '0%': { transform: 'translateX(-100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
