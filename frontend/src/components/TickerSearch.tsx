import { useId, useRef, useState } from "react";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { useInstrumentSearch } from "@/api/hooks";

export function TickerSearch({ onSelect }: { onSelect: (ticker: string) => void }) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const debouncedQuery = useDebouncedValue(query, 300);
  const { data: results, isFetching } = useInstrumentSearch(debouncedQuery);
  const listId = useId();
  const inputRef = useRef<HTMLInputElement>(null);

  function handleSelect(ticker: string) {
    onSelect(ticker);
    setQuery("");
    setOpen(false);
    inputRef.current?.blur();
  }

  return (
    <div className="relative w-full max-w-xs">
      <label htmlFor="ticker-search" className="sr-only">
        Search stocks by ticker or company name
      </label>
      <input
        id="ticker-search"
        ref={inputRef}
        type="search"
        role="combobox"
        aria-expanded={open}
        aria-controls={listId}
        aria-autocomplete="list"
        placeholder="Search ticker or company (e.g. AAPL)"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && query.trim()) {
            handleSelect(query.trim().toUpperCase());
          }
        }}
        className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
      />
      {open && debouncedQuery && (
        <ul
          id={listId}
          role="listbox"
          className="absolute z-30 mt-1 w-full overflow-hidden rounded-md border border-slate-200 bg-white shadow-lg dark:border-slate-700 dark:bg-slate-900"
        >
          {isFetching && (
            <li className="px-3 py-2 text-sm text-slate-500 dark:text-slate-400">Searching…</li>
          )}
          {!isFetching && results?.length === 0 && (
            <li className="px-3 py-2 text-sm text-slate-500 dark:text-slate-400">
              No matching tickers found
            </li>
          )}
          {results?.map((r) => (
            <li key={r.ticker}>
              <button
                type="button"
                role="option"
                aria-selected={false}
                onMouseDown={() => handleSelect(r.ticker)}
                className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <span>
                  <span className="font-semibold">{r.ticker}</span>{" "}
                  <span className="text-slate-500 dark:text-slate-400">{r.name}</span>
                </span>
                {r.is_demo && (
                  <span className="rounded bg-violet-100 px-1.5 py-0.5 text-[10px] text-violet-800 dark:bg-violet-950 dark:text-violet-400">
                    demo
                  </span>
                )}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
