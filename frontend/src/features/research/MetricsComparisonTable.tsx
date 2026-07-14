import { Card } from "@/components/Card";
import { Tooltip } from "@/components/Tooltip";

interface MetricsRow {
  label: string;
  metrics: Record<string, unknown>;
  highlight?: boolean;
}

const METRIC_COLUMNS: {
  key: string;
  label: string;
  tooltip: string;
  format: (v: unknown) => string;
}[] = [
  {
    key: "accuracy",
    label: "Accuracy",
    tooltip: "Fraction of predictions that matched the actual next-day direction.",
    format: (v) => (typeof v === "number" ? `${(v * 100).toFixed(1)}%` : "—"),
  },
  {
    key: "balanced_accuracy",
    label: "Balanced acc.",
    tooltip:
      "Accuracy adjusted for class imbalance — a fairer number when up/down days aren't 50/50.",
    format: (v) => (typeof v === "number" ? `${(v * 100).toFixed(1)}%` : "—"),
  },
  {
    key: "precision",
    label: "Precision",
    tooltip: "Of the days the model predicted 'up', what fraction actually went up.",
    format: (v) => (typeof v === "number" ? v.toFixed(3) : "—"),
  },
  {
    key: "recall",
    label: "Recall",
    tooltip: "Of all days that actually went up, what fraction the model caught.",
    format: (v) => (typeof v === "number" ? v.toFixed(3) : "—"),
  },
  {
    key: "f1",
    label: "F1",
    tooltip: "Harmonic mean of precision and recall.",
    format: (v) => (typeof v === "number" ? v.toFixed(3) : "—"),
  },
  {
    key: "roc_auc",
    label: "ROC-AUC",
    tooltip:
      "Ability to rank up-days above down-days across all thresholds. 0.5 = no better than chance.",
    format: (v) => (typeof v === "number" ? v.toFixed(3) : "n/a"),
  },
  {
    key: "brier_score",
    label: "Brier score",
    tooltip:
      "Mean squared error of the predicted probability vs. the actual outcome — lower is better calibrated.",
    format: (v) => (typeof v === "number" ? v.toFixed(3) : "—"),
  },
];

export function MetricsComparisonTable({ rows }: { rows: MetricsRow[] }) {
  return (
    <Card title="Model & baseline comparison">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-400">
              <th className="pb-2 pr-3 font-normal">Model</th>
              {METRIC_COLUMNS.map((col) => (
                <th key={col.key} className="pb-2 pr-3 font-normal">
                  <span className="flex items-center gap-1">
                    {col.label}
                    <Tooltip label={col.label}>{col.tooltip}</Tooltip>
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={row.label}
                className={`border-t border-slate-100 dark:border-slate-800 ${
                  row.highlight ? "bg-sky-50 dark:bg-sky-950/30" : ""
                }`}
              >
                <td className="py-2 pr-3 font-medium">{row.label}</td>
                {METRIC_COLUMNS.map((col) => (
                  <td key={col.key} className="py-2 pr-3 tabular-nums">
                    {col.format(row.metrics[col.key])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-3 text-xs text-slate-400">
        Metrics come from walk-forward (expanding-window) validation — the model is only ever
        evaluated on data that comes chronologically after what it was trained on, never a random
        shuffled split.
      </p>
    </Card>
  );
}
