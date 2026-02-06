import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        shell: '#0f1720',
        panel: '#182634',
        ink: '#f7fafc',
        accent: '#f2a23a',
        mint: '#4bc0b0',
      },
      boxShadow: {
        glow: '0 20px 80px rgba(75, 192, 176, 0.18)',
      },
    },
  },
  plugins: [],
};

export default config;
