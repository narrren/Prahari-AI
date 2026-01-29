/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'prahari-dark': '#0f172a',
        'prahari-card': '#1e293b',
        'prahari-accent': '#3b82f6',
        'prahari-danger': '#ef4444',
      }
    },
  },
  plugins: [],
}
