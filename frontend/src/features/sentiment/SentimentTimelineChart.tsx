import { useMemo } from "react";
import { Card } from "@/components/Card";
import { Plot, PLOTLY_CONFIG, plotlyFont, plotlyGridColor } from "@/components/Plot";
import { Tooltip } from "@/components/Tooltip";
import { useTheme } from "@/hooks/useTheme";
import { EmptyState } from "@/components/StateViews";
import type { SentimentTimelinePoint } from "@/types/api";

export function SentimentTimelineChart({
  timeline,
  activeModel,
}: {
  timeline: SentimentTimelinePoint[];
  activeModel: string;
}) {
  const [theme] = useTheme();
  const isDark = theme === "dark";

  const summary = useMemo(() => {
    if (timeline.length === 0) return "No sentiment history available.";
    const avg = timeline.reduce((s, p) => s + p.avg_compound, 0) / timeline.length;
    return `Daily average sentiment compound score over ${timeline.length} days, averaging ${avg.toFixed(2)} on a -1 (bearish) to +1 (bullish) scale, scored by ${activeModel}.`;
  }, [timeline, activeModel]);

  return (
    <Card
      title={
        <span className="flex items-center gap-1.5">
          Sentiment over time
          <Tooltip label="What is the compound score?">
            A -1 (very bearish) to +1 (very bullish) score aggregating {activeModel}-scored
            headlines each day.
          </Tooltip>
        </span>
      }
    >
      {timeline.length === 0 ? (
        <EmptyState title="No sentiment data yet" />
      ) : (
        <div>
          <p className="sr-only">{summary}</p>
          <Plot
            data={[
              {
                x: timeline.map((p) => p.date),
                y: timeline.map((p) => p.avg_compound),
                type: "scatter",
                mode: "lines+markers",
                name: "Avg. compound sentiment",
                line: { color: "#0ea5e9" },
              },
            ]}
            layout={{
              autosize: true,
              height: 260,
              margin: { t: 10, r: 20, l: 50, b: 40 },
              paper_bgcolor: "transparent",
              plot_bgcolor: "transparent",
              font: plotlyFont(isDark),
              xaxis: { gridcolor: plotlyGridColor(isDark), title: { text: "Date" } },
              yaxis: {
                gridcolor: plotlyGridColor(isDark),
                title: { text: "Compound score" },
                range: [-1, 1],
                zeroline: true,
              },
            }}
            config={PLOTLY_CONFIG}
            useResizeHandler
            style={{ width: "100%" }}
          />
        </div>
      )}
    </Card>
  );
}
