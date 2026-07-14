import { Card } from "@/components/Card";
import { DataStatusBadge } from "@/components/DataStatusBadge";
import { useMarketSocket } from "@/hooks/useMarketSocket";
import type { QuoteResponse } from "@/types/api";

function formatTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function OverviewCards({ quote }: { quote: QuoteResponse }) {
  const { quote: liveQuote, status: wsStatus } = useMarketSocket(quote.ticker);
  const price = liveQuote?.price ?? quote.price;
  const changePct = liveQuote?.change_pct ?? quote.change_pct;
  const changeAbs = liveQuote?.change_abs ?? quote.change_abs;
  const dataStatus = liveQuote?.data_status ?? quote.data_status;
  const asOf = liveQuote?.as_of ?? quote.as_of;
  const isUp = (changePct ?? 0) >= 0;

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <Card>
        <p className="text-xs text-slate-500 dark:text-slate-400">Price</p>
        <p className="mt-1 text-2xl font-bold tabular-nums">
          {price.toFixed(2)} <span className="text-sm font-normal">{quote.currency}</span>
        </p>
      </Card>
      <Card>
        <p className="text-xs text-slate-500 dark:text-slate-400">Change</p>
        <p
          className={`mt-1 flex items-center gap-1 text-2xl font-bold tabular-nums ${isUp ? "text-bullish" : "text-bearish"}`}
        >
          <span aria-hidden="true">{isUp ? "▲" : "▼"}</span>
          {changeAbs !== null && changeAbs !== undefined ? changeAbs.toFixed(2) : "—"}
          <span className="text-sm font-normal">
            ({changePct !== null && changePct !== undefined ? `${changePct.toFixed(2)}%` : "—"})
          </span>
        </p>
      </Card>
      <Card>
        <p className="text-xs text-slate-500 dark:text-slate-400">Market status</p>
        <p className="mt-1 text-lg font-semibold capitalize">{quote.market_status ?? "Unknown"}</p>
      </Card>
      <Card>
        <div className="flex items-center justify-between">
          <p className="text-xs text-slate-500 dark:text-slate-400">Data quality</p>
          <span
            className={`h-2 w-2 rounded-full ${wsStatus === "open" ? "bg-bullish" : "bg-amber-500"}`}
            title={`Live feed: ${wsStatus}`}
          />
        </div>
        <div className="mt-1">
          <DataStatusBadge status={dataStatus} />
        </div>
        <p className="mt-1 text-xs text-slate-400" title="Timestamp shown in your local timezone">
          as of {formatTime(asOf)}
        </p>
      </Card>
    </div>
  );
}
