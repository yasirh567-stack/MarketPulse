import { Card } from "@/components/Card";
import { Tooltip } from "@/components/Tooltip";
import { EmptyState } from "@/components/StateViews";

export function ConfusionMatrix({ matrix }: { matrix: number[][] | undefined }) {
  if (!matrix || matrix.length !== 2) {
    return (
      <Card title="Confusion matrix">
        <EmptyState title="No confusion matrix available" />
      </Card>
    );
  }
  const [[tn, fp], [fn, tp]] = matrix;
  const total = tn + fp + fn + tp;

  const cells = [
    { label: "Predicted down, actually down", value: tn, kind: "correct" },
    { label: "Predicted up, actually down", value: fp, kind: "wrong" },
    { label: "Predicted down, actually up", value: fn, kind: "wrong" },
    { label: "Predicted up, actually up", value: tp, kind: "correct" },
  ];

  return (
    <Card
      title={
        <span className="flex items-center gap-1.5">
          Confusion matrix
          <Tooltip label="How to read this">
            Rows are actual outcomes, columns are predicted outcomes, summed across all
            out-of-sample walk-forward folds ({total} predictions total).
          </Tooltip>
        </span>
      }
    >
      <div className="grid grid-cols-2 gap-2 text-center text-sm">
        {cells.map((cell) => (
          <div
            key={cell.label}
            className={`rounded-lg p-4 ${
              cell.kind === "correct"
                ? "bg-bullish-light dark:bg-emerald-950/60"
                : "bg-bearish-light dark:bg-red-950/60"
            }`}
          >
            <p className="text-2xl font-bold tabular-nums">{cell.value}</p>
            <p className="mt-1 text-xs text-slate-600 dark:text-slate-300">{cell.label}</p>
          </div>
        ))}
      </div>
      <p className="mt-2 text-xs text-slate-400">{total} total out-of-sample predictions.</p>
    </Card>
  );
}
