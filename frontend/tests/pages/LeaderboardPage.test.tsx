import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../testUtils";
import { LeaderboardPage } from "@/pages/LeaderboardPage";
import { api } from "@/api/endpoints";

vi.mock("@/api/endpoints", () => ({
  api: {
    leaderboard: vi.fn(),
  },
}));

describe("LeaderboardPage", () => {
  it("renders entries once the leaderboard loads (success state)", async () => {
    vi.mocked(api.leaderboard).mockResolvedValue({
      entries: [
        {
          ticker: "AAPL",
          model_name: "gradient_boosting",
          trained_at: new Date().toISOString(),
          n_train_samples: 200,
          accuracy: 0.6,
          balanced_accuracy: 0.58,
          roc_auc: 0.6,
          brier_score: 0.24,
          baseline_majority_balanced_accuracy: 0.5,
          baseline_previous_direction_balanced_accuracy: 0.52,
          beats_baseline: true,
          status: "ok",
          note: null,
        },
      ],
      disclaimer: "disclaimer text",
    });

    renderWithProviders(<LeaderboardPage />);

    expect(await screen.findByText("AAPL")).toBeInTheDocument();
    expect(await screen.findByText("Beats baseline")).toBeInTheDocument();
  });

  it("shows a per-row note for a ticker with insufficient data, without hiding the others", async () => {
    vi.mocked(api.leaderboard).mockResolvedValue({
      entries: [
        {
          ticker: "AAPL",
          model_name: "gradient_boosting",
          trained_at: new Date().toISOString(),
          n_train_samples: 200,
          accuracy: 0.6,
          balanced_accuracy: 0.58,
          roc_auc: 0.6,
          brier_score: 0.24,
          baseline_majority_balanced_accuracy: 0.5,
          baseline_previous_direction_balanced_accuracy: 0.52,
          beats_baseline: true,
          status: "ok",
          note: null,
        },
        {
          ticker: "ZZZNOPE",
          model_name: "gradient_boosting",
          trained_at: null,
          n_train_samples: null,
          accuracy: null,
          balanced_accuracy: null,
          roc_auc: null,
          brier_score: null,
          baseline_majority_balanced_accuracy: null,
          baseline_previous_direction_balanced_accuracy: null,
          beats_baseline: false,
          status: "insufficient_data",
          note: "not enough history",
        },
      ],
      disclaimer: "disclaimer text",
    });

    renderWithProviders(<LeaderboardPage />);

    expect(await screen.findByText("AAPL")).toBeInTheDocument();
    expect(await screen.findByText("ZZZNOPE")).toBeInTheDocument();
    expect(await screen.findByText(/insufficient data/i)).toBeInTheDocument();
  });

  it("shows an error state when the request fails", async () => {
    vi.mocked(api.leaderboard).mockRejectedValue(new Error("Leaderboard unavailable"));

    renderWithProviders(<LeaderboardPage />);

    expect(await screen.findByText(/couldn't load the leaderboard/i)).toBeInTheDocument();
  });
});
