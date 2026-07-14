import { Card } from "@/components/Card";
import { EmptyState } from "@/components/StateViews";
import type { MonthlyReturn } from "@/types/api";

export function MonthlyReturnsHeatmap({ monthlyReturns }: { monthlyReturns: MonthlyReturn[] }) {
  if (monthlyReturns.length === 0) {
    return (
      <Card title="Monthly returns">
        <EmptyState title="Not enough history for a monthly breakdown" />
      </Card>
    );
  }

  const maxAbs = Math.max(...monthlyReturns.map((m) => Math.abs(m.return_pct)), 1);

  return (
    <Card title="Monthly returns">
      <div className="flex flex-wrap gap-2">
        {monthlyReturns.map((m) => {
          const intensity = Math.min(Math.abs(m.return_pct) / maxAbs, 1);
          const isPositive = m.return_pct >= 0;
          return (
            <div
              key={m.month}
              className="flex w-20 flex-col items-center rounded-md p-2 text-center text-xs"
              style={{
                backgroundColor: isPositive
                  ? `rgba(15, 157, 88, ${0.15 + intensity * 0.5})`
                  : `rgba(197, 34, 31, ${0.15 + intensity * 0.5})`,
              }}
            >
              <span className="font-medium">{m.month}</span>
              <span className={isPositive ? "text-bullish" : "text-bearish"}>
                {isPositive ? "+" : ""}
                {m.return_pct.toFixed(1)}%
              </span>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
