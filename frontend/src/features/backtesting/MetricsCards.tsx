import { Card } from "@/components/Card";
import { Tooltip } from "@/components/Tooltip";

const METRIC_TOOLTIPS: Record<string, string> = {
  total_return_pct: "Total percentage change in portfolio value over the backtest period.",
  annualized_return_pct: "Total return scaled to a one-year equivalent rate.",
  annualized_volatility_pct: "Standard deviation of daily returns, annualized — a measure of risk.",
  sharpe_ratio: "Return per unit of total volatility (risk-adjusted return). Higher is better.",
  sortino_ratio: "Like Sharpe, but only penalizes downside volatility.",
  max_drawdown_pct: "The largest peak-to-trough decline during the backtest.",
  win_rate_pct: "Percentage of closed trades that were profitable.",
  num_trades: "Total number of completed trades.",
  avg_trade_return_pct: "Average percentage return per completed trade.",
  exposure_pct: "Percentage of the backtest period spent holding a position (vs. in cash).",
  turnover_count: "Total number of buy + sell fills.",
};

const LABELS: Record<string, string> = {
  total_return_pct: "Total return",
  annualized_return_pct: "Annualized return",
  annualized_volatility_pct: "Annualized volatility",
  sharpe_ratio: "Sharpe ratio",
  sortino_ratio: "Sortino ratio",
  max_drawdown_pct: "Max drawdown",
  win_rate_pct: "Win rate",
  num_trades: "Trades",
  avg_trade_return_pct: "Avg. trade return",
  exposure_pct: "Exposure",
  turnover_count: "Turnover",
};

const PERCENT_KEYS = new Set([
  "total_return_pct",
  "annualized_return_pct",
  "annualized_volatility_pct",
  "max_drawdown_pct",
  "win_rate_pct",
  "avg_trade_return_pct",
  "exposure_pct",
]);

export function MetricsCards({ metrics }: { metrics: Record<string, number | boolean> }) {
  const keys = Object.keys(LABELS).filter((k) => k in metrics);

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {keys.map((key) => {
        const value = metrics[key];
        const formatted =
          typeof value === "number"
            ? PERCENT_KEYS.has(key)
              ? `${value.toFixed(2)}%`
              : value.toFixed(key.includes("ratio") ? 2 : 0)
            : String(value);
        const isNegativeGood = key === "max_drawdown_pct";
        const numeric = typeof value === "number" ? value : 0;
        const colorClass =
          key.includes("return") || key === "sharpe_ratio" || key === "sortino_ratio"
            ? numeric >= 0
              ? "text-bullish"
              : "text-bearish"
            : isNegativeGood
              ? "text-bearish"
              : "";

        return (
          <Card key={key}>
            <p className="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
              {LABELS[key]}
              {METRIC_TOOLTIPS[key] && (
                <Tooltip label={LABELS[key]}>{METRIC_TOOLTIPS[key]}</Tooltip>
              )}
            </p>
            <p className={`mt-1 text-xl font-bold tabular-nums ${colorClass}`}>{formatted}</p>
          </Card>
        );
      })}
    </div>
  );
}
