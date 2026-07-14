const STORAGE_KEY = "marketpulse.watchlist_id";

function generateId(): string {
  // A random, anonymous, browser-local identifier — no account required.
  // 24 chars of base36 comfortably satisfies the backend's 6-64 char pattern.
  const random =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID().replace(/-/g, "")
      : Math.random().toString(36).slice(2) + Date.now().toString(36);
  return `anon-${random}`.slice(0, 64);
}

/** Returns a stable, anonymous watchlist identifier persisted in
 * localStorage — created once per browser, never sent anywhere but our own
 * backend, and never tied to a real account. */
export function useWatchlistId(): string {
  let id = localStorage.getItem(STORAGE_KEY);
  if (!id) {
    id = generateId();
    localStorage.setItem(STORAGE_KEY, id);
  }
  return id;
}
