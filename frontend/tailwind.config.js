/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: 'rgb(15 28 46 / <alpha-value>)',
        slate: {
          panel: 'rgb(21 34 56 / <alpha-value>)',
        },
        accent: {
          DEFAULT: 'rgb(26 122 109 / <alpha-value>)',
          soft: 'rgb(215 239 233 / <alpha-value>)',
          bright: 'rgb(42 168 151 / <alpha-value>)',
        },
        warn: 'rgb(196 122 26 / <alpha-value>)',
        danger: 'rgb(179 58 58 / <alpha-value>)',
        safe: 'rgb(45 122 70 / <alpha-value>)',
        paper: 'rgb(243 240 232 / <alpha-value>)',
        mist: 'rgb(232 238 244 / <alpha-value>)',
      },
      fontFamily: {
        display: ['"Fraunces"', 'Georgia', 'serif'],
        sans: ['"Source Sans 3"', 'Segoe UI', 'sans-serif'],
      },
      boxShadow: {
        soft: '0 12px 40px rgba(15, 28, 46, 0.12)',
      },
      opacity: {
        15: '0.15',
        45: '0.45',
        55: '0.55',
      },
    },
  },
  plugins: [],
}
