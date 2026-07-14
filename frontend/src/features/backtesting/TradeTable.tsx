import { Card } from "@/components/Card";
import { EmptyState } from "@/components/StateViews";
import type { Trade } from "@/types/api";

const REASON_LABELS: Record<string, string> = {
  holding_period: "Holding period reached",
  probability_exit: "Probability dropped",
  period_end: "End of backtest period",
};

export function TradeTable({ trades }: { trades: Trade[] }) {
  if (trades.length === 0) {
    return (
      <Card title="Trades">
        <EmptyState
          title="No trades were triggered"
          description="Try lowering the entry probability or sentiment threshold."
        />
      </Card>
    );
  }

  return (
    <Card title={`Trades (${trades.length})`}>
      <div className="max-h-80 overflow-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-white dark:bg-slate-900">
            <tr className="text-left text-xs text-slate-400">
              <th className="pb-2 pr-3 font-normal">Entry</th>
              <th className="pb-2 pr-3 font-normal">Exit</th>
              <th className="pb-2 pr-3 font-normal">Entry price</th>
              <th className="pb-2 pr-3 font-normal">Exit price</th>
              <th className="pb-2 pr-3 font-normal">Return</th>
              <th className="pb-2 font-normal">Exit reason</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((trade, i) => (
              <tr key={i} className="border-t border-slate-100 dark:border-slate-800">
                <td className="py-1.5 pr-3">{trade.entry_date}</td>
                <td className="py-1.5 pr-3">{trade.exit_date}</td>
                <td className="py-1.5 pr-3 tabular-nums">{trade.entry_price.toFixed(2)}</td>
                <td className="py-1.5 pr-3 tabular-nums">{trade.exit_price.toFixed(2)}</td>
                <td
                  className={`py-1.5 pr-3 tabular-nums font-medium ${
                    trade.return_pct >= 0 ? "text-bullish" : "text-bearish"
                  }`}
                >
                  {trade.return_pct >= 0 ? "+" : ""}
                  {trade.return_pct.toFixed(2)}%
                </td>
                <td className="py-1.5 text-slate-500 dark:text-slate-400">
                  {REASON_LABELS[trade.exit_reason] ?? trade.exit_reason}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
