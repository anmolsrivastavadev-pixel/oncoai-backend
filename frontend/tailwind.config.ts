import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#050B1A',
          900: '#0A1630',
          850: '#0D1C3B',
          800: '#112449',
          700: '#1A3260',
        },
        accent: {
          cyan: '#22D3EE',
          teal: '#2DD4BF',
          sky: '#38BDF8',
        },
        concern: {
          low: '#34D399',
          moderate: '#FBBF24',
          higher: '#FB7185',
        },
        ink: {
          DEFAULT: '#E6EEF9',
          muted: '#A9B8D0',
          faint: '#8495B2',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['"Space Grotesk"', 'Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(34,211,238,0.25), 0 8px 32px -8px rgba(34,211,238,0.45)',
        'glow-sm': '0 0 16px -4px rgba(34,211,238,0.55)',
        'glow-teal': '0 8px 32px -8px rgba(45,212,191,0.5)',
        glass: '0 8px 32px -12px rgba(0,0,0,0.6)',
      },
      backgroundImage: {
        'navy-radial': 'radial-gradient(1200px 600px at 10% -10%, rgba(34,211,238,0.10), transparent 60%), radial-gradient(900px 500px at 110% 10%, rgba(45,212,191,0.08), transparent 60%), linear-gradient(180deg, #050B1A 0%, #0A1630 100%)',
        'accent-gradient': 'linear-gradient(135deg, #22D3EE 0%, #2DD4BF 100%)',
      },
      keyframes: {
        'scan-line': {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
        'pulse-ring': {
          '0%': { transform: 'scale(0.9)', opacity: '0.7' },
          '100%': { transform: 'scale(1.35)', opacity: '0' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-400px 0' },
          '100%': { backgroundPosition: '400px 0' },
        },
        float: {
          '0%,100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-6px)' },
        },
      },
      animation: {
        'scan-line': 'scan-line 2.4s ease-in-out infinite alternate',
        'pulse-ring': 'pulse-ring 2.2s ease-out infinite',
        shimmer: 'shimmer 1.6s linear infinite',
        float: 'float 5s ease-in-out infinite',
      },
      spacing: {
        'safe-t': 'env(safe-area-inset-top)',
        'safe-b': 'env(safe-area-inset-bottom)',
      },
    },
  },
  plugins: [],
} satisfies Config;
