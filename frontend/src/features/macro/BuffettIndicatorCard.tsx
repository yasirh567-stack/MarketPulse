import { useMemo } from "react";
import { Card } from "@/components/Card";
import { DataStatusBadge } from "@/components/DataStatusBadge";
import { Tooltip } from "@/components/Tooltip";
import { ErrorState, SkeletonBlock } from "@/components/StateViews";
import { Plot, PLOTLY_CONFIG, plotlyFont, plotlyGridColor } from "@/components/Plot";
import { useTheme } from "@/hooks/useTheme";
import { useBuffettIndicator } from "@/api/hooks";

export function BuffettIndicatorCard() {
  const { data, isLoading, isError, error, refetch } = useBuffettIndicator();
  const [theme] = useTheme();
  const isDark = theme === "dark";

  const summary = useMemo(() => {
    if (!data) return "";
    return (
      `Market-cap-to-GDP ("Buffett Indicator") over time, currently ${data.current_ratio_pct.toFixed(1)}%, ` +
      `at the ${data.percentile_rank.toFixed(0)}th percentile of its own history in this dataset.`
    );
  }, [data]);

  return (
    <Card
      title={
        <span className="flex items-center gap-1.5">
          Market valuation: Buffett Indicator
          <Tooltip label="What is this?">
            Total US stock market value divided by GDP — a market-wide valuation gauge Warren
            Buffett has cited, not a per-stock or short-term signal.
          </Tooltip>
        </span>
      }
      action={data && <DataStatusBadge status={data.data_status} />}
    >
      {isLoading && <SkeletonBlock lines={5} />}
      {isError && (
        <ErrorState
          title="Couldn't load the Buffett Indicator"
          description={(error as Error)?.message}
          onRetry={() => refetch()}
        />
      )}
      {data && (
        <div>
          <div className="flex flex-wrap items-baseline gap-4">
            <p className="text-3xl font-bold tabular-nums">{data.current_ratio_pct.toFixed(1)}%</p>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              {data.percentile_rank.toFixed(0)}th percentile historically · as of{" "}
              {new Date(data.as_of).toLocaleDateString()}
            </p>
          </div>
          <p className="mt-2 text-sm text-slate-700 dark:text-slate-300">{data.interpretation}</p>

          <p className="sr-only">{summary}</p>
          <Plot
            data={[
              {
                x: data.historical.map((p) => p.quarter_end),
                y: data.historical.map((p) => p.ratio_pct),
                type: "scatter",
                mode: "lines",
                name: "Market cap / GDP",
                line: { color: "#0ea5e9" },
              },
            ]}
            layout={{
              autosize: true,
              height: 220,
              margin: { t: 10, r: 20, l: 50, b: 40 },
              paper_bgcolor: "transparent",
              plot_bgcolor: "transparent",
              font: plotlyFont(isDark),
              xaxis: { gridcolor: plotlyGridColor(isDark), title: { text: "Quarter" } },
              yaxis: { gridcolor: plotlyGridColor(isDark), title: { text: "Ratio (%)" } },
            }}
            config={PLOTLY_CONFIG}
            useResizeHandler
            style={{ width: "100%" }}
          />

          <p className="mt-2 text-xs text-slate-400">{data.methodology_note}</p>
          <p className="mt-1 text-xs italic text-slate-400">{data.disclaimer}</p>
        </div>
      )}
    </Card>
  );
}
