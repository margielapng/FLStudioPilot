/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{ts,tsx}', './index.html'],
  theme: {
    extend: {
      colors: {
        surface: {
          900: '#0d0d0f',
          800: '#141417',
          700: '#1c1c21',
          600: '#25252c',
        },
        accent: {
          DEFAULT: '#7c5cfc',
          hover: '#9b82fd',
        },
        fl: {
          orange: '#ff6b00',
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      }
    }
  },
  plugins: []
}
