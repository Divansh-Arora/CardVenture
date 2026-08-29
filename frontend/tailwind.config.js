/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        cream: {
          DEFAULT: "#FFF9EE",
          100: "#FFFDF8",
          200: "#FFF3DC",
        },
        ink: {
          900: "#2E2A4A", // used for body text, not backgrounds
          700: "#4A4468",
        },
        bubblegum: {
          DEFAULT: "#FF6FA5",
          soft: "#FFA6C9",
          dim: "#FFE3EE",
        },
        sunshine: {
          DEFAULT: "#FFC93C",
          soft: "#FFDD7A",
          dim: "#FFF3D2",
        },
        sky: {
          DEFAULT: "#3EC6E0",
          soft: "#8FE0F0",
          dim: "#DEF7FC",
        },
        grass: {
          DEFAULT: "#5FD36B",
          soft: "#A2E8A8",
          dim: "#E5F9E6",
        },
        grape: {
          DEFAULT: "#9B6BFF",
          soft: "#C4A9FF",
          dim: "#EFE5FF",
        },
        tangerine: {
          DEFAULT: "#FF8A3D",
          soft: "#FFB37A",
          dim: "#FFEADA",
        },
      },
      fontFamily: {
        display: ["'Baloo 2'", "cursive"],
        body: ["'Nunito'", "sans-serif"],
      },
      borderRadius: {
        "4xl": "1.75rem",
        "5xl": "2.25rem",
      },
      boxShadow: {
        pop: "0 6px 0 0 rgba(46,42,74,0.12)",
        "pop-sm": "0 4px 0 0 rgba(46,42,74,0.12)",
        "pop-lg": "0 9px 0 0 rgba(46,42,74,0.12)",
        card: "0 14px 30px -12px rgba(46,42,74,0.25)",
        glow: "0 0 0 6px rgba(255,201,60,0.25)",
      },
      backgroundImage: {
        sky: "linear-gradient(180deg, #DEF7FC 0%, #FFF9EE 45%, #FFF3D2 100%)",
        confetti:
          "radial-gradient(circle at 20% 20%, rgba(255,111,165,0.18) 0, transparent 40%), radial-gradient(circle at 80% 30%, rgba(62,198,224,0.18) 0, transparent 40%), radial-gradient(circle at 50% 80%, rgba(255,201,60,0.18) 0, transparent 40%)",
      },
      keyframes: {
        bob: {
          "0%, 100%": { transform: "translateY(0px) rotate(-1deg)" },
          "50%": { transform: "translateY(-8px) rotate(1deg)" },
        },
        pop: {
          "0%": { transform: "scale(0.9)", opacity: 0 },
          "60%": { transform: "scale(1.04)", opacity: 1 },
          "100%": { transform: "scale(1)" },
        },
        wiggle: {
          "0%, 100%": { transform: "rotate(-2deg)" },
          "50%": { transform: "rotate(2deg)" },
        },
        twinkle: {
          "0%, 100%": { opacity: 0.4, transform: "scale(0.9)" },
          "50%": { opacity: 1, transform: "scale(1.15)" },
        },
        floatUp: {
          "0%": { transform: "translateY(10px)", opacity: 0 },
          "100%": { transform: "translateY(0)", opacity: 1 },
        },
      },
      animation: {
        bob: "bob 3.2s ease-in-out infinite",
        pop: "pop 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) both",
        wiggle: "wiggle 0.6s ease-in-out infinite",
        twinkle: "twinkle 1.8s ease-in-out infinite",
        floatUp: "floatUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) both",
      },
    },
  },
  plugins: [],
};
