// Wires react-plotly.js to the smaller `plotly.js-dist-min` build (rather
// than the full plotly.js, which bundles chart types this app never uses)
// to keep the production bundle leaner.
import Plotly from "plotly.js-dist-min";
import createPlotlyComponent from "react-plotly.js/factory";
import type { Config } from "plotly.js";

export const Plot = createPlotlyComponent(Plotly);

export const PLOTLY_CONFIG: Partial<Config> = {
  displaylogo: false,
  responsive: true,
  modeBarButtonsToRemove: ["lasso2d", "select2d"],
};

export function plotlyFont(isDark: boolean) {
  return {
    color: isDark ? "#cbd5e1" : "#334155",
    family: "Inter, system-ui, sans-serif",
    size: 12,
  };
}

export function plotlyGridColor(isDark: boolean) {
  return isDark ? "#334155" : "#e2e8f0";
}
