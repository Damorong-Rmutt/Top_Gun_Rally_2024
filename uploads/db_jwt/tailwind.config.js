module.exports = {
  content: [
    "./templates/**/*.html", // Scans all HTML files in the templates folder
    "./static/**/*.js", // Scans JS files in the static folder
  ],
  theme: {
    extend: {
      colors: {
        crayola: {
          50: "#feeff1",
          100: "#fce0e4",
          200: "#fac1c9",
          300: "#f7a1ad",
          400: "#f58292",
          500: "#f26377",
          600: "#c24f5f",
          700: "#913b47",
          800: "#612830",
          900: "#301418",
        },
      },
    },
  },
  plugins: [],
};
