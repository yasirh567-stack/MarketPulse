import { Card } from "@/components/Card";
import { Tooltip } from "@/components/Tooltip";
import type { LeaderboardEntry } from "@/types/api";

const LEADERBOARD_COLUMNS: {
  key: keyof LeaderboardEntry;
  label: string;
  tooltip: string;
  format: (v: unknown) => string;
}[] = [
  {
    key: "balanced_accuracy",
    label: "Balanced acc.",
    tooltip:
      "Accuracy adjusted for class imbalance — a fairer number when up/down days aren't 50/50.",
    format: (v) => (typeof v === "number" ? `${(v * 100).toFixed(1)}%` : "—"),
  },
  {
    key: "roc_auc",
    label: "ROC-AUC",
    tooltip:
      "Ability to rank up-days above down-days across all thresholds. 0.5 = no better than chance.",
    format: (v) => (typeof v === "number" ? v.toFixed(3) : "—"),
  },
  {
    key: "brier_score",
    label: "Brier score",
    tooltip: "Mean squared error of predicted probability vs. actual outcome — lower is better.",
    format: (v) => (typeof v === "number" ? v.toFixed(3) : "—"),
  },
  {
    key: "n_train_samples",
    label: "Train samples",
    tooltip: "Number of trading days used to train this model.",
    format: (v) => (typeof v === "number" ? String(v) : "—"),
  },
  {
    key: "trained_at",
    label: "Trained",
    tooltip: "When this model was last (re)trained.",
    format: (v) => (typeof v === "string" ? new Date(v).toLocaleString() : "—"),
  },
];

function BeatsBaselineBadge({ entry }: { entry: LeaderboardEntry }) {
  if (entry.status !== "ok") return <span className="text-slate-400">—</span>;
  return (
    <span
      className={`rounded px-1.5 py-0.5 text-xs font-medium ${
        entry.beats_baseline
          ? "bg-bullish-light text-bullish dark:bg-green-950/40 dark:text-green-400"
          : "bg-bearish-light text-bearish dark:bg-red-950/40 dark:text-red-400"
      }`}
    >
      {entry.beats_baseline ? "Beats baseline" : "No edge over baseline"}
    </span>
  );
}

export function LeaderboardTable({ entries }: { entries: LeaderboardEntry[] }) {
  return (
    <Card title="Model leaderboard">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-400">
              <th className="pb-2 pr-3 font-normal">Ticker</th>
              {LEADERBOARD_COLUMNS.map((col) => (
                <th key={col.key} className="pb-2 pr-3 font-normal">
                  <span className="flex items-center gap-1">
                    {col.label}
                    <Tooltip label={col.label}>{col.tooltip}</Tooltip>
                  </span>
                </th>
              ))}
              <th className="pb-2 pr-3 font-normal">vs. baseline</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry) => (
              <tr key={entry.ticker} className="border-t border-slate-100 dark:border-slate-800">
                <td className="py-2 pr-3 font-medium">{entry.ticker}</td>
                {entry.status === "ok" ? (
                  LEADERBOARD_COLUMNS.map((col) => (
                    <td key={col.key} className="py-2 pr-3 tabular-nums">
                      {col.format(entry[col.key])}
                    </td>
                  ))
                ) : (
                  <td
                    colSpan={LEADERBOARD_COLUMNS.length}
                    className="py-2 pr-3 text-slate-400 dark:text-slate-500"
                  >
                    {entry.status === "insufficient_data" ? "Insufficient data" : "Unavailable"}
                    {entry.note ? ` — ${entry.note}` : ""}
                  </td>
                )}
                <td className="py-2 pr-3">
                  <BeatsBaselineBadge entry={entry} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-3 text-xs text-slate-400">
        Walk-forward validation metrics only — not evidence of future performance. "Beats baseline"
        compares balanced accuracy against the stronger of the majority-class and previous-direction
        baselines.
      </p>
    </Card>
  );
}
