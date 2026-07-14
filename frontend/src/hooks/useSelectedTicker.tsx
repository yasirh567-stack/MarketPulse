import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

const STORAGE_KEY = "marketpulse.selected_ticker";
const DEFAULT_TICKER = "AAPL";

interface SelectedTickerContextValue {
  ticker: string;
  setTicker: (ticker: string) => void;
}

const SelectedTickerContext = createContext<SelectedTickerContextValue | undefined>(undefined);

export function SelectedTickerProvider({ children }: { children: ReactNode }) {
  const [ticker, setTicker] = useState<string>(
    () => localStorage.getItem(STORAGE_KEY) ?? DEFAULT_TICKER
  );

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, ticker);
  }, [ticker]);

  return (
    <SelectedTickerContext.Provider value={{ ticker, setTicker }}>
      {children}
    </SelectedTickerContext.Provider>
  );
}

/** The single ticker selected across Dashboard/Research/Backtesting/Assistant
 * pages — shared via context + localStorage so switching pages doesn't lose
 * the user's place. */
export function useSelectedTicker(): SelectedTickerContextValue {
  const ctx = useContext(SelectedTickerContext);
  if (!ctx) {
    throw new Error("useSelectedTicker must be used within a SelectedTickerProvider");
  }
  return ctx;
}
