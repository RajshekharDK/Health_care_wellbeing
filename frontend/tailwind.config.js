export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#14b8a6", // teal-500 base
        primaryDark: "#0f766e",
        glassLight: "rgba(255,255,255,0.6)",
        glassDark: "rgba(31,41,55,0.6)",
      },
      backdropBlur: {
        xs: "2px",
      },
      boxShadow: {
        soft: "0 8px 24px rgba(0,0,0,0.05)",
        glass: "0 4px 20px rgba(0,0,0,0.08)",
      },
      borderRadius: {
        xl2: "1.25rem",
        xl3: "1.75rem",
      },
    },
  },
  plugins: [],
};