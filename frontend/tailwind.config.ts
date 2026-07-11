import type { Config } from "tailwindcss";
import typography from "@tailwindcss/typography";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#000000",
        surface: "#0A0A0A",
        card: "#0F0F0F",
        line: "rgba(255,255,255,0.08)",
        lineStrong: "rgba(255,255,255,0.16)",
        accent: "#8B5CF6",
        accentDim: "rgba(139,92,246,0.16)",
        textPrimary: "#FFFFFF",
        textSecondary: "#A3A3A3",
        textMuted: "#525252",
      },
      fontFamily: {
        display: ['"Syne"', "system-ui", "sans-serif"],
        sans: ['"DM Sans"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
      letterSpacing: {
        tight2: "-0.04em",
        tight3: "-0.06em",
      },
      borderRadius: {
        none: "0",
        sm: "2px",
        DEFAULT: "0",
      },
    },
  },
  plugins: [typography],
} satisfies Config;
