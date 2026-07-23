/**
 * GSAP setup — registers plugins once and defines a named CustomEase that
 * matches the Framer Motion house curve in `motion.ts` ([0.22, 1, 0.36, 1]),
 * so scroll-driven GSAP work and interaction-driven Framer work share one
 * feel. Import `gsap` / `ScrollTrigger` from here, never from "gsap" directly,
 * so registration is guaranteed to have run.
 */
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { CustomEase } from "gsap/CustomEase";

// ES modules evaluate once, so this registration runs a single time per app.
gsap.registerPlugin(ScrollTrigger, CustomEase);

// Mirrors ease = [0.22, 1, 0.36, 1] from lib/motion.ts.
// cubic-bezier(x1,y1,x2,y2) -> "M0,0 C{x1},{y1} {x2},{y2} 1,1"
CustomEase.create("house", "M0,0 C0.22,1 0.36,1 1,1");

gsap.defaults({ ease: "house", duration: 0.6 });

/** Named ease string for use in gsap.to/from/timeline calls. */
export const HOUSE_EASE = "house";

export { gsap, ScrollTrigger };
