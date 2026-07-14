import { useLeaderboard } from "@/api/hooks";
import { Card } from "@/components/Card";
import { ErrorState, SkeletonBlock } from "@/components/StateViews";
import { LeaderboardTable } from "@/features/leaderboard/LeaderboardTable";

export function LeaderboardPage() {
  const { data, isLoading, isError, error, refetch } = useLeaderboard();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Model leaderboard</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Compares walk-forward-validated model quality across the bundled tickers — which ones the
          model is genuinely predictive for, honestly measured against naive baselines.
        </p>
      </div>

      {isLoading && (
        <Card>
          <p className="mb-3 text-xs text-slate-400">
            First load can take 10-20 seconds while any stale models retrain — this is expected, not
            stuck.
          </p>
          <SkeletonBlock lines={6} />
        </Card>
      )}

      {isError && (
        <ErrorState
          title="Couldn't load the leaderboard"
          description={(error as Error)?.message}
          onRetry={() => refetch()}
        />
      )}

      {data && <LeaderboardTable entries={data.entries} />}
    </div>
  );
}
