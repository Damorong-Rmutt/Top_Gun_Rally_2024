/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./*.{html,js}"],
  theme: {
    extend: {
      colors: {
        reddd: {
          50: "#ffeff0",
          100: "#ffdfe0",
          200: "#ffbfc1",
          300: "#ff9ea2",
          400: "#ff7e83",
          500: "#ff5e64",
          600: "#cc4b50",
          700: "#99383c",
          800: "#662628",
          900: "#331314",
        },
      },
    },
  },
  plugins: [],
};
