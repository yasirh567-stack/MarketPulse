import { Card } from "@/components/Card";
import { EmptyState } from "@/components/StateViews";
import { Tooltip } from "@/components/Tooltip";
import type { DetectedEvent } from "@/types/api";

const CATEGORY_LABELS: Record<string, string> = {
  earnings: "Earnings",
  guidance: "Guidance",
  acquisition: "Acquisition",
  lawsuit: "Lawsuit",
  investigation: "Investigation",
  product_launch: "Product launch",
  executive_departure: "Executive departure",
  analyst_upgrade: "Analyst upgrade",
  analyst_downgrade: "Analyst downgrade",
  dividend: "Dividend",
  stock_split: "Stock split",
  macro: "Macro",
};

export function EventsPanel({
  events,
  disclaimer,
}: {
  events: DetectedEvent[];
  disclaimer: string;
}) {
  return (
    <Card
      title={
        <span className="flex items-center gap-1.5">
          Detected events
          <Tooltip label="What is a detected event?">{disclaimer}</Tooltip>
        </span>
      }
    >
      {events.length === 0 ? (
        <EmptyState
          title="No events detected"
          description="No keyword-matched events in recent headlines."
        />
      ) : (
        <ul className="space-y-2">
          {events.map((event) => (
            <li
              key={event.id}
              className="rounded-lg border border-slate-100 p-2.5 text-sm dark:border-slate-800"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-full bg-sky-100 px-2 py-0.5 text-xs font-medium text-sky-800 dark:bg-sky-950 dark:text-sky-400">
                  {CATEGORY_LABELS[event.category] ?? event.category}
                </span>
                <span className="text-xs text-slate-400">
                  confidence {(event.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <p className="mt-1">
                {event.source_url ? (
                  <a
                    href={event.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:underline"
                  >
                    {event.headline}
                  </a>
                ) : (
                  event.headline
                )}
              </p>
              <p className="mt-1 text-xs text-slate-400">
                matched: {event.matched_keywords.join(", ")}
              </p>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
