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
        // Deal score color ramp
        score: {
          low:    "#ef4444",  // 1–3
          fair:   "#f59e0b",  // 4–6
          good:   "#22c55e",  // 7–8
          great:  "#10b981",  // 9–10
        },
      },
    },
  },
  plugins: [],
};

export default config;
