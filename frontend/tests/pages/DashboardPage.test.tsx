import { describe, expect, it, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../testUtils";
import { DashboardPage } from "@/pages/DashboardPage";
import { api } from "@/api/endpoints";

vi.mock("@/api/endpoints", () => ({
  api: {
    getWatchlist: vi.fn(),
    addWatchlistItem: vi.fn(),
    removeWatchlistItem: vi.fn(),
    searchInstruments: vi.fn(),
    screener: vi.fn(),
    quote: vi.fn(),
    history: vi.fn(),
    news: vi.fn(),
    sentiment: vi.fn(),
    events: vi.fn(),
    prediction: vi.fn(),
  },
}));

const EMPTY_WATCHLIST = { watchlist_id: 1, owner_key: "anon-test", items: [] };
const EMPTY_SCREENER = { entries: [], disclaimer: "" };

function mockAllHappyPath() {
  vi.mocked(api.getWatchlist).mockResolvedValue(EMPTY_WATCHLIST);
  vi.mocked(api.screener).mockResolvedValue(EMPTY_SCREENER);
  vi.mocked(api.quote).mockResolvedValue({
    ticker: "AAPL",
    name: null,
    price: 284.42,
    previous_close: 278.42,
    change_abs: 6.0,
    change_pct: 2.15,
    currency: "USD",
    market_status: "closed",
    as_of: new Date().toISOString(),
    data_status: "demo",
    source: "demo",
  });
  vi.mocked(api.history).mockResolvedValue({
    ticker: "AAPL",
    interval: "1d",
    data_status: "demo",
    source: "demo",
    bars: [
      {
        ts: new Date().toISOString(),
        open: 280,
        high: 285,
        low: 279,
        close: 284,
        adj_close: 284,
        volume: 1_000_000,
      },
    ],
  });
  vi.mocked(api.news).mockResolvedValue({
    ticker: "AAPL",
    total: 0,
    page: 1,
    page_size: 8,
    articles: [],
  });
  vi.mocked(api.sentiment).mockResolvedValue({
    ticker: "AAPL",
    active_model: "vader",
    timeline: [],
    by_source_type: {},
    by_model: {},
  });
  vi.mocked(api.events).mockResolvedValue({
    ticker: "AAPL",
    events: [],
    disclaimer: "disclaimer text",
  });
  vi.mocked(api.prediction).mockResolvedValue({
    ticker: "AAPL",
    model_name: "gradient_boosting",
    predicted_direction: "up",
    probability_up: 0.62,
    confidence_label: "moderate",
    as_of_date: new Date().toISOString(),
    trained_at: new Date().toISOString(),
    train_start: new Date().toISOString(),
    train_end: new Date().toISOString(),
    n_train_samples: 200,
    top_features: [{ feature: "volatility_10", importance: 0.1 }],
    sentiment_shift_note: null,
    limitations: ["Not financial advice."],
  });
}

describe("DashboardPage", () => {
  beforeEach(() => {
    Object.values(api).forEach((fn) => {
      if (vi.isMockFunction(fn)) fn.mockReset();
    });
  });

  it("renders the overview and prediction once data loads (success state)", async () => {
    mockAllHappyPath();
    renderWithProviders(<DashboardPage />);

    expect(await screen.findByText("284.42")).toBeInTheDocument();
    expect(await screen.findByText(/next-day direction estimate/i)).toBeInTheDocument();
    expect(await screen.findByText("Up")).toBeInTheDocument();
  });

  it("shows an empty state for news when there are no articles", async () => {
    mockAllHappyPath();
    renderWithProviders(<DashboardPage />);

    expect(await screen.findByText(/no recent headlines/i)).toBeInTheDocument();
  });

  it("shows an error state when the quote request fails", async () => {
    mockAllHappyPath();
    vi.mocked(api.quote).mockRejectedValue(new Error("Quote service unavailable"));

    renderWithProviders(<DashboardPage />);

    expect(await screen.findByText(/couldn't load quote/i)).toBeInTheDocument();
  });
});
