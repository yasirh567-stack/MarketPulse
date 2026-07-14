import type { ReactNode } from "react";

export function Skeleton({ className = "h-4 w-full" }: { className?: string }) {
  return <div className={`skeleton ${className}`} role="status" aria-label="Loading" />;
}

export function SkeletonBlock({ lines = 3 }: { lines?: number }) {
  return (
    <div className="space-y-2" role="status" aria-label="Loading content">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className={`h-4 ${i === lines - 1 ? "w-2/3" : "w-full"}`} />
      ))}
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-slate-300 p-8 text-center dark:border-slate-700">
      <p className="font-medium text-slate-700 dark:text-slate-300">{title}</p>
      {description && (
        <p className="max-w-sm text-sm text-slate-500 dark:text-slate-400">{description}</p>
      )}
      {action}
    </div>
  );
}

export function ErrorState({
  title = "Something went wrong",
  description,
  onRetry,
}: {
  title?: string;
  description?: string;
  onRetry?: () => void;
}) {
  return (
    <div
      role="alert"
      className="flex flex-col items-center justify-center gap-2 rounded-lg border border-bearish/30 bg-bearish-light p-6 text-center dark:border-red-900 dark:bg-red-950/40"
    >
      <p className="font-medium text-bearish dark:text-red-400">{title}</p>
      {description && (
        <p className="max-w-sm text-sm text-bearish/80 dark:text-red-300/80">{description}</p>
      )}
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-2 rounded-md border border-bearish/40 px-3 py-1.5 text-sm font-medium text-bearish hover:bg-bearish/10 dark:border-red-800 dark:text-red-400"
        >
          Try again
        </button>
      )}
    </div>
  );
}
