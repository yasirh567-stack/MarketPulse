/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bullish: {
          DEFAULT: "#0f9d58",
          light: "#e6f4ea",
        },
        bearish: {
          DEFAULT: "#c5221f",
          light: "#fce8e6",
        },
        neutral: {
          DEFAULT: "#5f6368",
          light: "#f1f3f4",
        },
        surface: {
          DEFAULT: "#ffffff",
          dark: "#111318",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
