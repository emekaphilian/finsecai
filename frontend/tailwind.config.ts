import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#0F172A",
        secondary: "#1E293B",
        gold: "#F59E0B",
        "text-primary": "#F1F5F9",
        "text-secondary": "#CBD5E1",
        border: "#334155",
        danger: "#EF4444",
        success: "#22C55E",
        warning: "#F59E0B",
        info: "#60A5FA",
      },
      fontFamily: {
        sans: ["-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
