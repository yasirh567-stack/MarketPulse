import { useId, useState, type FormEvent } from "react";
import type { BacktestConfigInput } from "@/types/api";

interface FieldErrors {
  [key: string]: string;
}

const DEFAULTS: Omit<BacktestConfigInput, "ticker"> = {
  prob_threshold: 0.55,
  sentiment_threshold: 0.0,
  exit_prob_threshold: 0.45,
  holding_period_days: 5,
  transaction_cost_bps: 10,
  slippage_bps: 5,
  initial_capital: 10_000,
  model_name: "gradient_boosting",
};

export function BacktestForm({
  ticker,
  onSubmit,
  isSubmitting,
  onSweep,
  isSweeping,
}: {
  ticker: string;
  onSubmit: (config: BacktestConfigInput) => void;
  isSubmitting: boolean;
  onSweep?: (config: BacktestConfigInput) => void;
  isSweeping?: boolean;
}) {
  const [form, setForm] = useState({ ...DEFAULTS });
  const [errors, setErrors] = useState<FieldErrors>({});
  const formId = useId();

  function update<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function validate(): FieldErrors {
    const next: FieldErrors = {};
    if (form.prob_threshold <= 0.5 || form.prob_threshold > 0.95) {
      next.prob_threshold = "Entry probability threshold must be between 0.5 and 0.95.";
    }
    if (form.exit_prob_threshold < 0.05 || form.exit_prob_threshold > 0.5) {
      next.exit_prob_threshold = "Exit probability threshold must be between 0.05 and 0.5.";
    }
    if (form.exit_prob_threshold >= form.prob_threshold) {
      next.exit_prob_threshold = "Exit threshold should be lower than the entry threshold.";
    }
    if (form.holding_period_days < 1 || form.holding_period_days > 60) {
      next.holding_period_days = "Holding period must be between 1 and 60 trading days.";
    }
    if (form.transaction_cost_bps < 0 || form.transaction_cost_bps > 500) {
      next.transaction_cost_bps = "Transaction cost must be between 0 and 500 bps.";
    }
    if (form.slippage_bps < 0 || form.slippage_bps > 500) {
      next.slippage_bps = "Slippage must be between 0 and 500 bps.";
    }
    if (form.initial_capital < 100) {
      next.initial_capital = "Initial capital must be at least $100.";
    }
    return next;
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const validationErrors = validate();
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length === 0) {
      onSubmit({ ticker, ...form });
    }
  }

  function handleSweep() {
    // The sweep endpoint ignores `prob_threshold` (it sweeps its own fixed
    // set of thresholds server-side) — the exit/sentiment/cost/holding-period
    // fields still apply, so reuse the same validation for those.
    const validationErrors = validate();
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length === 0) {
      onSweep?.({ ticker, ...form });
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      className="space-y-4"
      aria-label="Backtest configuration"
    >
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <Field label="Entry probability ≥" id={`${formId}-prob`} error={errors.prob_threshold}>
          <input
            id={`${formId}-prob`}
            type="number"
            step={0.01}
            min={0.5}
            max={0.95}
            value={form.prob_threshold}
            onChange={(e) => update("prob_threshold", Number(e.target.value))}
            className="input"
          />
        </Field>
        <Field label="Sentiment ≥" id={`${formId}-sent`} error={errors.sentiment_threshold}>
          <input
            id={`${formId}-sent`}
            type="number"
            step={0.01}
            min={-1}
            max={1}
            value={form.sentiment_threshold}
            onChange={(e) => update("sentiment_threshold", Number(e.target.value))}
            className="input"
          />
        </Field>
        <Field label="Exit probability <" id={`${formId}-exit`} error={errors.exit_prob_threshold}>
          <input
            id={`${formId}-exit`}
            type="number"
            step={0.01}
            min={0.05}
            max={0.5}
            value={form.exit_prob_threshold}
            onChange={(e) => update("exit_prob_threshold", Number(e.target.value))}
            className="input"
          />
        </Field>
        <Field
          label="Holding period (days)"
          id={`${formId}-hold`}
          error={errors.holding_period_days}
        >
          <input
            id={`${formId}-hold`}
            type="number"
            min={1}
            max={60}
            value={form.holding_period_days}
            onChange={(e) => update("holding_period_days", Number(e.target.value))}
            className="input"
          />
        </Field>
        <Field
          label="Transaction cost (bps)"
          id={`${formId}-cost`}
          error={errors.transaction_cost_bps}
        >
          <input
            id={`${formId}-cost`}
            type="number"
            min={0}
            max={500}
            value={form.transaction_cost_bps}
            onChange={(e) => update("transaction_cost_bps", Number(e.target.value))}
            className="input"
          />
        </Field>
        <Field label="Slippage (bps)" id={`${formId}-slip`} error={errors.slippage_bps}>
          <input
            id={`${formId}-slip`}
            type="number"
            min={0}
            max={500}
            value={form.slippage_bps}
            onChange={(e) => update("slippage_bps", Number(e.target.value))}
            className="input"
          />
        </Field>
        <Field label="Initial capital ($)" id={`${formId}-cap`} error={errors.initial_capital}>
          <input
            id={`${formId}-cap`}
            type="number"
            min={100}
            value={form.initial_capital}
            onChange={(e) => update("initial_capital", Number(e.target.value))}
            className="input"
          />
        </Field>
        <Field label="Model" id={`${formId}-model`}>
          <select
            id={`${formId}-model`}
            value={form.model_name}
            onChange={(e) => update("model_name", e.target.value)}
            className="input"
          >
            <option value="gradient_boosting">Gradient boosting</option>
            <option value="logistic_regression">Logistic regression</option>
          </select>
        </Field>
      </div>
      <div className="flex flex-wrap gap-3">
        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white hover:bg-slate-700 disabled:opacity-50 dark:bg-white dark:text-slate-900"
        >
          {isSubmitting ? "Running backtest…" : "Run backtest"}
        </button>
        {onSweep && (
          <button
            type="button"
            onClick={handleSweep}
            disabled={isSweeping}
            className="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-100 disabled:opacity-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            {isSweeping ? "Comparing thresholds…" : "Compare confidence thresholds"}
          </button>
        )}
      </div>
    </form>
  );
}

function Field({
  label,
  id,
  error,
  children,
}: {
  label: string;
  id: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label
        htmlFor={id}
        className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400"
      >
        {label}
      </label>
      {children}
      {error && (
        <p className="mt-1 text-xs text-bearish" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
