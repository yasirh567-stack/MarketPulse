import { Card } from "@/components/Card";
import { Plot, PLOTLY_CONFIG, plotlyFont, plotlyGridColor } from "@/components/Plot";
import { useTheme } from "@/hooks/useTheme";
import { EmptyState } from "@/components/StateViews";
import type { SentimentTimelinePoint } from "@/types/api";

export function MentionVolumeChart({ timeline }: { timeline: SentimentTimelinePoint[] }) {
  const [theme] = useTheme();
  const isDark = theme === "dark";

  if (timeline.length === 0) {
    return (
      <Card title="Bullish / neutral / bearish mentions">
        <EmptyState title="No mention data yet" />
      </Card>
    );
  }

  return (
    <Card title="Bullish / neutral / bearish mentions">
      <p className="sr-only">
        Stacked bar chart of daily article/mention counts split into bullish, neutral, and bearish
        categories, not relying on color alone (see legend).
      </p>
      <Plot
        data={[
          {
            x: timeline.map((p) => p.date),
            y: timeline.map((p) => p.bullish_count),
            type: "bar",
            name: "Bullish ▲",
            marker: { color: "#0f9d58" },
          },
          {
            x: timeline.map((p) => p.date),
            y: timeline.map((p) => p.neutral_count),
            type: "bar",
            name: "Neutral ●",
            marker: { color: "#94a3b8" },
          },
          {
            x: timeline.map((p) => p.date),
            y: timeline.map((p) => p.bearish_count),
            type: "bar",
            name: "Bearish ▼",
            marker: { color: "#c5221f" },
          },
        ]}
        layout={{
          autosize: true,
          height: 260,
          barmode: "stack",
          margin: { t: 10, r: 20, l: 50, b: 40 },
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          font: plotlyFont(isDark),
          legend: { orientation: "h", y: -0.25 },
          xaxis: { gridcolor: plotlyGridColor(isDark), title: { text: "Date" } },
          yaxis: { gridcolor: plotlyGridColor(isDark), title: { text: "Article count" } },
        }}
        config={PLOTLY_CONFIG}
        useResizeHandler
        style={{ width: "100%" }}
      />
    </Card>
  );
}
