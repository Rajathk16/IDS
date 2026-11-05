import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        cyber: {
          bg: "#070a13",
          surface: "#0b1120",
          card: "#0f172a",
          border: "#1e293b",
          highlight: "#334155",
        },
        neon: {
          cyan: "#00f0ff",
          green: "#10b981",
          red: "#ef4444",
          amber: "#f59e0b",
          purple: "#a855f7",
          magenta: "#ec4899",
        },
      },
      fontFamily: {
        mono: ['"SF Mono"', "Menlo", "Monaco", "Consolas", '"Liberation Mono"', '"Courier New"', "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;

