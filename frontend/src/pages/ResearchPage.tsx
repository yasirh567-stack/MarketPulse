import { useSelectedTicker } from "@/hooks/useSelectedTicker";
import { useModelMetrics } from "@/api/hooks";
import { TickerSearch } from "@/components/TickerSearch";
import { Card } from "@/components/Card";
import { ErrorState, SkeletonBlock } from "@/components/StateViews";
import { MetricsComparisonTable } from "@/features/research/MetricsComparisonTable";
import { ConfusionMatrix } from "@/features/research/ConfusionMatrix";
import { FeatureImportanceChart } from "@/features/research/FeatureImportanceChart";

export function ResearchPage() {
  const { ticker, setTicker } = useSelectedTicker();
  const { data, isLoading, isError, error, refetch } = useModelMetrics(ticker);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Research: {ticker}</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Model methodology, validation metrics, and explainability for the current ticker.
          </p>
        </div>
        <TickerSearch onSelect={setTicker} />
      </div>

      {isLoading && (
        <Card>
          <SkeletonBlock lines={6} />
        </Card>
      )}
      {isError && (
        <ErrorState
          title="No trained model yet for this ticker"
          description={
            (error as Error)?.message ??
            "Visit the Dashboard for this ticker first to trigger training, then come back."
          }
          onRetry={() => refetch()}
        />
      )}

      {data && (
        <>
          <Card>
            <div className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
              <div>
                <p className="text-slate-500 dark:text-slate-400">Model</p>
                <p className="font-semibold">{data.model_name}</p>
              </div>
              <div>
                <p className="text-slate-500 dark:text-slate-400">Trained</p>
                <p className="font-semibold">{new Date(data.trained_at).toLocaleString()}</p>
              </div>
              <div>
                <p className="text-slate-500 dark:text-slate-400">Training window</p>
                <p className="font-semibold">
                  {new Date(data.train_start).toLocaleDateString()} –{" "}
                  {new Date(data.train_end).toLocaleDateString()}
                </p>
              </div>
              <div>
                <p className="text-slate-500 dark:text-slate-400">Samples</p>
                <p className="font-semibold">
                  {data.n_train_samples} train / {data.n_test_samples} out-of-sample test
                </p>
              </div>
            </div>
          </Card>

          <MetricsComparisonTable
            rows={[
              { label: "Majority-class baseline", metrics: data.baseline_metrics.majority_class },
              {
                label: "Previous-direction baseline",
                metrics: data.baseline_metrics.previous_direction,
              },
              { label: "Price-only model", metrics: data.metrics.price_only },
              { label: "Sentiment-only model", metrics: data.metrics.sentiment_only },
              {
                label: `Combined model (${data.model_name})`,
                metrics: data.metrics.combined,
                highlight: true,
              },
            ]}
          />

          <ConfusionMatrix
            matrix={(data.metrics.combined as { confusion_matrix?: number[][] }).confusion_matrix}
          />

          <div className="grid gap-6 lg:grid-cols-2">
            <FeatureImportanceChart
              entries={data.metrics.permutation_importance}
              valueKey="importance"
              title="Permutation importance (default)"
            />
            <FeatureImportanceChart
              entries={data.metrics.shap}
              valueKey="mean_abs_shap"
              title="SHAP values (optional enhancement)"
            />
          </div>

          <Card title="Model limitations">
            <ul className="list-disc space-y-1 pl-5 text-sm text-slate-600 dark:text-slate-400">
              <li>
                Trained on a limited window of daily bars and news sentiment — not intraday or
                high-frequency data.
              </li>
              <li>
                Walk-forward validation only; performance can still vary significantly across
                tickers and time periods.
              </li>
              <li>Random seed {data.random_seed} — reproducible, but not immune to overfitting.</li>
              <li>
                A model beating the baselines here on historical data is not a guarantee it will do
                so going forward.
              </li>
            </ul>
          </Card>
        </>
      )}
    </div>
  );
}
