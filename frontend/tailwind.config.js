/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
        display: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
        mono: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
      },
      colors: {
        // Violet-tinted dark surfaces
        surface: {
          base:    '#08080f',
          DEFAULT: '#0f0f1a',
          raised:  '#16162a',
          hover:   '#1c1c35',
        },
        border: {
          DEFAULT: '#1e1e38',
          light:   '#2a2a50',
        },
      },
    },
  },
  plugins: [],
}
