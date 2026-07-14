import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { ThresholdSweepChart } from "@/features/backtesting/ThresholdSweepChart";
import type { ThresholdSweepPoint } from "@/types/api";

const THRESHOLDS: ThresholdSweepPoint[] = [
  {
    prob_threshold: 0.5,
    sharpe_ratio: 0.42,
    sortino_ratio: 0.5,
    total_return_pct: 3.2,
    win_rate_pct: 55.0,
    num_trades: 12,
    max_drawdown_pct: -8.1,
  },
  {
    prob_threshold: 0.65,
    sharpe_ratio: 0.71,
    sortino_ratio: 0.8,
    total_return_pct: 5.5,
    win_rate_pct: 60.0,
    num_trades: 4,
    max_drawdown_pct: -3.4,
  },
];

describe("ThresholdSweepChart", () => {
  it("renders one table row per threshold with its metrics", () => {
    render(<ThresholdSweepChart thresholds={THRESHOLDS} />);

    expect(screen.getByText("0.50")).toBeInTheDocument();
    expect(screen.getByText("0.65")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
  });
});
