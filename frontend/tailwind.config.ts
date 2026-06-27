import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#172033",
        panel: "#f7f9fc",
        line: "#d9e2ef",
        signal: "#1f7a8c",
        accent: "#c75c2f"
      }
    }
  },
  plugins: []
};

export default config;

