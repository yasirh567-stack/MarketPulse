// Mirrors backend/app/schemas/*.py response shapes. Kept as plain types
// (not generated) since the API surface is small and stable enough that a
// codegen step would add more ceremony than value here.

export type DataStatus = "live" | "delayed" | "historical" | "cached" | "demo";
export type SentimentLabel = "bullish" | "neutral" | "bearish";

export interface InstrumentSearchResult {
  ticker: string;
  name: string;
  exchange: string | null;
  sector: string | null;
  is_demo: boolean;
}

export interface ScreenerEntry {
  ticker: string;
  name: string | null;
  price: number;
  change_pct: number | null;
  data_status: DataStatus;
  avg_sentiment: number;
  sentiment_label: SentimentLabel;
  bullish_mentions: number;
  bearish_mentions: number;
  article_count: number;
}

export interface ScreenerResponse {
  entries: ScreenerEntry[];
  disclaimer: string;
}

export interface QuoteResponse {
  ticker: string;
  name: string | null;
  price: number;
  previous_close: number | null;
  change_abs: number | null;
  change_pct: number | null;
  currency: string;
  market_status: string | null;
  as_of: string;
  data_status: DataStatus;
  source: string;
}

export interface PriceBar {
  ts: string;
  open: number;
  high: number;
  low: number;
  close: number;
  adj_close: number | null;
  volume: number | null;
}

export interface HistoryResponse {
  ticker: string;
  interval: string;
  data_status: DataStatus;
  source: string;
  bars: PriceBar[];
}

export interface NewsArticle {
  id: number;
  ticker: string;
  title: string;
  summary: string | null;
  url: string;
  source: string;
  published_at: string;
  data_status: DataStatus;
}

export interface NewsListResponse {
  ticker: string;
  total: number;
  page: number;
  page_size: number;
  articles: NewsArticle[];
}

export interface SentimentTimelinePoint {
  date: string;
  avg_compound: number;
  bullish_count: number;
  neutral_count: number;
  bearish_count: number;
  total_count: number;
}

export interface SourceComparisonEntry {
  avg_compound: number;
  count: number;
}

export interface SentimentResponse {
  ticker: string;
  active_model: string;
  timeline: SentimentTimelinePoint[];
  by_source_type: Record<string, SourceComparisonEntry>;
  by_model: Record<string, SourceComparisonEntry>;
}

export interface DetectedEvent {
  id: number;
  ticker: string;
  category: string;
  headline: string;
  source_url: string | null;
  matched_keywords: string[];
  confidence: number;
  published_at: string;
}

export interface EventsListResponse {
  ticker: string;
  events: DetectedEvent[];
  disclaimer: string;
}

export interface FeatureImportanceEntry {
  feature: string;
  importance?: number;
  std?: number;
  coefficient?: number;
  mean_abs_shap?: number;
}

export interface PredictionResponse {
  ticker: string;
  model_name: string;
  predicted_direction: "up" | "down";
  probability_up: number;
  confidence_label: "low" | "moderate" | "high";
  as_of_date: string;
  trained_at: string;
  train_start: string;
  train_end: string;
  n_train_samples: number;
  top_features: FeatureImportanceEntry[];
  sentiment_shift_note: string | null;
  limitations: string[];
}

export interface ModelMetricsResponse {
  ticker: string;
  model_name: string;
  trained_at: string;
  train_start: string;
  train_end: string;
  n_train_samples: number;
  n_test_samples: number;
  metrics: {
    combined: Record<string, unknown>;
    price_only: Record<string, unknown>;
    sentiment_only: Record<string, unknown>;
    permutation_importance: FeatureImportanceEntry[];
    coefficients: FeatureImportanceEntry[] | null;
    shap: FeatureImportanceEntry[] | null;
  };
  baseline_metrics: {
    majority_class: Record<string, unknown>;
    previous_direction: Record<string, unknown>;
  };
  feature_names: string[];
  random_seed: number;
}

export interface BacktestConfigInput {
  ticker: string;
  start_date?: string | null;
  end_date?: string | null;
  prob_threshold: number;
  sentiment_threshold: number;
  exit_prob_threshold: number;
  holding_period_days: number;
  transaction_cost_bps: number;
  slippage_bps: number;
  initial_capital: number;
  model_name?: string;
}

export interface EquityPoint {
  date: string;
  value: number;
}

export interface DrawdownPoint {
  date: string;
  drawdown_pct: number;
}

export interface Trade {
  entry_date: string;
  exit_date: string;
  entry_price: number;
  exit_price: number;
  return_pct: number;
  exit_reason: string;
}

export interface MonthlyReturn {
  month: string;
  return_pct: number;
}

export interface BacktestResponse {
  run_id: number;
  ticker: string;
  status: string;
  created_at: string;
  config: Record<string, unknown>;
  metrics: Record<string, number | boolean>;
  equity_curve: EquityPoint[];
  benchmark_curve: EquityPoint[];
  drawdown_curve: DrawdownPoint[];
  trades: Trade[];
  monthly_returns: MonthlyReturn[];
  disclaimer: string;
}

export interface LeaderboardEntry {
  ticker: string;
  model_name: string;
  trained_at: string | null;
  n_train_samples: number | null;
  accuracy: number | null;
  balanced_accuracy: number | null;
  roc_auc: number | null;
  brier_score: number | null;
  baseline_majority_balanced_accuracy: number | null;
  baseline_previous_direction_balanced_accuracy: number | null;
  beats_baseline: boolean;
  status: "ok" | "insufficient_data" | "error";
  note: string | null;
}

export interface LeaderboardResponse {
  entries: LeaderboardEntry[];
  disclaimer: string;
}

export interface ThresholdSweepRequest {
  ticker: string;
  start_date?: string | null;
  end_date?: string | null;
  prob_thresholds: number[];
  sentiment_threshold: number;
  exit_prob_threshold: number;
  holding_period_days: number;
  transaction_cost_bps: number;
  slippage_bps: number;
  initial_capital: number;
  model_name?: string;
}

export interface ThresholdSweepPoint {
  prob_threshold: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  total_return_pct: number;
  win_rate_pct: number;
  num_trades: number;
  max_drawdown_pct: number;
}

export interface ThresholdSweepResponse {
  ticker: string;
  thresholds: ThresholdSweepPoint[];
  disclaimer: string;
}

export interface AssistantCitation {
  title: string;
  url: string | null;
  published_at: string;
  kind: string;
}

export interface AssistantQueryResponse {
  ticker: string;
  question: string;
  answer: string;
  citations: AssistantCitation[];
  disclaimer: string;
  data_sufficient: boolean;
}

export interface QuarterlyRatioPoint {
  quarter_end: string;
  ratio_pct: number;
}

export interface BuffettIndicatorResponse {
  current_ratio_pct: number;
  as_of: string;
  data_status: DataStatus;
  source: string;
  percentile_rank: number;
  interpretation: string;
  historical: QuarterlyRatioPoint[];
  methodology_note: string;
  disclaimer: string;
}

export interface WatchlistItem {
  ticker: string;
  added_at: string;
}

export interface WatchlistResponse {
  watchlist_id: number;
  owner_key: string;
  items: WatchlistItem[];
}

export interface ProviderStatus {
  name: string;
  status: string;
  last_success_at: string | null;
  last_failure_at: string | null;
  last_error: string | null;
}

export interface HealthResponse {
  status: string;
  demo_mode: boolean;
  environment: string;
  database_ok: boolean;
  active_sentiment_model: string;
  finbert_available: boolean;
  providers: ProviderStatus[];
  version: string;
}

export interface ApiErrorBody {
  error: string;
  message: string;
  detail?: unknown;
}
