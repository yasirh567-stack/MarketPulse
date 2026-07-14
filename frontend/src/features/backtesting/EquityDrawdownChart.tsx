import { Card } from "@/components/Card";
import { Plot, PLOTLY_CONFIG, plotlyFont, plotlyGridColor } from "@/components/Plot";
import { useTheme } from "@/hooks/useTheme";
import type { DrawdownPoint, EquityPoint, Trade } from "@/types/api";

export function EquityDrawdownChart({
  equityCurve,
  benchmarkCurve,
  drawdownCurve,
  trades,
}: {
  equityCurve: EquityPoint[];
  benchmarkCurve: EquityPoint[];
  drawdownCurve: DrawdownPoint[];
  trades: Trade[];
}) {
  const [theme] = useTheme();
  const isDark = theme === "dark";

  const tradeEntryDates = trades.map((t) => t.entry_date);
  const tradeEntryValues = trades.map((t) => {
    const point = equityCurve.find((p) => p.date === t.entry_date);
    return point?.value ?? null;
  });

  return (
    <Card title="Equity curve vs. buy-and-hold">
      <p className="sr-only">
        Line chart comparing strategy equity to a buy-and-hold benchmark over time, with trade entry
        markers, followed by a drawdown chart showing percentage decline from each running peak.
      </p>
      <Plot
        data={[
          {
            x: equityCurve.map((p) => p.date),
            y: equityCurve.map((p) => p.value),
            type: "scatter",
            mode: "lines",
            name: "Strategy",
            xaxis: "x",
            yaxis: "y",
            line: { color: "#0ea5e9" },
          },
          {
            x: benchmarkCurve.map((p) => p.date),
            y: benchmarkCurve.map((p) => p.value),
            type: "scatter",
            mode: "lines",
            name: "Buy & hold",
            xaxis: "x",
            yaxis: "y",
            line: { color: "#94a3b8", dash: "dot" },
          },
          {
            x: tradeEntryDates,
            y: tradeEntryValues,
            type: "scatter",
            mode: "markers",
            name: "Trade entry",
            xaxis: "x",
            yaxis: "y",
            marker: { color: "#0f9d58", size: 9, symbol: "triangle-up" },
          },
          {
            x: drawdownCurve.map((p) => p.date),
            y: drawdownCurve.map((p) => p.drawdown_pct),
            type: "scatter",
            mode: "lines",
            name: "Drawdown",
            xaxis: "x",
            yaxis: "y2",
            fill: "tozeroy",
            line: { color: "#c5221f" },
          },
        ]}
        layout={{
          autosize: true,
          height: 440,
          margin: { t: 10, r: 20, l: 60, b: 40 },
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          font: plotlyFont(isDark),
          legend: { orientation: "h", y: -0.15 },
          xaxis: { gridcolor: plotlyGridColor(isDark), title: { text: "Date" } },
          yaxis: {
            domain: [0.35, 1],
            gridcolor: plotlyGridColor(isDark),
            title: { text: "Portfolio value ($)" },
          },
          yaxis2: {
            domain: [0, 0.27],
            gridcolor: plotlyGridColor(isDark),
            title: { text: "Drawdown (%)" },
          },
        }}
        config={PLOTLY_CONFIG}
        useResizeHandler
        style={{ width: "100%" }}
      />
    </Card>
  );
}
