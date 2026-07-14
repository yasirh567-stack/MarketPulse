import { NavLink, Outlet } from "react-router-dom";
import { useTheme } from "@/hooks/useTheme";
import { useHealth } from "@/api/hooks";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/research", label: "Research" },
  { to: "/backtesting", label: "Backtesting" },
  { to: "/leaderboard", label: "Leaderboard" },
  { to: "/assistant", label: "Assistant" },
  { to: "/status", label: "Status" },
];

function navLinkClass({ isActive }: { isActive: boolean }): string {
  return `rounded-md px-3 py-2 text-sm font-medium transition-colors ${
    isActive
      ? "bg-slate-900 text-white dark:bg-white dark:text-slate-900"
      : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
  }`;
}

export function AppLayout() {
  const [theme, toggleTheme] = useTheme();
  const { data: health } = useHealth();

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-surface-dark">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-white focus:px-3 focus:py-2 focus:shadow"
      >
        Skip to main content
      </a>
      <header className="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <div className="flex items-center gap-4">
            <NavLink to="/" className="text-lg font-bold tracking-tight">
              MarketPulse<span className="text-sky-500"> AI</span>
            </NavLink>
            <nav aria-label="Main navigation" className="hidden gap-1 md:flex">
              {NAV_ITEMS.map((item) => (
                <NavLink key={item.to} to={item.to} className={navLinkClass}>
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-3">
            {health?.demo_mode && (
              <span className="rounded-full bg-violet-100 px-2.5 py-1 text-xs font-medium text-violet-800 dark:bg-violet-950 dark:text-violet-400">
                Demo Mode
              </span>
            )}
            <button
              type="button"
              onClick={toggleTheme}
              aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
              className="rounded-md border border-slate-300 p-2 text-sm dark:border-slate-700"
            >
              {theme === "dark" ? "☀" : "☾"}
            </button>
          </div>
        </div>
        <nav
          aria-label="Main navigation (mobile)"
          className="flex gap-1 overflow-x-auto border-t border-slate-100 px-4 py-2 md:hidden dark:border-slate-800"
        >
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.to} to={item.to} className={navLinkClass}>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main id="main-content" className="mx-auto max-w-7xl px-4 py-6">
        <Outlet />
      </main>
      <footer className="mx-auto max-w-7xl px-4 py-8 text-xs text-slate-400 dark:text-slate-500">
        <p>
          MarketPulse AI is an educational portfolio project. Nothing on this site is financial
          advice, and no model output guarantees any investment outcome.
        </p>
      </footer>
    </div>
  );
}
