"""Reproducible standalone training CLI.

Usage:
    python -m scripts.train_models                  # trains all bundled demo tickers
    python -m scripts.train_models AAPL MSFT         # trains specific tickers
    python -m scripts.train_models --model logistic_regression AAPL

This calls exactly the same `app.ml.service.train_and_persist` path the API's
`POST /api/v1/models/train` endpoint uses, so results are identical whether
triggered here or through the running server — there is only one training
code path, not a separate "offline" one that could drift from production.
Random seeds are fixed (see app.ml.pipeline.RANDOM_SEED) for reproducibility.
"""

from __future__ import annotations

import argparse
import sys

from app.core.config import get_settings
from app.core.errors import InsufficientDataError
from app.core.logging import configure_logging, get_logger
from app.database.base import Base
from app.database.session import get_engine, get_session_factory
from app.ml.service import DEFAULT_MODEL_NAME, train_and_persist

logger = get_logger("scripts.train_models")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "tickers", nargs="*", help="Tickers to train (defaults to the bundled demo tickers)"
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL_NAME,
        choices=["gradient_boosting", "logistic_regression"],
        help="Model type to train (default: %(default)s)",
    )
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings.log_level)
    Base.metadata.create_all(bind=get_engine())

    tickers = [t.upper() for t in args.tickers] or settings.demo_ticker_list
    session_factory = get_session_factory()

    exit_code = 0
    for ticker in tickers:
        db = session_factory()
        try:
            run = train_and_persist(db, settings, ticker, args.model)
            logger.info(
                "Trained %s for %s: %d train samples, run id %d",
                args.model,
                ticker,
                run.n_train_samples,
                run.id,
            )
        except InsufficientDataError as exc:
            logger.warning("Skipped %s: %s", ticker, exc)
            exit_code = 1
        finally:
            db.close()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
