import type { Config } from "tailwindcss";
import typography from "@tailwindcss/typography";

/**
 * Colors are sourced from CSS variables defined in `src/index.css`.
 * Solid colors use `rgb(var(--x) / <alpha-value>)` so Tailwind opacity
 * modifiers (e.g. `bg-accent/10`, `text-textPrimary/40`) keep working.
 * Composite tokens (lines, dim fills) carry their own alpha via `var(--x)`.
 */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "rgb(var(--paper) / <alpha-value>)",
        surface: "rgb(var(--surface) / <alpha-value>)",
        card: "rgb(var(--card) / <alpha-value>)",
        // Kept as literal rgba (not var) so Tailwind alpha modifiers like
        // `border-line/50` still resolve. Mirrors --line / --line-strong.
        line: "rgba(32, 30, 25, 0.12)",
        lineStrong: "rgba(32, 30, 25, 0.28)",
        accent: "rgb(var(--accent) / <alpha-value>)",
        accentDeep: "rgb(var(--accent-deep) / <alpha-value>)",
        accentDim: "var(--accent-dim)",
        accent2: "rgb(var(--accent2) / <alpha-value>)",
        accent2Dim: "var(--accent2-dim)",
        textPrimary: "rgb(var(--ink) / <alpha-value>)",
        textSecondary: "rgb(var(--text-secondary) / <alpha-value>)",
        textMuted: "rgb(var(--text-muted) / <alpha-value>)",
        ok: "rgb(var(--ok) / <alpha-value>)",
        warn: "rgb(var(--warn) / <alpha-value>)",
        error: "rgb(var(--error) / <alpha-value>)",
        local: "rgb(var(--local) / <alpha-value>)",
      },
      fontFamily: {
        display: ['"Bricolage Grotesque"', "system-ui", "sans-serif"],
        sans: ['"Instrument Sans"', "system-ui", "sans-serif"],
        serif: ['"Source Serif 4"', "Georgia", "serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
      letterSpacing: {
        tight2: "-0.03em",
        tight3: "-0.05em",
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
