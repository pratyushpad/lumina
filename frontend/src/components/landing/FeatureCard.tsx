import { motion, useReducedMotion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { duration, ease } from "@/lib/motion";
import { CountUp } from "./CountUp";

export interface FeatureMetric {
  value: number;
  prefix?: string;
  suffix?: string;
  label: string;
}

interface FeatureCardProps {
  n: string;
  icon: LucideIcon;
  title: string;
  desc: string;
  metrics?: FeatureMetric[];
  tone?: "accent" | "accent2";
  span?: string;
  border?: boolean;
  delay?: number;
}

/**
 * Feature card with a hand-built "hard shadow" hover: a solid ink-colored
 * plate sits behind the card at a fixed offset and fades/slides into view on
 * hover. Only transform + opacity ever animate (no box-shadow tweening), so
 * it stays GPU-cheap while still reading as real brutalist depth.
 */
export function FeatureCard({
  n,
  icon: Icon,
  title,
  desc,
  metrics,
  tone = "accent",
  span = "",
  border = true,
  delay = 0,
}: FeatureCardProps) {
  const reduce = useReducedMotion();
  const toneClass = tone === "accent" ? "text-accent" : "text-accent2";
  const toneBg = tone === "accent" ? "bg-accent" : "bg-accent2";

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-10%" }}
      transition={{ delay, duration: duration.cinematic, ease }}
      className={`group relative ${span} ${border ? "md:border-r border-line" : ""}`}
    >
      {/* Hard-shadow plate, offset, revealed on hover/focus only. */}
      {!reduce && (
        <div
          aria-hidden="true"
          className={`pointer-events-none absolute inset-0 ${toneBg} opacity-0 transition-opacity duration-150 ease-out translate-x-[6px] translate-y-[6px] group-hover:opacity-100`}
        />
      )}

      <div className="relative h-full border border-transparent bg-background p-8 transition-transform duration-150 ease-out will-change-transform group-hover:border-lineStrong group-hover:-translate-x-[2px] group-hover:-translate-y-[2px]">
        <div className="flex items-center justify-between">
          <Icon size={18} className={toneClass} />
          <span className="font-mono text-[10px] tracking-tight2 text-textMuted">{n}</span>
        </div>

        <h3 className="mt-8 font-display text-xl font-bold tracking-tight2">{title}</h3>
        <p className="mt-3 text-sm text-textSecondary leading-relaxed">{desc}</p>

        {metrics && metrics.length > 0 && (
          <div className="mt-6 flex flex-wrap items-baseline gap-x-6 gap-y-2 border-t border-line pt-5">
            {metrics.map((m) => (
              <div key={m.label} className="flex flex-col">
                <span className={`font-display text-2xl font-bold tracking-tight2 ${toneClass}`}>
                  <CountUp value={m.value} prefix={m.prefix} suffix={m.suffix} />
                </span>
                <span className="mt-1 font-mono text-[10px] uppercase tracking-tight2 text-textMuted">
                  {m.label}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}
