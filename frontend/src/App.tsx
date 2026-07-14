import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";
import { AppLayout } from "@/layouts/AppLayout";
import { LandingPage } from "@/pages/LandingPage";
import { AssistantPage } from "@/pages/AssistantPage";
import { StatusPage } from "@/pages/StatusPage";
import { SkeletonBlock } from "@/components/StateViews";

// The Dashboard/Research/Backtesting pages all pull in Plotly (a large
// charting library) — lazy-loading them keeps the landing page and other
// chart-free routes from paying for that download upfront.
const DashboardPage = lazy(() =>
  import("@/pages/DashboardPage").then((m) => ({ default: m.DashboardPage }))
);
const ResearchPage = lazy(() =>
  import("@/pages/ResearchPage").then((m) => ({ default: m.ResearchPage }))
);
const BacktestingPage = lazy(() =>
  import("@/pages/BacktestingPage").then((m) => ({ default: m.BacktestingPage }))
);
const LeaderboardPage = lazy(() =>
  import("@/pages/LeaderboardPage").then((m) => ({ default: m.LeaderboardPage }))
);

function PageFallback() {
  return (
    <div className="p-6">
      <SkeletonBlock lines={8} />
    </div>
  );
}

export function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<LandingPage />} />
        <Route
          path="/dashboard"
          element={
            <Suspense fallback={<PageFallback />}>
              <DashboardPage />
            </Suspense>
          }
        />
        <Route
          path="/research"
          element={
            <Suspense fallback={<PageFallback />}>
              <ResearchPage />
            </Suspense>
          }
        />
        <Route
          path="/backtesting"
          element={
            <Suspense fallback={<PageFallback />}>
              <BacktestingPage />
            </Suspense>
          }
        />
        <Route
          path="/leaderboard"
          element={
            <Suspense fallback={<PageFallback />}>
              <LeaderboardPage />
            </Suspense>
          }
        />
        <Route path="/assistant" element={<AssistantPage />} />
        <Route path="/status" element={<StatusPage />} />
      </Route>
    </Routes>
  );
}
