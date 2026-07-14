import { useMemo } from "react";
import { Plot, PLOTLY_CONFIG, plotlyFont, plotlyGridColor } from "@/components/Plot";
import { useTheme } from "@/hooks/useTheme";
import type { HistoryResponse } from "@/types/api";

export function PriceVolumeChart({ history }: { history: HistoryResponse }) {
  const [theme] = useTheme();
  const isDark = theme === "dark";

  const dates = history.bars.map((b) => b.ts);
  const closes = history.bars.map((b) => b.close);
  const volumes = history.bars.map((b) => b.volume ?? 0);

  const summary = useMemo(() => {
    if (history.bars.length === 0) return "No price data available for this range.";
    const first = history.bars[0];
    const last = history.bars[history.bars.length - 1];
    const changePct = (((last.close - first.close) / first.close) * 100).toFixed(2);
    return `Price chart for ${history.ticker} from ${first.ts.slice(0, 10)} to ${last.ts.slice(0, 10)}. Closed at ${last.close.toFixed(2)}, a ${changePct}% change over the period (${history.data_status} data, source: ${history.source}). Volume chart below shows daily traded shares.`;
  }, [history]);

  return (
    <div>
      <p className="sr-only">{summary}</p>
      <Plot
        data={[
          {
            x: dates,
            open: history.bars.map((b) => b.open),
            high: history.bars.map((b) => b.high),
            low: history.bars.map((b) => b.low),
            close: closes,
            type: "candlestick",
            name: history.ticker,
            xaxis: "x",
            yaxis: "y",
            increasing: { line: { color: "#0f9d58" } },
            decreasing: { line: { color: "#c5221f" } },
          },
          {
            x: dates,
            y: volumes,
            type: "bar",
            name: "Volume",
            xaxis: "x",
            yaxis: "y2",
            marker: { color: isDark ? "#475569" : "#cbd5e1" },
          },
        ]}
        layout={{
          autosize: true,
          height: 420,
          margin: { t: 20, r: 20, l: 60, b: 40 },
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          font: plotlyFont(isDark),
          showlegend: false,
          xaxis: {
            gridcolor: plotlyGridColor(isDark),
            title: { text: "Date (UTC)" },
            rangeslider: { visible: false },
          },
          yaxis: {
            domain: [0.3, 1],
            gridcolor: plotlyGridColor(isDark),
            title: { text: "Price (USD)" },
          },
          yaxis2: {
            domain: [0, 0.22],
            gridcolor: plotlyGridColor(isDark),
            title: { text: "Volume (shares)" },
          },
        }}
        config={PLOTLY_CONFIG}
        useResizeHandler
        style={{ width: "100%" }}
      />
    </div>
  );
}
