import type { SentimentLabel } from "@/types/api";

const CONFIG: Record<SentimentLabel, { label: string; icon: string; className: string }> = {
  bullish: {
    label: "Bullish",
    icon: "▲",
    className: "bg-bullish-light text-bullish dark:bg-emerald-950 dark:text-emerald-400",
  },
  neutral: {
    label: "Neutral",
    icon: "●",
    className: "bg-neutral-light text-neutral dark:bg-slate-800 dark:text-slate-300",
  },
  bearish: {
    label: "Bearish",
    icon: "▼",
    className: "bg-bearish-light text-bearish dark:bg-red-950 dark:text-red-400",
  },
};

/** Icon + label sentiment indicator — never color-only, so it remains legible
 * without relying on red/green perception. */
export function SentimentBadge({ label }: { label: SentimentLabel }) {
  const config = CONFIG[label];
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${config.className}`}
    >
      <span aria-hidden="true">{config.icon}</span>
      {config.label}
    </span>
  );
}
