import { Card } from "@/components/Card";
import { Plot, PLOTLY_CONFIG, plotlyFont, plotlyGridColor } from "@/components/Plot";
import { Tooltip } from "@/components/Tooltip";
import { useTheme } from "@/hooks/useTheme";
import type { PredictionResponse } from "@/types/api";

const CONFIDENCE_COPY: Record<string, string> = {
  low: "Low confidence — probability is close to 50/50.",
  moderate: "Moderate confidence.",
  high: "Higher confidence, but still not a guarantee.",
};

export function PredictionCard({ prediction }: { prediction: PredictionResponse }) {
  const [theme] = useTheme();
  const isDark = theme === "dark";
  const isUp = prediction.predicted_direction === "up";
  const features = prediction.top_features.slice(0, 6).reverse();
  const importanceKey =
    features.length > 0 && "importance" in features[0] ? "importance" : "coefficient";

  return (
    <Card
      title={
        <span className="flex items-center gap-1.5">
          Next-day direction estimate
          <Tooltip label="What is this?">
            A research model's statistical estimate of tomorrow's price direction, trained with
            walk-forward validation. Not financial advice.
          </Tooltip>
        </span>
      }
    >
      <div className="flex flex-wrap items-center gap-4">
        <div
          className={`flex items-center gap-2 rounded-lg px-4 py-3 text-lg font-bold ${
            isUp
              ? "bg-bullish-light text-bullish dark:bg-emerald-950 dark:text-emerald-400"
              : "bg-bearish-light text-bearish dark:bg-red-950 dark:text-red-400"
          }`}
        >
          <span aria-hidden="true">{isUp ? "▲" : "▼"}</span>
          {isUp ? "Up" : "Down"}
        </div>
        <div>
          <p className="text-sm text-slate-500 dark:text-slate-400">Probability up</p>
          <p className="text-2xl font-bold tabular-nums">
            {(prediction.probability_up * 100).toFixed(1)}%
          </p>
        </div>
        <div>
          <p className="text-sm text-slate-500 dark:text-slate-400">Confidence</p>
          <p className="text-lg font-semibold capitalize">{prediction.confidence_label}</p>
        </div>
        <div className="ml-auto text-right text-xs text-slate-400">
          <p>Model: {prediction.model_name}</p>
          <p>Trained: {new Date(prediction.trained_at).toLocaleString()}</p>
          <p>{prediction.n_train_samples} training samples</p>
        </div>
      </div>

      <p className="mt-3 text-sm text-slate-600 dark:text-slate-400">
        {CONFIDENCE_COPY[prediction.confidence_label]}
      </p>
      {prediction.sentiment_shift_note && (
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
          {prediction.sentiment_shift_note}
        </p>
      )}

      {features.length > 0 && (
        <div className="mt-4">
          <h4 className="mb-1 text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
            Most influential features (permutation importance)
          </h4>
          <p className="sr-only">
            Horizontal bar chart ranking which input features most affected model accuracy when
            shuffled, from {features[0]?.feature} to {features[features.length - 1]?.feature}.
          </p>
          <Plot
            data={[
              {
                x: features.map((f) => (f[importanceKey as keyof typeof f] as number) ?? 0),
                y: features.map((f) => f.feature),
                type: "bar",
                orientation: "h",
                marker: { color: "#0ea5e9" },
              },
            ]}
            layout={{
              autosize: true,
              height: 40 * features.length + 60,
              margin: { t: 10, r: 20, l: 140, b: 40 },
              paper_bgcolor: "transparent",
              plot_bgcolor: "transparent",
              font: plotlyFont(isDark),
              xaxis: { gridcolor: plotlyGridColor(isDark), title: { text: "Importance" } },
              yaxis: { automargin: true },
            }}
            config={PLOTLY_CONFIG}
            useResizeHandler
            style={{ width: "100%" }}
          />
        </div>
      )}

      <ul className="mt-4 list-disc space-y-1 pl-5 text-xs text-slate-400">
        {prediction.limitations.map((l) => (
          <li key={l}>{l}</li>
        ))}
      </ul>
    </Card>
  );
}
