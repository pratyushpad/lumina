/**
 * Single motion vocabulary. Import these instead of inlining durations or
 * curves in components, so timing stays consistent as the UI grows.
 *
 * Durations follow the rule that UI motion stays under 300ms — anything slower
 * reads as lag on interactions the user repeats.
 */
export const duration = {
  fast: 0.12, // press feedback, hover
  base: 0.18, // disclosure, chips, inline reveals
  slow: 0.24, // overlays, panels
  cinematic: 0.6, // large landing entrances / scroll reveals (non-interactive)
} as const;

/** Expressive ease-out: starts fast so the UI feels immediately responsive. */
export const ease = [0.22, 1, 0.36, 1] as const;

/** Same curve as a CSS string, for `transition`/`animation` shorthand. */
export const easeCss = "cubic-bezier(0.22, 1, 0.36, 1)";

/**
 * Waterfall reveal for lists that represent a sequence (e.g. the trace
 * inspector's pipeline stages). Slightly larger step than `staggerStep` so the
 * cascade reads as a pipeline, not a single block.
 */
export const waterfallStep = 0.06;

/** Between staggered siblings; keep total stagger under ~0.4s. */
export const staggerStep = 0.04;

/** Standard entrance for content that appears in place. */
export const fadeRise = {
  hidden: { opacity: 0, y: 8 },
  visible: { opacity: 1, y: 0 },
};

/**
 * Press feedback. Subtle scale-down confirms the interface heard the click;
 * spring rather than duration so a rapid press/release stays smooth.
 */
export const springPress = { type: "spring", stiffness: 500, damping: 30 } as const;

/** Overlays scale from near-full — nothing in the real world grows from nothing. */
export const overlayIn = {
  initial: { opacity: 0, scale: 0.97 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.97 },
};
