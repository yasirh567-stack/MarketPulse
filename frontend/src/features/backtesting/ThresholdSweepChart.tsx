import { Card } from "@/components/Card";
import { Plot, PLOTLY_CONFIG, plotlyFont, plotlyGridColor } from "@/components/Plot";
import { useTheme } from "@/hooks/useTheme";
import type { ThresholdSweepPoint } from "@/types/api";

export function ThresholdSweepChart({ thresholds }: { thresholds: ThresholdSweepPoint[] }) {
  const [theme] = useTheme();
  const isDark = theme === "dark";

  return (
    <Card title="Confidence-threshold comparison">
      <p className="mb-3 text-xs text-slate-500 dark:text-slate-400">
        The same strategy run at each entry-probability threshold, against the identical
        out-of-sample signal — shows whether trading only when the model is more confident actually
        improves risk-adjusted return, or just means fewer trades with no edge.
      </p>
      <Plot
        data={[
          {
            x: thresholds.map((t) => t.prob_threshold),
            y: thresholds.map((t) => t.sharpe_ratio),
            type: "scatter",
            mode: "lines+markers",
            name: "Sharpe ratio",
            line: { color: "#0ea5e9" },
            marker: { size: 8 },
          },
        ]}
        layout={{
          autosize: true,
          height: 260,
          margin: { t: 10, r: 20, l: 50, b: 40 },
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          font: plotlyFont(isDark),
          xaxis: {
            gridcolor: plotlyGridColor(isDark),
            title: { text: "Entry probability threshold" },
          },
          yaxis: {
            gridcolor: plotlyGridColor(isDark),
            title: { text: "Sharpe ratio" },
            zeroline: true,
          },
        }}
        config={PLOTLY_CONFIG}
        useResizeHandler
        style={{ width: "100%" }}
      />
      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[520px] text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-400">
              <th className="pb-2 pr-3 font-normal">Threshold</th>
              <th className="pb-2 pr-3 font-normal">Sharpe</th>
              <th className="pb-2 pr-3 font-normal">Total return</th>
              <th className="pb-2 pr-3 font-normal">Win rate</th>
              <th className="pb-2 pr-3 font-normal">Trades</th>
              <th className="pb-2 pr-3 font-normal">Max drawdown</th>
            </tr>
          </thead>
          <tbody>
            {thresholds.map((t) => (
              <tr
                key={t.prob_threshold}
                className="border-t border-slate-100 dark:border-slate-800"
              >
                <td className="py-2 pr-3 font-medium tabular-nums">
                  {t.prob_threshold.toFixed(2)}
                </td>
                <td className="py-2 pr-3 tabular-nums">{t.sharpe_ratio.toFixed(2)}</td>
                <td className="py-2 pr-3 tabular-nums">{t.total_return_pct.toFixed(2)}%</td>
                <td className="py-2 pr-3 tabular-nums">{t.win_rate_pct.toFixed(1)}%</td>
                <td className="py-2 pr-3 tabular-nums">{t.num_trades}</td>
                <td className="py-2 pr-3 tabular-nums">{t.max_drawdown_pct.toFixed(2)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
