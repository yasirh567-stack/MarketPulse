import { describe, expect, it, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../testUtils";
import { BuffettIndicatorCard } from "@/features/macro/BuffettIndicatorCard";
import { api } from "@/api/endpoints";

vi.mock("@/api/endpoints", () => ({
  api: {
    buffettIndicator: vi.fn(),
  },
}));

describe("BuffettIndicatorCard", () => {
  beforeEach(() => {
    vi.mocked(api.buffettIndicator).mockReset();
  });

  it("renders the current ratio, percentile, and interpretation once loaded", async () => {
    vi.mocked(api.buffettIndicator).mockResolvedValue({
      current_ratio_pct: 195.3,
      as_of: new Date().toISOString(),
      data_status: "demo",
      source: "demo",
      percentile_rank: 92,
      interpretation: "The current ratio is higher than about 92% of its own history.",
      historical: [
        { quarter_end: "2025-01-01", ratio_pct: 180.2 },
        { quarter_end: "2026-01-01", ratio_pct: 195.3 },
      ],
      methodology_note: "Approximated as Wilshire 5000 / GDP.",
      disclaimer: "Not financial advice.",
    });

    renderWithProviders(<BuffettIndicatorCard />);

    expect(await screen.findByText("195.3%")).toBeInTheDocument();
    expect(screen.getByText(/92% of its own history/)).toBeInTheDocument();
    expect(screen.getByText("Demo")).toBeInTheDocument();
  });

  it("shows an error state when the request fails", async () => {
    vi.mocked(api.buffettIndicator).mockRejectedValue(new Error("FRED unavailable"));

    renderWithProviders(<BuffettIndicatorCard />);

    expect(await screen.findByText(/couldn't load the buffett indicator/i)).toBeInTheDocument();
  });
});
