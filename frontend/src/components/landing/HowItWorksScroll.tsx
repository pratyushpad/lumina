import { motion, useReducedMotion } from "framer-motion";
import { ArrowUpRight } from "lucide-react";
import { useEffect, useRef } from "react";
import { gsap } from "@/lib/gsapConfig";

interface Step {
  n: string;
  t: string;
  d: string;
}

interface HowItWorksScrollProps {
  steps: Step[];
}

/**
 * Scroll-driven pipeline: a hairline connector runs down the left edge of the
 * stage list and fills in an accent line as the section scrolls through
 * view, with each stage revealing in lockstep. One GSAP timeline scrubbed to
 * a single ScrollTrigger keeps the line-draw and the four reveals perfectly
 * in sync (all frames of one 0->1 progress value).
 *
 * Reduced motion renders the original static stacked list — no scrub, no
 * pinning, everything visible via a simple opacity-only whileInView.
 */
export function HowItWorksScroll({ steps }: HowItWorksScrollProps) {
  const reduce = useReducedMotion();
  const sectionRef = useRef<HTMLDivElement>(null);
  const lineFillRef = useRef<HTMLDivElement>(null);
  const rowRefs = useRef<Array<HTMLDivElement | null>>([]);

  useEffect(() => {
    if (reduce) return;
    const ctx = gsap.context(() => {
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: sectionRef.current,
          start: "top 75%",
          end: "bottom 55%",
          scrub: 0.6,
        },
      });

      tl.fromTo(lineFillRef.current, { scaleY: 0 }, { scaleY: 1, ease: "none", duration: 4 }, 0);

      rowRefs.current.forEach((row, i) => {
        if (!row) return;
        tl.fromTo(
          row,
          { opacity: 0, x: -16 },
          { opacity: 1, x: 0, ease: "none", duration: 1 },
          i * 0.95,
        );
      });
    }, sectionRef);

    // ctx.revert() tears down every tween + ScrollTrigger created inside the
    // context callback above, so no separate ScrollTrigger.kill() is needed.
    return () => ctx.revert();
  }, [reduce]);

  if (reduce) {
    return (
      <div className="border-t border-line">
        {steps.map((s, i) => (
          <motion.div
            key={s.n}
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.06 }}
            className="grid grid-cols-12 items-center border-b border-line py-8"
          >
            <span className="col-span-2 font-mono text-xs text-textMuted">{s.n}</span>
            <span className="col-span-4 md:col-span-3 font-display text-2xl md:text-3xl font-bold tracking-tight2 text-textPrimary">
              {s.t}
            </span>
            <span className="col-span-6 md:col-span-6 text-sm text-textSecondary">{s.d}</span>
          </motion.div>
        ))}
      </div>
    );
  }

  return (
    <div ref={sectionRef} className="relative border-t border-line pl-6">
      {/* Connector track + scrubbed fill */}
      <div className="absolute left-0 top-0 h-full w-px bg-line" />
      <div
        ref={lineFillRef}
        className="absolute left-0 top-0 h-full w-px origin-top bg-accent"
        style={{ transform: "scaleY(0)" }}
      />

      {steps.map((s, i) => (
        <div
          key={s.n}
          ref={(el) => {
            rowRefs.current[i] = el;
          }}
          className="group relative grid grid-cols-12 items-center border-b border-line py-8 opacity-0 transition-colors hover:bg-textPrimary/[0.03]"
        >
          <span
            aria-hidden="true"
            className="absolute -left-6 top-1/2 h-2 w-2 -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent"
          />
          <span className="col-span-2 font-mono text-xs text-textMuted">{s.n}</span>
          <span className="col-span-4 md:col-span-3 font-display text-2xl md:text-3xl font-bold tracking-tight2 text-textPrimary">
            {s.t}
          </span>
          <span className="col-span-5 md:col-span-5 text-sm text-textSecondary">{s.d}</span>
          <ArrowUpRight
            size={20}
            className="col-span-1 ml-auto text-textMuted transition-colors group-hover:text-accent"
          />
        </div>
      ))}
    </div>
  );
}
