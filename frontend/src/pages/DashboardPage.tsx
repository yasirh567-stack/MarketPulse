import { useState } from "react";
import { useSelectedTicker } from "@/hooks/useSelectedTicker";
import { useEvents, useHistory, useNews, usePrediction, useQuote, useSentiment } from "@/api/hooks";
import { WatchlistSidebar } from "@/features/watchlist/WatchlistSidebar";
import { OverviewCards } from "@/features/market/OverviewCards";
import { PriceVolumeChart } from "@/features/market/PriceVolumeChart";
import { NewsFeed } from "@/features/news/NewsFeed";
import { EventsPanel } from "@/features/events/EventsPanel";
import { SentimentTimelineChart } from "@/features/sentiment/SentimentTimelineChart";
import { MentionVolumeChart } from "@/features/sentiment/MentionVolumeChart";
import { SourceComparisonTable } from "@/features/sentiment/SourceComparisonTable";
import { PredictionCard } from "@/features/predictions/PredictionCard";
import { Card } from "@/components/Card";
import { ErrorState, SkeletonBlock } from "@/components/StateViews";

const PERIOD_OPTIONS = [
  { label: "1M", days: 30 },
  { label: "3M", days: 90 },
  { label: "6M", days: 180 },
  { label: "1Y", days: 365 },
];

export function DashboardPage() {
  const { ticker } = useSelectedTicker();
  const [periodDays, setPeriodDays] = useState(180);

  const quoteQuery = useQuote(ticker);
  const historyQuery = useHistory(ticker, periodDays);
  const newsQuery = useNews(ticker, 1, 8);
  const sentimentQuery = useSentiment(ticker, 30);
  const eventsQuery = useEvents(ticker);
  const predictionQuery = usePrediction(ticker);

  return (
    <div className="flex flex-col gap-6 lg:flex-row">
      <WatchlistSidebar />

      <div className="min-w-0 flex-1 space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h1 className="text-2xl font-bold">{ticker}</h1>
          <div
            className="flex gap-1 rounded-md border border-slate-200 p-1 dark:border-slate-800"
            role="group"
            aria-label="Chart period"
          >
            {PERIOD_OPTIONS.map((opt) => (
              <button
                key={opt.label}
                onClick={() => setPeriodDays(opt.days)}
                aria-pressed={periodDays === opt.days}
                className={`rounded px-2.5 py-1 text-xs font-medium ${
                  periodDays === opt.days
                    ? "bg-slate-900 text-white dark:bg-white dark:text-slate-900"
                    : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {quoteQuery.isLoading && <SkeletonBlock lines={2} />}
        {quoteQuery.isError && (
          <ErrorState
            title="Couldn't load quote"
            description={(quoteQuery.error as Error)?.message}
            onRetry={() => quoteQuery.refetch()}
          />
        )}
        {quoteQuery.data && <OverviewCards quote={quoteQuery.data} />}

        <Card title="Price & volume">
          {historyQuery.isLoading && <SkeletonBlock lines={6} />}
          {historyQuery.isError && (
            <ErrorState
              title="Couldn't load price history"
              onRetry={() => historyQuery.refetch()}
            />
          )}
          {historyQuery.data && <PriceVolumeChart history={historyQuery.data} />}
        </Card>

        <div className="grid gap-6 lg:grid-cols-2">
          {sentimentQuery.isLoading && <SkeletonBlock lines={5} />}
          {sentimentQuery.data && (
            <SentimentTimelineChart
              timeline={sentimentQuery.data.timeline}
              activeModel={sentimentQuery.data.active_model}
            />
          )}
          {sentimentQuery.data && <MentionVolumeChart timeline={sentimentQuery.data.timeline} />}
        </div>

        {sentimentQuery.data && (
          <SourceComparisonTable
            bySourceType={sentimentQuery.data.by_source_type}
            byModel={sentimentQuery.data.by_model}
          />
        )}

        {predictionQuery.isLoading && (
          <Card title="Next-day direction estimate">
            <SkeletonBlock lines={4} />
          </Card>
        )}
        {predictionQuery.isError && (
          <Card title="Next-day direction estimate">
            <ErrorState
              title="Prediction unavailable"
              description={(predictionQuery.error as Error)?.message}
              onRetry={() => predictionQuery.refetch()}
            />
          </Card>
        )}
        {predictionQuery.data && <PredictionCard prediction={predictionQuery.data} />}

        <div className="grid gap-6 lg:grid-cols-2">
          {newsQuery.isLoading && (
            <Card title="Recent news">
              <SkeletonBlock lines={5} />
            </Card>
          )}
          {newsQuery.data && <NewsFeed articles={newsQuery.data.articles} />}

          {eventsQuery.isLoading && (
            <Card title="Detected events">
              <SkeletonBlock lines={5} />
            </Card>
          )}
          {eventsQuery.data && (
            <EventsPanel
              events={eventsQuery.data.events}
              disclaimer={eventsQuery.data.disclaimer}
            />
          )}
        </div>
      </div>
    </div>
  );
}
