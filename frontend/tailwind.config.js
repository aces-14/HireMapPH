/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        cream:  { DEFAULT: "#FAFAF8", dark: "#F5F0E8" },
        border: "#E0D9CC",
        muted:  "#78716C",
        ink:    "#2C2416",
        amber:  { DEFAULT: "#D97706", light: "#FDE68A", pale: "#FEF3C7" },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        display: ["'Instrument Serif'", "Georgia", "serif"],
      },
    },
  },
  plugins: [],
}

