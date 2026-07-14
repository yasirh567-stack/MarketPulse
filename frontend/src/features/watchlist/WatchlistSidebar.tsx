import { useWatchlistId } from "@/hooks/useWatchlistId";
import { useSelectedTicker } from "@/hooks/useSelectedTicker";
import {
  useAddWatchlistItem,
  useRemoveWatchlistItem,
  useScreener,
  useWatchlist,
} from "@/api/hooks";
import { SentimentBadge } from "@/components/SentimentBadge";
import { EmptyState, SkeletonBlock } from "@/components/StateViews";
import { TickerSearch } from "@/components/TickerSearch";

export function WatchlistSidebar() {
  const watchlistId = useWatchlistId();
  const { ticker: selectedTicker, setTicker: setSelectedTicker } = useSelectedTicker();
  const { data: watchlist, isLoading } = useWatchlist(watchlistId);
  const addItem = useAddWatchlistItem(watchlistId);
  const removeItem = useRemoveWatchlistItem(watchlistId);

  const tickers = watchlist?.items.map((i) => i.ticker) ?? [];
  const { data: screener } = useScreener(tickers.length > 0 ? tickers : undefined);
  const screenerByTicker = new Map((screener?.entries ?? []).map((e) => [e.ticker, e]));

  return (
    <aside className="flex w-full flex-col gap-4 lg:w-72" aria-label="Watchlist">
      <TickerSearch
        onSelect={(ticker) => {
          setSelectedTicker(ticker);
          addItem.mutate(ticker);
        }}
      />
      <div>
        <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
          Watchlist
        </h2>
        {isLoading && <SkeletonBlock lines={3} />}
        {!isLoading && tickers.length === 0 && (
          <EmptyState
            title="No stocks yet"
            description="Search above and select a ticker to add it to your watchlist."
          />
        )}
        <ul className="space-y-1">
          {tickers.map((ticker) => {
            const entry = screenerByTicker.get(ticker);
            const isSelected = ticker === selectedTicker;
            return (
              <li key={ticker}>
                <div
                  className={`group flex items-center justify-between rounded-md px-2 py-1.5 ${
                    isSelected
                      ? "bg-sky-50 dark:bg-sky-950/50"
                      : "hover:bg-slate-50 dark:hover:bg-slate-800/50"
                  }`}
                >
                  <button
                    type="button"
                    onClick={() => setSelectedTicker(ticker)}
                    aria-current={isSelected ? "true" : undefined}
                    className="flex flex-1 items-center justify-between gap-2 text-left text-sm"
                  >
                    <span className="font-semibold">{ticker}</span>
                    <span className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                      {entry ? (
                        <>
                          <span
                            className={
                              (entry.change_pct ?? 0) >= 0
                                ? "text-bullish"
                                : (entry.change_pct ?? 0) < 0
                                  ? "text-bearish"
                                  : ""
                            }
                          >
                            {entry.change_pct !== null
                              ? `${entry.change_pct >= 0 ? "+" : ""}${entry.change_pct.toFixed(2)}%`
                              : "—"}
                          </span>
                          <SentimentBadge label={entry.sentiment_label} />
                        </>
                      ) : (
                        "…"
                      )}
                    </span>
                  </button>
                  <button
                    type="button"
                    onClick={() => removeItem.mutate(ticker)}
                    aria-label={`Remove ${ticker} from watchlist`}
                    className="ml-1 hidden rounded px-1 text-slate-400 hover:bg-slate-200 hover:text-slate-700 group-hover:block dark:hover:bg-slate-700"
                  >
                    ✕
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    </aside>
  );
}
