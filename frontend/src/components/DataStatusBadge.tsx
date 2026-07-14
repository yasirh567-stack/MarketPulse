import type { DataStatus } from "@/types/api";

const CONFIG: Record<DataStatus, { label: string; icon: string; className: string }> = {
  live: {
    label: "Live",
    icon: "●",
    className: "bg-bullish-light text-bullish dark:bg-emerald-950 dark:text-emerald-400",
  },
  delayed: {
    label: "Delayed",
    icon: "◔",
    className: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-400",
  },
  historical: {
    label: "Historical",
    icon: "▤",
    className: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
  },
  cached: {
    label: "Cached",
    icon: "▢",
    className: "bg-sky-100 text-sky-800 dark:bg-sky-950 dark:text-sky-400",
  },
  demo: {
    label: "Demo",
    icon: "◆",
    className: "bg-violet-100 text-violet-800 dark:bg-violet-950 dark:text-violet-400",
  },
};

/**
 * Renders the data-provenance badge required everywhere data is shown. Uses
 * both an icon glyph and a text label (not color alone) so the distinction
 * still reads for colorblind users, per the accessibility requirements.
 */
export function DataStatusBadge({ status }: { status: DataStatus }) {
  const config = CONFIG[status] ?? CONFIG.cached;
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${config.className}`}
      title={`This data is ${config.label.toLowerCase()}`}
    >
      <span aria-hidden="true">{config.icon}</span>
      {config.label}
    </span>
  );
}
