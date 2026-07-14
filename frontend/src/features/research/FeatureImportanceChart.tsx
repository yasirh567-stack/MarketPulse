import { Card } from "@/components/Card";
import { Plot, PLOTLY_CONFIG, plotlyFont, plotlyGridColor } from "@/components/Plot";
import { useTheme } from "@/hooks/useTheme";
import { EmptyState } from "@/components/StateViews";
import type { FeatureImportanceEntry } from "@/types/api";

export function FeatureImportanceChart({
  entries,
  valueKey,
  title,
}: {
  entries: FeatureImportanceEntry[] | null | undefined;
  valueKey: "importance" | "coefficient" | "mean_abs_shap";
  title: string;
}) {
  const [theme] = useTheme();
  const isDark = theme === "dark";

  if (!entries || entries.length === 0) {
    return (
      <Card title={title}>
        <EmptyState
          title="Not available"
          description={
            valueKey === "mean_abs_shap"
              ? "SHAP is an optional enhancement and isn't installed in this environment — permutation importance above is the default explanation method."
              : "No data for this view."
          }
        />
      </Card>
    );
  }

  const sorted = [...entries].reverse();

  return (
    <Card title={title}>
      <Plot
        data={[
          {
            x: sorted.map((e) => e[valueKey] ?? 0),
            y: sorted.map((e) => e.feature),
            type: "bar",
            orientation: "h",
            marker: { color: "#0ea5e9" },
          },
        ]}
        layout={{
          autosize: true,
          height: 32 * sorted.length + 60,
          margin: { t: 10, r: 20, l: 150, b: 40 },
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          font: plotlyFont(isDark),
          xaxis: { gridcolor: plotlyGridColor(isDark), title: { text: title } },
          yaxis: { automargin: true },
        }}
        config={PLOTLY_CONFIG}
        useResizeHandler
        style={{ width: "100%" }}
      />
    </Card>
  );
}
