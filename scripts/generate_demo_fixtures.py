#!/usr/bin/env python3
"""Generate small, deterministic demo fixtures under data/demo/.

Design decision: fixtures store *offsets* (trading-days-ago / hours-ago), not
baked-in absolute dates. The demo providers resolve these to real calendar
dates/timestamps relative to "now" at request time. That keeps the bundled
demo feeling current indefinitely (a recruiter running this in 2027 sees
"3 hours ago" news and a price history ending "today"), without ever having
to regenerate fixtures or claim recycled data is live.

Price series use a seeded geometric Brownian motion (pure stdlib `random`, no
numpy dependency needed just to generate fixtures) — clearly a synthetic
stand-in, never presented as real historical prices (the API always tags
these rows with data_status="demo").

Run with: python3 scripts/generate_demo_fixtures.py
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEMO_DIR = REPO_ROOT / "data" / "demo"

# ticker -> (display name, sector, starting price, annualized drift, annualized vol, seed)
INSTRUMENTS = {
    "AAPL": ("Apple Inc.", "Technology", 190.0, 0.14, 0.28, 1001),
    "MSFT": ("Microsoft Corporation", "Technology", 415.0, 0.16, 0.26, 1002),
    "TSLA": ("Tesla, Inc.", "Consumer Cyclical", 245.0, 0.05, 0.55, 1003),
    "NVDA": ("NVIDIA Corporation", "Technology", 120.0, 0.35, 0.50, 1004),
    "GME": ("GameStop Corp.", "Consumer Cyclical", 22.0, -0.05, 0.75, 1005),
    "CHTR": ("Charter Communications, Inc. (Spectrum)", "Communication Services", 340.0, 0.04, 0.40, 1006),
}

TRADING_DAYS = 260  # ~ one year of trading history


def generate_price_series(start_price: float, drift: float, vol: float, seed: int, n_days: int):
    rng = random.Random(seed)
    dt = 1.0 / 252.0
    prices = []
    price = start_price
    for i in range(n_days):
        shock = rng.gauss(0.0, 1.0)
        ret = (drift - 0.5 * vol**2) * dt + vol * math.sqrt(dt) * shock
        price = max(0.5, price * math.exp(ret))
        intraday_vol = vol * math.sqrt(dt) * 0.6
        open_px = price * math.exp(rng.gauss(0, intraday_vol))
        high = max(open_px, price) * (1 + abs(rng.gauss(0, intraday_vol)))
        low = min(open_px, price) * (1 - abs(rng.gauss(0, intraday_vol)))
        base_volume = 20_000_000 if price > 50 else 60_000_000
        volume = int(base_volume * math.exp(rng.gauss(0, 0.35)))
        # offset_days counts backward from "today": n_days-1-i => oldest first
        offset_days = n_days - 1 - i
        prices.append(
            {
                "offset_trading_days": offset_days,
                "open": round(open_px, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(price, 2),
                "adj_close": round(price, 2),
                "volume": volume,
            }
        )
    return prices


NEWS_TEMPLATES = {
    "AAPL": [
        (72, "Apple Reports Quarterly Earnings Above Analyst Estimates", "earnings",
         "Apple posted quarterly revenue and EPS ahead of consensus estimates, driven by "
         "stronger-than-expected Services segment growth."),
        (60, "Apple Raises Guidance for Upcoming Quarter", "guidance",
         "Apple guided next quarter revenue slightly above the prior consensus range, "
         "citing steady demand across its product lineup."),
        (48, "Analyst Upgrades Apple to Buy, Cites Services Momentum", "analyst_upgrade",
         "A sell-side analyst raised their rating on Apple shares, pointing to accelerating "
         "high-margin Services revenue as a key upside driver."),
        (36, "Apple Unveils New Product Line at Annual Event", "product_launch",
         "Apple announced a refreshed product lineup at its annual product event, with "
         "shipping expected to begin next month."),
        (24, "Apple Faces Regulatory Investigation Over App Store Practices", "investigation",
         "Regulators opened an inquiry into Apple's App Store fee structure, adding to "
         "ongoing scrutiny of the company's platform policies."),
        (10, "Apple Declares Quarterly Dividend", "dividend",
         "Apple's board declared its regular quarterly cash dividend, payable to "
         "shareholders of record next month."),
        (4, "Apple Shares Trade Higher Amid Broader Tech Rally", "market_move",
         "Apple shares moved higher along with the broader technology sector as investors "
         "rotated back into large-cap growth names."),
    ],
    "MSFT": [
        (80, "Microsoft Quarterly Cloud Revenue Beats Expectations", "earnings",
         "Microsoft's Azure and cloud segment grew faster than analysts expected, "
         "lifting overall quarterly results above consensus."),
        (55, "Microsoft Announces Acquisition of AI Startup", "acquisition",
         "Microsoft agreed to acquire a smaller AI infrastructure startup to bolster its "
         "cloud and enterprise AI offerings, terms undisclosed."),
        (40, "Analyst Downgrades Microsoft on Valuation Concerns", "analyst_downgrade",
         "An analyst moved to a neutral rating on Microsoft, citing a stretched valuation "
         "after the stock's recent run-up."),
        (28, "Microsoft Declares Increased Quarterly Dividend", "dividend",
         "Microsoft's board approved a dividend increase, marking another consecutive "
         "year of payout growth."),
        (14, "Microsoft Executive Steps Down", "executive_departure",
         "A senior Microsoft executive announced plans to leave the company, with an "
         "internal successor named on an interim basis."),
        (6, "Microsoft Launches New AI-Powered Product Suite", "product_launch",
         "Microsoft rolled out a new suite of AI-integrated productivity tools aimed at "
         "enterprise customers."),
    ],
    "TSLA": [
        (90, "Tesla Delivery Numbers Miss Analyst Estimates", "earnings",
         "Tesla reported quarterly vehicle deliveries below the average analyst estimate, "
         "citing production ramp challenges at a newer facility."),
        (65, "Tesla Cuts Full-Year Guidance", "guidance",
         "Tesla lowered its full-year delivery guidance, pointing to softer demand in "
         "some international markets."),
        (50, "Tesla Under Investigation Over Autopilot Safety Claims", "investigation",
         "Regulators expanded a safety investigation into Tesla's driver-assistance "
         "systems following several reported incidents."),
        (32, "Tesla Unveils Next-Generation Vehicle Platform", "product_launch",
         "Tesla showed off a new vehicle platform at a company event, with production "
         "targeted for next year."),
        (20, "Analyst Upgrades Tesla Citing Energy Storage Growth", "analyst_upgrade",
         "An analyst raised their price target on Tesla, highlighting faster-than-expected "
         "growth in the company's energy storage business."),
        (8, "Tesla CEO Comments Spark Volatility in Shares", "executive_departure",
         "Tesla shares swung after comments from company leadership about future strategy "
         "priorities drew mixed reactions from investors."),
    ],
    "NVDA": [
        (75, "NVIDIA Reports Record Data Center Revenue", "earnings",
         "NVIDIA posted another quarter of record data center segment revenue, driven by "
         "continued strong demand for AI accelerators."),
        (58, "NVIDIA Raises Forward Guidance on AI Chip Demand", "guidance",
         "NVIDIA guided next quarter revenue well above consensus, citing sustained "
         "demand for its latest AI training and inference chips."),
        (42, "NVIDIA Announces Stock Split", "stock_split",
         "NVIDIA's board approved a stock split, aiming to make shares more accessible "
         "to a broader base of individual investors."),
        (30, "Analyst Raises NVIDIA Price Target on AI Backlog", "analyst_upgrade",
         "An analyst raised their NVIDIA price target, citing a growing order backlog "
         "for next-generation AI accelerator chips."),
        (16, "NVIDIA Announces Partnership With Major Cloud Providers", "product_launch",
         "NVIDIA expanded partnerships with major cloud providers to deploy its latest "
         "chips at scale."),
        (5, "NVIDIA Shares Volatile on Chip Export Policy Headlines", "macro",
         "NVIDIA shares moved on renewed headlines about semiconductor export policy "
         "affecting the broader chip sector."),
    ],
    "GME": [
        (95, "GameStop Reports Narrower Quarterly Loss", "earnings",
         "GameStop reported a smaller quarterly loss than analysts expected, as cost-cutting "
         "measures partially offset declining store traffic."),
        (70, "GameStop Announces Store Closures as Part of Restructuring", "guidance",
         "GameStop said it would close a number of underperforming stores as part of an "
         "ongoing turnaround effort."),
        (52, "GameStop Executive Departs Amid Strategy Shift", "executive_departure",
         "A senior GameStop executive left the company as leadership continues to "
         "reassess the retailer's long-term strategy."),
        (38, "GameStop Shares Spike on Heavy Retail Trading Volume", "market_move",
         "GameStop shares saw a sharp rise in volatility amid unusually heavy retail "
         "trading activity."),
        (22, "GameStop Faces Shareholder Lawsuit Over Disclosures", "lawsuit",
         "GameStop was named in a shareholder lawsuit alleging inadequate disclosure "
         "of certain business risks."),
        (9, "Analyst Downgrades GameStop on Turnaround Uncertainty", "analyst_downgrade",
         "An analyst downgraded GameStop shares, citing continued uncertainty about the "
         "pace of the company's turnaround plan."),
    ],
    "CHTR": [
        (85, "Charter Reports Broadband Subscriber Losses", "earnings",
         "Charter Communications reported a decline in broadband subscribers for the "
         "quarter, citing intensifying competition from fixed wireless providers."),
        (62, "Charter Lowers Full-Year Subscriber Guidance", "guidance",
         "Charter cut its full-year subscriber growth outlook, pointing to a more "
         "competitive residential broadband market than previously expected."),
        (48, "Charter Announces Merger Talks With Cox Communications", "acquisition",
         "Charter confirmed it was in discussions regarding a potential merger with "
         "Cox Communications, a move that would reshape the cable industry landscape."),
        (34, "Charter Faces Investigation Over Billing Practices", "investigation",
         "State regulators opened an inquiry into Charter's Spectrum billing practices "
         "following a rise in customer complaints."),
        (20, "Charter Launches New Spectrum Mobile Bundle", "product_launch",
         "Charter unveiled a new bundled mobile and broadband plan under its Spectrum "
         "brand, aiming to slow subscriber losses to competitors."),
        (11, "Analyst Downgrades Charter on Competitive Pressure", "analyst_downgrade",
         "An analyst downgraded Charter shares, citing sustained competitive pressure "
         "from fiber and fixed wireless broadband alternatives."),
        (4, "Charter Declares Quarterly Dividend", "dividend",
         "Charter's board declared its regular quarterly dividend, payable to "
         "shareholders of record next month."),
    ],
}


def generate_buffett_indicator_series(n_quarters=80, seed=2001):
    """Illustrative, clearly-synthetic quarterly market-cap-to-GDP ("Buffett
    Indicator") series for demo mode — a long-run upward-drifting random walk
    loosely shaped like the real long-term trend (roughly 60-80% decades ago,
    100-150%+ more recently), NOT real historical Federal Reserve/Wilshire
    data. Real values require the optional FRED integration (see
    app/providers/macro.py) — this fixture only powers DEMO_MODE.
    """
    rng = random.Random(seed)
    values = []
    ratio = 65.0
    for i in range(n_quarters):
        ratio = max(30.0, ratio + rng.gauss(1.1, 4.5))
        # offset counts backward from the most recent quarter: 0 = current
        quarters_ago = n_quarters - 1 - i
        values.append({"quarters_ago": quarters_ago, "ratio_pct": round(ratio, 2)})
    return values


def build_news_fixture(ticker: str):
    articles = []
    for i, (hours_ago, title, _category, summary) in enumerate(NEWS_TEMPLATES[ticker]):
        articles.append(
            {
                "hours_ago": hours_ago,
                "title": title,
                "summary": summary,
                "source": "MarketPulse Demo Wire",
                "url": f"https://example.com/demo-news/{ticker.lower()}/{i}",
            }
        )
    return {"ticker": ticker, "articles": articles}


def main() -> None:
    prices_dir = DEMO_DIR / "prices"
    news_dir = DEMO_DIR / "news"
    prices_dir.mkdir(parents=True, exist_ok=True)
    news_dir.mkdir(parents=True, exist_ok=True)

    instruments_manifest = []
    for ticker, (name, sector, start_price, drift, vol, seed) in INSTRUMENTS.items():
        series = generate_price_series(start_price, drift, vol, seed, TRADING_DAYS)
        payload = {
            "ticker": ticker,
            "name": name,
            "sector": sector,
            "generation_method": "seeded geometric Brownian motion (demo synthetic data)",
            "seed": seed,
            "bars": series,
        }
        out_path = prices_dir / f"{ticker}.json"
        out_path.write_text(json.dumps(payload, indent=2))
        print(f"wrote {out_path} ({len(series)} bars)")

        news_payload = build_news_fixture(ticker)
        news_path = news_dir / f"{ticker}.json"
        news_path.write_text(json.dumps(news_payload, indent=2))
        print(f"wrote {news_path} ({len(news_payload['articles'])} articles)")

        instruments_manifest.append({"ticker": ticker, "name": name, "sector": sector})

    manifest_path = DEMO_DIR / "instruments.json"
    manifest_path.write_text(json.dumps(instruments_manifest, indent=2))
    print(f"wrote {manifest_path}")

    macro_dir = DEMO_DIR / "macro"
    macro_dir.mkdir(parents=True, exist_ok=True)
    buffett_payload = {
        "generation_method": "seeded random walk (demo synthetic data, NOT real FRED/Wilshire figures)",
        "seed": 2001,
        "quarterly_observations": generate_buffett_indicator_series(),
    }
    buffett_path = macro_dir / "buffett_indicator.json"
    buffett_path.write_text(json.dumps(buffett_payload, indent=2))
    print(f"wrote {buffett_path} ({len(buffett_payload['quarterly_observations'])} quarters)")


if __name__ == "__main__":
    main()
