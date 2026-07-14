import { useId, useState, type ReactNode } from "react";

/** A keyboard-accessible tooltip (focus OR hover reveals it) used to explain
 * financial/ML jargon inline without cluttering the UI with permanent text. */
export function Tooltip({ label, children }: { label: string; children: ReactNode }) {
  const [visible, setVisible] = useState(false);
  const id = useId();

  return (
    <span className="relative inline-flex">
      <button
        type="button"
        aria-describedby={id}
        aria-label={`More information: ${label}`}
        onFocus={() => setVisible(true)}
        onBlur={() => setVisible(false)}
        onMouseEnter={() => setVisible(true)}
        onMouseLeave={() => setVisible(false)}
        className="inline-flex h-4 w-4 items-center justify-center rounded-full border border-slate-400 text-[10px] leading-none text-slate-500 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-400 dark:hover:bg-slate-800"
      >
        ?
      </button>
      {visible && (
        <span
          id={id}
          role="tooltip"
          className="absolute bottom-full left-1/2 z-20 mb-2 w-56 -translate-x-1/2 rounded-md bg-slate-900 p-2 text-xs text-white shadow-lg dark:bg-slate-700"
        >
          {children}
        </span>
      )}
    </span>
  );
}
