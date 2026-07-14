import { useSelectedTicker } from "@/hooks/useSelectedTicker";
import { useRunBacktest, useThresholdSweep } from "@/api/hooks";
import { TickerSearch } from "@/components/TickerSearch";
import { Card } from "@/components/Card";
import { ErrorState, SkeletonBlock } from "@/components/StateViews";
import { BacktestForm } from "@/features/backtesting/BacktestForm";
import { MetricsCards } from "@/features/backtesting/MetricsCards";
import { EquityDrawdownChart } from "@/features/backtesting/EquityDrawdownChart";
import { TradeTable } from "@/features/backtesting/TradeTable";
import { MonthlyReturnsHeatmap } from "@/features/backtesting/MonthlyReturnsHeatmap";
import { ThresholdSweepChart } from "@/features/backtesting/ThresholdSweepChart";
import type { BacktestConfigInput } from "@/types/api";

export function BacktestingPage() {
  const { ticker, setTicker } = useSelectedTicker();
  const backtestMutation = useRunBacktest();
  const sweepMutation = useThresholdSweep();

  function handleSubmit(config: BacktestConfigInput) {
    backtestMutation.mutate(config);
  }

  function handleSweep(config: BacktestConfigInput) {
    sweepMutation.mutate({
      ticker: config.ticker,
      start_date: config.start_date,
      end_date: config.end_date,
      sentiment_threshold: config.sentiment_threshold,
      exit_prob_threshold: config.exit_prob_threshold,
      holding_period_days: config.holding_period_days,
      transaction_cost_bps: config.transaction_cost_bps,
      slippage_bps: config.slippage_bps,
      initial_capital: config.initial_capital,
      model_name: config.model_name,
      prob_thresholds: [0.5, 0.55, 0.6, 0.65, 0.7],
    });
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Backtesting: {ticker}</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Simulate a sentiment + probability threshold strategy against buy-and-hold.
          </p>
        </div>
        <TickerSearch onSelect={setTicker} />
      </div>

      <Card title="Strategy configuration">
        <BacktestForm
          ticker={ticker}
          onSubmit={handleSubmit}
          isSubmitting={backtestMutation.isPending}
          onSweep={handleSweep}
          isSweeping={sweepMutation.isPending}
        />
      </Card>

      <div
        role="status"
        className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-200"
      >
        <strong>Hypothetical results.</strong> This simulates a strategy against historical/demo
        data with simplified execution assumptions. Past performance does not guarantee future
        results, and this is not financial advice.
      </div>

      {backtestMutation.isPending && (
        <Card>
          <SkeletonBlock lines={8} />
        </Card>
      )}

      {backtestMutation.isError && (
        <ErrorState
          title="Backtest failed"
          description={(backtestMutation.error as Error)?.message}
          onRetry={() => backtestMutation.mutate(backtestMutation.variables!)}
        />
      )}

      {backtestMutation.data && (
        <>
          <MetricsCards metrics={backtestMutation.data.metrics} />
          <EquityDrawdownChart
            equityCurve={backtestMutation.data.equity_curve}
            benchmarkCurve={backtestMutation.data.benchmark_curve}
            drawdownCurve={backtestMutation.data.drawdown_curve}
            trades={backtestMutation.data.trades}
          />
          <div className="grid gap-6 lg:grid-cols-2">
            <TradeTable trades={backtestMutation.data.trades} />
            <MonthlyReturnsHeatmap monthlyReturns={backtestMutation.data.monthly_returns} />
          </div>
        </>
      )}

      {sweepMutation.isPending && (
        <Card title="Confidence-threshold comparison">
          <SkeletonBlock lines={6} />
        </Card>
      )}

      {sweepMutation.isError && (
        <ErrorState
          title="Threshold comparison failed"
          description={(sweepMutation.error as Error)?.message}
          onRetry={() => sweepMutation.mutate(sweepMutation.variables!)}
        />
      )}

      {sweepMutation.data && <ThresholdSweepChart thresholds={sweepMutation.data.thresholds} />}
    </div>
  );
}
