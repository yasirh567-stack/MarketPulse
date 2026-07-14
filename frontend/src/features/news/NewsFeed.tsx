import { Card } from "@/components/Card";
import { DataStatusBadge } from "@/components/DataStatusBadge";
import { EmptyState } from "@/components/StateViews";
import type { NewsArticle } from "@/types/api";

function timeAgo(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const hours = Math.round(diffMs / (1000 * 60 * 60));
  if (hours < 1) return "less than an hour ago";
  if (hours < 24) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}

export function NewsFeed({ articles }: { articles: NewsArticle[] }) {
  if (articles.length === 0) {
    return (
      <Card title="Recent news">
        <EmptyState
          title="No recent headlines"
          description="Try again shortly or pick another ticker."
        />
      </Card>
    );
  }

  return (
    <Card title="Recent news">
      <ul className="divide-y divide-slate-100 dark:divide-slate-800">
        {articles.map((article) => (
          <li key={article.id} className="py-3 first:pt-0 last:pb-0">
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium text-slate-900 hover:underline dark:text-slate-100"
            >
              {article.title}
            </a>
            {article.summary && (
              <p className="mt-1 line-clamp-2 text-sm text-slate-600 dark:text-slate-400">
                {article.summary}
              </p>
            )}
            <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs text-slate-400">
              <span>{article.source}</span>
              <span aria-hidden="true">·</span>
              <span>{timeAgo(article.published_at)}</span>
              <DataStatusBadge status={article.data_status} />
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}
