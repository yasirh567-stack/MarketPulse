# Model Card — Next-Period Direction Estimator

## Intended use

Estimates the probability that a given ticker's closing price will be **higher**
tomorrow than today, using daily price/volume history and aggregated news sentiment.
It is a **research/educational tool** for exploring how price, momentum, and
sentiment features relate to short-term direction — not a trading signal generator,
and not a substitute for professional financial advice.

**Do not** use this model's output as the sole basis for a real trading decision.
No claim is made or implied that this model, or any variant of it, can generate
positive risk-adjusted returns going forward.

## Out of scope

- Intraday or high-frequency prediction (free daily-bar data cannot support this).
- Predicting the *magnitude* of a price move — only direction (up/down).
- Multi-day-ahead forecasts — the target is always the very next trading day.
- Any ticker with less than ~4 months of aligned price+feature history (see
  "Minimum data requirement" below).

## Data

- **Price/volume**: daily OHLCV bars from `yfinance` (real tickers, delayed ~15 min
  intraday but this doesn't affect daily-bar research) or bundled synthetic demo
  fixtures (`DEMO_MODE=true`), clearly tagged via `data_status`.
- **Sentiment**: VADER (default) or FinBERT (optional) scores of recent news
  headlines/summaries stored in the database, aggregated into a trailing 5-day window.
- **Events**: rule-based keyword-detected categories (earnings, guidance, M&A,
  litigation, etc.) from the same stored headlines, one-hot encoded over a trailing
  5-day window.

Demo-mode price series are **seeded synthetic geometric Brownian motion**, not real
historical prices — see `docs/data-sources.md`. Demo-mode news is fictional but
realistic-sounding sample copy, also clearly labeled.

## Methodology

### Feature engineering (`backend/app/ml/features.py`)
Price features (12): lagged returns (1d, 5d), 10-day momentum, 10-day volatility,
distance from 5-/20-day moving averages, volume change, relative volume, RSI(14),
MACD/signal/histogram.

Sentiment features (4): 5-day average compound sentiment, sentiment momentum
(change vs. prior day's 5-day average), bullish-to-bearish mention ratio, article count.

Event features (12): one indicator per detected category, active if that category
appeared in the trailing 5 days.

### Time alignment (leakage prevention)
A feature row for trading day **T** may only use:
- price/volume data through and including day T's close,
- news/events published **strictly before** T's close (never at or after).

The label for row T is the sign of `close[T+1] - close[T]` — the only place future
information appears, and only as the target, never as an input. This is enforced in
code (`build_dataset`) and directly asserted in
`backend/tests/test_feature_alignment.py` (e.g. perturbing a future bar's price
provably does not change any earlier row's computed features).

### Validation
**Walk-forward (expanding-window) cross-validation** — never a random/shuffled split.
Each fold's model is trained only on data chronologically before that fold's test
block. Five folds, minimum 40-sample initial training window
(`app/ml/pipeline.py: N_SPLITS`, `MIN_TRAIN_SIZE`).

Reported alongside the combined (price + sentiment + events) model:
- **Majority-class baseline** — always predict the more common class in the training fold.
- **Previous-direction baseline** — predict that today's direction repeats yesterday's.
- **Price-only model** — same architecture, price features only.
- **Sentiment-only model** — same architecture, sentiment + event features only.

This comparison is always shown together in the Research page — a headline accuracy
number is never displayed without these baselines next to it.

### Models
- **Logistic regression** (`StandardScaler` + `LogisticRegression`) — coefficients
  available as an additional explainability signal.
- **Gradient boosting** (`GradientBoostingClassifier`, 150 estimators, depth 3) — the
  default.

Both use `random_state=42` everywhere randomness is involved.

### Calibration — and a bug we found and fixed
Predicted probabilities are calibrated via a from-scratch **temporal Platt scaling**
(`app/ml/calibration.py`), never scikit-learn's default `CalibratedClassifierCV`
(which uses shuffled K-fold internally — leaking future rows into calibration of
earlier ones for time-series data).

During initial end-to-end testing, the *production* model (trained once on all
history for live predictions) briefly showed 97% confidence on a ticker whose
honest walk-forward accuracy was ~49.5% — indistinguishable from a coin flip. The
root cause: the calibrator was being fit on the model's own training predictions,
and a gradient-boosted model can trivially separate rows it was trained on, so the
calibrator learned "this model's training-set confidence is very informative" — which
doesn't generalize. **Fix:** the production model now trains on the first 80% of
available history (chronologically) and the calibrator is fit only on the
remaining, later 20% — data the model never saw during training. This trades a
little recency (the live model doesn't train on its most recent ~20% of history)
for calibration honesty. See `app/ml/pipeline.py::train_final_model` and the
regression test in `test_ml_pipeline.py`.

### Explainability
- **Permutation importance** (default) — computed on a genuinely held-out slice
  (the same later 20% used for calibration), 15 repeats, `random_state=42`.
- **SHAP** (optional) — only computed if the `shap` package is importable
  (`requirements-ml.txt`); the API/UI clearly say "not installed" rather than
  fabricating a result when it's unavailable.
- **Coefficients** — for logistic regression, raw fitted coefficients as a second,
  cheap cross-check against permutation importance.

## Metrics reported

Accuracy, balanced accuracy, precision, recall, F1, ROC-AUC (when both classes are
present in a fold), Brier score, and a confusion matrix summed across all
out-of-sample folds. All computed by scikit-learn directly on realized predictions
— never hand-adjusted or fabricated.

## Leaderboard

`GET /api/v1/leaderboard` compares these metrics across several tickers in one
call, reusing `get_or_train`'s existing staleness/auto-train semantics — it is not
a second training code path, just a query/aggregation layer over the same
append-only `model_runs` table every other model endpoint already writes to. Each
row reports `beats_baseline`: whether the combined model's balanced accuracy
exceeds the stronger of the majority-class and previous-direction baselines for
that ticker — the same "never show a headline number without its baseline"
framing used on the Research page, applied across tickers instead of within one.
A ticker that fails (insufficient history, or a market-data provider issue) is
marked on its own row rather than failing the whole request.

## Minimum data requirement

Training requires **at least 80 usable rows** after feature warm-up and dropping the
unlabeled final row (`app/ml/pipeline.py: MIN_TOTAL_SAMPLES`). Below that, the API
returns a 422 `insufficient_data` error with an explanation, rather than a guess.
Predictions additionally require the most recent bar's own feature row to be
NaN-free (enough trailing history for rolling indicators); if not, the same error
class is raised for that specific reason.

## Limitations

- Small feature/training set relative to institutional systems — this is a portfolio/
  research project, not a production trading system.
- Demo tickers' "history" is synthetic (seeded GBM), so their walk-forward metrics
  reflect a synthetic random walk, not real market dynamics; real tickers (when
  `DEMO_MODE=false` and network access is available) use real yfinance history.
- Sentiment coverage depends entirely on how many headlines are stored for a
  ticker — a ticker with very little news will have near-zero-variance sentiment
  features, which the sentiment-only baseline will honestly reflect (low accuracy).
- Walk-forward metrics can vary substantially by ticker, time period, and market
  regime; a model beating baselines on one ticker/period is not evidence it will do
  so elsewhere or going forward.
- No survivorship-bias controls, no transaction-level market-impact modeling, no
  regime-switching detection.

## Ethical considerations

- The API and UI never present a prediction without its probability, confidence
  label, training date, and a list of limitations attached (see
  `PredictionResponse.limitations` in `backend/app/schemas/ml.py` and the
  Dashboard's Prediction Card / Research page).
- No claim of guaranteed returns is made anywhere in the UI, API responses, or docs.
- The model does not use any protected-characteristic or non-market data; inputs
  are limited to price/volume/news-derived features for the instrument itself.
