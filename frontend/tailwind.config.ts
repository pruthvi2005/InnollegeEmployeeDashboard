import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: {
        '2xl': '1400px',
      },
    },
    extend: {
      colors: {
        primary: {
          DEFAULT: '#1053B6',
          foreground: '#ffffff',
          50: '#eff7ff',
          100: '#dbeeff',
          200: '#b9dfff',
          300: '#86c7ff',
          400: '#4ca8ff',
          500: '#0675E5',
          600: '#1053B6',
          700: '#0A377B',
          800: '#061B43',
          900: '#04132f',
          950: '#02091a',
        },
        navy: {
          DEFAULT: '#061B43',
          light: '#0A377B',
          dark: '#061B43',
          rich: '#0A377B',
        },
        accent: {
          DEFAULT: '#0675E5',
          foreground: '#ffffff',
          hover: '#008FFF',
        },
        surface: {
          DEFAULT: '#f8fafc',
          muted: '#f1f5f9',
          hover: '#e2e8f0',
        },
        card: {
          DEFAULT: '#ffffff',
          foreground: '#0f172a',
        },
        sidebar: {
          DEFAULT: '#061B43',
          text: '#dbeeff',
          active: '#008FFF',
          hover: 'rgba(255, 255, 255, 0.1)',
        },
        border: '#dbeaff',
        input: '#dbeaff',
        ring: '#0675E5',
        background: '#f7fbff',
        foreground: '#061B43',
        muted: {
          DEFAULT: '#64748b',
          foreground: '#94a3b8',
        },
        success: {
          DEFAULT: '#16a34a',
          foreground: '#ffffff',
          bg: '#f0fdf4',
        },
        warning: {
          DEFAULT: '#d97706',
          foreground: '#ffffff',
          bg: '#fffbeb',
        },
        danger: {
          DEFAULT: '#dc2626',
          foreground: '#ffffff',
          bg: '#fef2f2',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      keyframes: {
        fadeIn: {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        slideInLeft: {
          from: { transform: 'translateX(-100%)' },
          to: { transform: 'translateX(0)' },
        },
      },
      animation: {
        fadeIn: 'fadeIn 0.25s ease-out forwards',
        slideInLeft: 'slideInLeft 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards',
      },
    },
  },
  plugins: [],
};

export default config;
