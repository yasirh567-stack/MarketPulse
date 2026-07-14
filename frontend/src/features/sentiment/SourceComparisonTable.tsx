import { Card } from "@/components/Card";
import { EmptyState } from "@/components/StateViews";
import type { SourceComparisonEntry } from "@/types/api";

function Row({ label, entry }: { label: string; entry: SourceComparisonEntry }) {
  const isPositive = entry.avg_compound >= 0;
  return (
    <tr className="border-b border-slate-100 last:border-0 dark:border-slate-800">
      <td className="py-2 pr-4 font-medium capitalize">{label}</td>
      <td className={`py-2 pr-4 tabular-nums ${isPositive ? "text-bullish" : "text-bearish"}`}>
        {entry.avg_compound.toFixed(3)}
      </td>
      <td className="py-2 tabular-nums text-slate-500 dark:text-slate-400">{entry.count}</td>
    </tr>
  );
}

export function SourceComparisonTable({
  bySourceType,
  byModel,
}: {
  bySourceType: Record<string, SourceComparisonEntry>;
  byModel: Record<string, SourceComparisonEntry>;
}) {
  const hasData = Object.keys(bySourceType).length > 0 || Object.keys(byModel).length > 0;

  return (
    <Card title="Source & model comparison">
      {!hasData ? (
        <EmptyState title="No comparison data yet" />
      ) : (
        <div className="space-y-4">
          <div>
            <h4 className="mb-1 text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
              By source
            </h4>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-slate-400">
                  <th className="pb-1 font-normal">Source</th>
                  <th className="pb-1 font-normal">Avg. compound</th>
                  <th className="pb-1 font-normal">Count</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(bySourceType).map(([key, entry]) => (
                  <Row key={key} label={key} entry={entry} />
                ))}
              </tbody>
            </table>
          </div>
          <div>
            <h4 className="mb-1 text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
              By NLP model
            </h4>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-slate-400">
                  <th className="pb-1 font-normal">Model</th>
                  <th className="pb-1 font-normal">Avg. compound</th>
                  <th className="pb-1 font-normal">Count</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(byModel).map(([key, entry]) => (
                  <Row key={key} label={key} entry={entry} />
                ))}
              </tbody>
            </table>
            <p className="mt-2 text-xs text-slate-400">
              Only one model is active unless FinBERT is enabled — this table compares whichever
              models actually scored text, never fabricated numbers for an inactive model.
            </p>
          </div>
        </div>
      )}
    </Card>
  );
}
