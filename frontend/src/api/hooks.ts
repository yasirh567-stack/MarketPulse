import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/endpoints";
import type { BacktestConfigInput, ThresholdSweepRequest } from "@/types/api";

// TanStack Query passes an AbortSignal via the query function context, which
// we forward into fetch — this is what makes "cancel obsolete requests" (e.g.
// rapid ticker switches) work for free instead of needing manual bookkeeping.

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: ({ signal }) => api.health(signal),
    refetchInterval: 30_000,
  });
}

export function useBuffettIndicator() {
  return useQuery({
    queryKey: ["buffett-indicator"],
    queryFn: ({ signal }) => api.buffettIndicator(signal),
    staleTime: 60 * 60_000, // updates at most every few hours server-side; no need to poll often
  });
}

export function useInstrumentSearch(query: string) {
  return useQuery({
    queryKey: ["instrument-search", query],
    queryFn: ({ signal }) => api.searchInstruments(query, signal),
    enabled: query.trim().length > 0,
    staleTime: 60_000,
  });
}

export function useScreener(tickers?: string[]) {
  return useQuery({
    queryKey: ["screener", tickers?.join(",") ?? "default"],
    queryFn: ({ signal }) => api.screener(tickers, signal),
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
}

export function useQuote(ticker: string) {
  return useQuery({
    queryKey: ["quote", ticker],
    queryFn: ({ signal }) => api.quote(ticker, signal),
    enabled: Boolean(ticker),
    staleTime: 15_000,
    refetchInterval: 30_000,
  });
}

export function useHistory(ticker: string, periodDays: number) {
  return useQuery({
    queryKey: ["history", ticker, periodDays],
    queryFn: ({ signal }) => api.history(ticker, periodDays, signal),
    enabled: Boolean(ticker),
    staleTime: 60_000,
  });
}

export function useNews(ticker: string, page: number, pageSize = 8) {
  return useQuery({
    queryKey: ["news", ticker, page, pageSize],
    queryFn: ({ signal }) => api.news(ticker, page, pageSize, signal),
    enabled: Boolean(ticker),
    staleTime: 60_000,
  });
}

export function useSentiment(ticker: string, windowDays = 30) {
  return useQuery({
    queryKey: ["sentiment", ticker, windowDays],
    queryFn: ({ signal }) => api.sentiment(ticker, windowDays, signal),
    enabled: Boolean(ticker),
    staleTime: 60_000,
  });
}

export function useEvents(ticker: string) {
  return useQuery({
    queryKey: ["events", ticker],
    queryFn: ({ signal }) => api.events(ticker, signal),
    enabled: Boolean(ticker),
    staleTime: 60_000,
  });
}

export function usePrediction(ticker: string) {
  return useQuery({
    queryKey: ["prediction", ticker],
    queryFn: ({ signal }) => api.prediction(ticker, signal),
    enabled: Boolean(ticker),
    staleTime: 5 * 60_000,
    retry: false, // training can legitimately fail with "insufficient data" — don't retry that
  });
}

export function useModelMetrics(ticker: string) {
  return useQuery({
    queryKey: ["model-metrics", ticker],
    queryFn: ({ signal }) => api.modelMetrics(ticker, signal),
    enabled: Boolean(ticker),
    staleTime: 5 * 60_000,
    retry: false,
  });
}

export function useRunBacktest() {
  return useMutation({
    mutationFn: (config: BacktestConfigInput) => api.runBacktest(config),
  });
}

export function useThresholdSweep() {
  return useMutation({
    mutationFn: (config: ThresholdSweepRequest) => api.runThresholdSweep(config),
  });
}

export function useLeaderboard(tickers?: string[], modelName?: string) {
  return useQuery({
    queryKey: ["leaderboard", tickers?.join(",") ?? "default", modelName ?? "default"],
    queryFn: ({ signal }) => api.leaderboard(tickers, modelName, signal),
    staleTime: 5 * 60_000,
    retry: false, // a cold leaderboard call already retrains several models; don't triple that cost on failure
  });
}

export function useAssistantQuery() {
  return useMutation({
    mutationFn: ({ ticker, question }: { ticker: string; question: string }) =>
      api.askAssistant(ticker, question),
  });
}

export function useWatchlist(watchlistId: string) {
  return useQuery({
    queryKey: ["watchlist", watchlistId],
    queryFn: ({ signal }) => api.getWatchlist(watchlistId, signal),
    enabled: Boolean(watchlistId),
    staleTime: 30_000,
  });
}

export function useAddWatchlistItem(watchlistId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (ticker: string) => api.addWatchlistItem(watchlistId, ticker),
    onSuccess: (data) => {
      queryClient.setQueryData(["watchlist", watchlistId], data);
    },
  });
}

export function useRemoveWatchlistItem(watchlistId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (ticker: string) => api.removeWatchlistItem(watchlistId, ticker),
    onSuccess: (data) => {
      queryClient.setQueryData(["watchlist", watchlistId], data);
    },
  });
}
