import { describe, expect, it, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../testUtils";
import { WatchlistSidebar } from "@/features/watchlist/WatchlistSidebar";
import { api } from "@/api/endpoints";

vi.mock("@/api/endpoints", () => ({
  api: {
    getWatchlist: vi.fn(),
    addWatchlistItem: vi.fn(),
    removeWatchlistItem: vi.fn(),
    searchInstruments: vi.fn(),
    screener: vi.fn(),
  },
}));

describe("WatchlistSidebar", () => {
  beforeEach(() => {
    vi.mocked(api.getWatchlist).mockReset();
    vi.mocked(api.addWatchlistItem).mockReset();
    vi.mocked(api.removeWatchlistItem).mockReset();
    vi.mocked(api.searchInstruments).mockReset();
    vi.mocked(api.screener).mockReset();
    vi.mocked(api.screener).mockResolvedValue({ entries: [], disclaimer: "" });
  });

  it("shows an empty state when the watchlist has no items", async () => {
    vi.mocked(api.getWatchlist).mockResolvedValue({
      watchlist_id: 1,
      owner_key: "anon-test",
      items: [],
    });

    renderWithProviders(<WatchlistSidebar />);

    expect(await screen.findByText(/no stocks yet/i)).toBeInTheDocument();
  });

  it("renders existing watchlist items", async () => {
    vi.mocked(api.getWatchlist).mockResolvedValue({
      watchlist_id: 1,
      owner_key: "anon-test",
      items: [{ ticker: "AAPL", added_at: new Date().toISOString() }],
    });
    vi.mocked(api.screener).mockResolvedValue({
      entries: [
        {
          ticker: "AAPL",
          name: "Apple Inc.",
          price: 284.4,
          change_pct: 1.2,
          data_status: "demo",
          avg_sentiment: 0.2,
          sentiment_label: "bullish",
          bullish_mentions: 3,
          bearish_mentions: 0,
          article_count: 5,
        },
      ],
      disclaimer: "",
    });

    renderWithProviders(<WatchlistSidebar />);

    expect(await screen.findByText("AAPL")).toBeInTheDocument();
    expect(await screen.findByText("Bullish")).toBeInTheDocument();
  });

  it("removes an item when the remove button is clicked", async () => {
    vi.mocked(api.getWatchlist).mockResolvedValue({
      watchlist_id: 1,
      owner_key: "anon-test",
      items: [{ ticker: "TSLA", added_at: new Date().toISOString() }],
    });
    vi.mocked(api.removeWatchlistItem).mockResolvedValue({
      watchlist_id: 1,
      owner_key: "anon-test",
      items: [],
    });

    const user = userEvent.setup();
    renderWithProviders(<WatchlistSidebar />);

    const removeButton = await screen.findByRole("button", { name: /remove tsla/i });
    await user.click(removeButton);

    await waitFor(() =>
      expect(api.removeWatchlistItem).toHaveBeenCalledWith(expect.any(String), "TSLA")
    );
  });
});
