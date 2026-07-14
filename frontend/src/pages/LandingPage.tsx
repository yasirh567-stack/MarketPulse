import { Link } from "react-router-dom";

const FEATURES = [
  {
    title: "Market overview & charts",
    body: "Interactive price, volume, and sentiment charts for any tracked ticker, always labeled live/delayed/historical/cached/demo.",
  },
  {
    title: "News & sentiment",
    body: "Recent headlines scored by VADER (with optional FinBERT comparison), aggregated bullish/neutral/bearish over time.",
  },
  {
    title: "Explainable predictions",
    body: "A walk-forward-validated model estimates next-day direction, with permutation-importance explanations — never a black box.",
  },
  {
    title: "Honest backtesting",
    body: "A sentiment+probability strategy backtested against buy-and-hold, with transaction costs, drawdown, and hypothetical-results warnings.",
  },
  {
    title: "Evidence-based assistant",
    body: "Ask 'why is this stock moving?' and get a deterministic, cited answer built from retrieved headlines — no generative hallucination.",
  },
  {
    title: "Full transparency",
    body: "A dedicated status page shows exactly which data sources and models are active, and what live/demo/cached actually mean.",
  },
];

const TECH_BADGES = [
  "React",
  "TypeScript",
  "FastAPI",
  "SQLAlchemy",
  "scikit-learn",
  "VADER",
  "FinBERT (optional)",
  "Plotly",
  "WebSockets",
  "SQLite/PostgreSQL",
];

export function LandingPage() {
  return (
    <div className="space-y-16">
      <section className="mx-auto max-w-3xl text-center">
        <span className="mb-4 inline-block rounded-full bg-violet-100 px-3 py-1 text-xs font-semibold text-violet-800 dark:bg-violet-950 dark:text-violet-400">
          Educational portfolio project — not financial advice
        </span>
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
          Real-time stock sentiment &amp; market intelligence
        </h1>
        <p className="mt-4 text-lg text-slate-600 dark:text-slate-300">
          MarketPulse AI combines market data, financial news, NLP sentiment, explainable machine
          learning, and rigorous backtesting into one transparent research dashboard — runnable
          entirely for free, with a full demo mode that needs zero API keys.
        </p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <Link
            to="/dashboard"
            className="rounded-lg bg-slate-900 px-6 py-3 text-sm font-semibold text-white hover:bg-slate-700 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-200"
          >
            Launch Dashboard
          </Link>
          <Link
            to="/status"
            className="rounded-lg border border-slate-300 px-6 py-3 text-sm font-semibold hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
          >
            View data &amp; model status
          </Link>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map((f) => (
          <div
            key={f.title}
            className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"
          >
            <h2 className="font-semibold">{f.title}</h2>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{f.body}</p>
          </div>
        ))}
      </section>

      <section className="mx-auto max-w-3xl rounded-xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-200">
        <h2 className="font-semibold">What this is — and isn't</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5">
          <li>
            All predictions and backtests are research estimates on limited historical/demo data —
            they do not guarantee any future outcome.
          </li>
          <li>
            "Real-time" means a polling interval suited to free data sources, not sub-second ticks.
            Every figure is labeled live, delayed, historical, cached, or demo.
          </li>
          <li>Nothing in this application is financial advice.</li>
        </ul>
      </section>

      <section className="text-center">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
          Built with
        </h2>
        <div className="mt-3 flex flex-wrap items-center justify-center gap-2">
          {TECH_BADGES.map((t) => (
            <span
              key={t}
              className="rounded-full border border-slate-300 px-3 py-1 text-xs text-slate-600 dark:border-slate-700 dark:text-slate-300"
            >
              {t}
            </span>
          ))}
        </div>
      </section>
    </div>
  );
}
