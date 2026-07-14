import { useHealth } from "@/api/hooks";
import { Card } from "@/components/Card";
import { DataStatusBadge } from "@/components/DataStatusBadge";
import { ErrorState, SkeletonBlock } from "@/components/StateViews";
import { BuffettIndicatorCard } from "@/features/macro/BuffettIndicatorCard";
import type { DataStatus } from "@/types/api";

const STATUS_EXPLANATIONS: { status: DataStatus; explanation: string }[] = [
  {
    status: "live",
    explanation:
      "Streamed close to real time. Not used in this project's free-tier setup for market data.",
  },
  {
    status: "delayed",
    explanation: "Real quote/history from yfinance, typically delayed ~15 minutes for US equities.",
  },
  {
    status: "historical",
    explanation:
      "Past price bars retrieved from a real provider, not subject to same-day delay concerns.",
  },
  {
    status: "cached",
    explanation:
      "A previously fetched real result served again to avoid hitting provider rate limits.",
  },
  {
    status: "demo",
    explanation:
      "Bundled synthetic/fixture data — clearly labeled, used when DEMO_MODE is on or a provider is unavailable.",
  },
];

const PROVIDER_DESCRIPTIONS: Record<string, string> = {
  market_data: "yfinance (free, unofficial Yahoo Finance data) with demo-fixture fallback.",
  news: "Google News RSS (free, no API key) with demo-fixture fallback.",
};

export function StatusPage() {
  const { data: health, isLoading, isError, error, refetch } = useHealth();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">System status & methodology</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          What's live, what's demo, and which models are actually running right now.
        </p>
      </div>

      {isLoading && (
        <Card>
          <SkeletonBlock lines={5} />
        </Card>
      )}
      {isError && (
        <ErrorState
          title="Couldn't reach the API"
          description={(error as Error)?.message}
          onRetry={() => refetch()}
        />
      )}

      {health && (
        <>
          <Card title="Overall">
            <div className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
              <div>
                <p className="text-slate-500 dark:text-slate-400">API status</p>
                <p className="font-semibold capitalize">{health.status}</p>
              </div>
              <div>
                <p className="text-slate-500 dark:text-slate-400">Database</p>
                <p className="font-semibold">{health.database_ok ? "Connected" : "Unavailable"}</p>
              </div>
              <div>
                <p className="text-slate-500 dark:text-slate-400">Mode</p>
                <p className="font-semibold">{health.demo_mode ? "Demo" : "Live"}</p>
              </div>
              <div>
                <p className="text-slate-500 dark:text-slate-400">Environment</p>
                <p className="font-semibold">{health.environment}</p>
              </div>
            </div>
          </Card>

          <Card title="Active sentiment model">
            <p className="text-sm">
              Currently scoring text with{" "}
              <strong className="capitalize">{health.active_sentiment_model}</strong>.
              {!health.finbert_available && (
                <span className="text-slate-500 dark:text-slate-400">
                  {" "}
                  FinBERT is an optional, heavier upgrade (requires torch/transformers + a one-time
                  model download) — VADER is always available as the guaranteed fallback.
                </span>
              )}
            </p>
          </Card>

          <Card title="Data providers">
            {health.providers.length === 0 ? (
              <p className="text-sm text-slate-500 dark:text-slate-400">
                No provider calls recorded yet this session — visit the Dashboard to populate this.
              </p>
            ) : (
              <ul className="space-y-2">
                {health.providers.map((p) => (
                  <li
                    key={p.name}
                    className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-100 p-3 text-sm dark:border-slate-800"
                  >
                    <div>
                      <p className="font-medium">{p.name}</p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        {PROVIDER_DESCRIPTIONS[p.name] ?? "Optional provider."}
                      </p>
                    </div>
                    <div className="text-right text-xs text-slate-400">
                      <p
                        className={
                          p.status === "ok"
                            ? "text-bullish"
                            : p.status === "degraded"
                              ? "text-amber-600"
                              : "text-bearish"
                        }
                      >
                        {p.status}
                      </p>
                      {p.last_success_at && (
                        <p>Last success: {new Date(p.last_success_at).toLocaleString()}</p>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </>
      )}

      <BuffettIndicatorCard />

      <Card title="What the data-status badges mean">
        <ul className="space-y-2 text-sm">
          {STATUS_EXPLANATIONS.map((item) => (
            <li key={item.status} className="flex items-start gap-3">
              <DataStatusBadge status={item.status} />
              <span className="text-slate-600 dark:text-slate-400">{item.explanation}</span>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
