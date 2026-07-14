import { apiFetch } from "@/api/client";
import type {
  AssistantQueryResponse,
  BacktestConfigInput,
  BacktestResponse,
  BuffettIndicatorResponse,
  EventsListResponse,
  HealthResponse,
  HistoryResponse,
  InstrumentSearchResult,
  LeaderboardResponse,
  ModelMetricsResponse,
  NewsListResponse,
  PredictionResponse,
  QuoteResponse,
  ScreenerResponse,
  SentimentResponse,
  ThresholdSweepRequest,
  ThresholdSweepResponse,
  WatchlistResponse,
} from "@/types/api";

export const api = {
  health: (signal?: AbortSignal) => apiFetch<HealthResponse>("/api/v1/health", { signal }),

  buffettIndicator: (signal?: AbortSignal) =>
    apiFetch<BuffettIndicatorResponse>("/api/v1/macro/buffett-indicator", { signal }),

  searchInstruments: (q: string, signal?: AbortSignal) =>
    apiFetch<InstrumentSearchResult[]>("/api/v1/instruments/search", {
      params: { q },
      signal,
    }),

  screener: (tickers?: string[], signal?: AbortSignal) =>
    apiFetch<ScreenerResponse>("/api/v1/instruments/screener", {
      params: tickers ? { tickers: tickers.join(",") } : undefined,
      signal,
    }),

  quote: (ticker: string, signal?: AbortSignal) =>
    apiFetch<QuoteResponse>(`/api/v1/market/${ticker}/quote`, { signal }),

  history: (ticker: string, periodDays: number, signal?: AbortSignal) =>
    apiFetch<HistoryResponse>(`/api/v1/market/${ticker}/history`, {
      params: { period_days: periodDays, interval: "1d" },
      signal,
    }),

  news: (ticker: string, page: number, pageSize: number, signal?: AbortSignal) =>
    apiFetch<NewsListResponse>(`/api/v1/news/${ticker}`, {
      params: { page, page_size: pageSize },
      signal,
    }),

  sentiment: (ticker: string, windowDays: number, signal?: AbortSignal) =>
    apiFetch<SentimentResponse>(`/api/v1/sentiment/${ticker}`, {
      params: { window_days: windowDays },
      signal,
    }),

  events: (ticker: string, signal?: AbortSignal) =>
    apiFetch<EventsListResponse>(`/api/v1/events/${ticker}`, { signal }),

  prediction: (ticker: string, signal?: AbortSignal) =>
    apiFetch<PredictionResponse>(`/api/v1/predictions/${ticker}`, { signal }),

  modelMetrics: (ticker: string, signal?: AbortSignal) =>
    apiFetch<ModelMetricsResponse>(`/api/v1/models/${ticker}/latest`, { signal }),

  runBacktest: (config: BacktestConfigInput, signal?: AbortSignal) =>
    apiFetch<BacktestResponse>("/api/v1/backtests", { method: "POST", body: config, signal }),

  getBacktest: (runId: number, signal?: AbortSignal) =>
    apiFetch<BacktestResponse>(`/api/v1/backtests/${runId}`, { signal }),

  runThresholdSweep: (config: ThresholdSweepRequest, signal?: AbortSignal) =>
    apiFetch<ThresholdSweepResponse>("/api/v1/backtests/threshold-sweep", {
      method: "POST",
      body: config,
      signal,
    }),

  leaderboard: (tickers?: string[], modelName?: string, signal?: AbortSignal) =>
    apiFetch<LeaderboardResponse>("/api/v1/leaderboard", {
      params: {
        ...(tickers ? { tickers: tickers.join(",") } : {}),
        ...(modelName ? { model_name: modelName } : {}),
      },
      signal,
    }),

  askAssistant: (ticker: string, question: string, signal?: AbortSignal) =>
    apiFetch<AssistantQueryResponse>("/api/v1/assistant/query", {
      method: "POST",
      body: { ticker, question },
      signal,
    }),

  getWatchlist: (watchlistId: string, signal?: AbortSignal) =>
    apiFetch<WatchlistResponse>(`/api/v1/watchlists/${watchlistId}`, { signal }),

  addWatchlistItem: (watchlistId: string, ticker: string) =>
    apiFetch<WatchlistResponse>(`/api/v1/watchlists/${watchlistId}/items`, {
      method: "POST",
      body: { ticker },
    }),

  removeWatchlistItem: (watchlistId: string, ticker: string) =>
    apiFetch<WatchlistResponse>(`/api/v1/watchlists/${watchlistId}/items/${ticker}`, {
      method: "DELETE",
    }),
};
