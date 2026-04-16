"""Generate realistic mock daily stock price data for 5 tickers."""
import json
from pathlib import Path
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)

# Generate trading days (skip weekends) from 2023-01-03 to 2024-12-31
start = datetime(2023, 1, 3)
end = datetime(2024, 12, 31)
trading_days = []
d = start
while d <= end:
    if d.weekday() < 5:  # Mon-Fri
        trading_days.append(d.strftime("%Y-%m-%d"))
    d += timedelta(days=1)

n_days = len(trading_days)

# Ticker configs: start_price, end_price, avg_daily_vol, shrout (thousands)
tickers = {
    "AAPL": {"start": 130.0, "end": 250.0, "vol_mean": 55_000_000, "shrout": 15_700_000},
    "JPM":  {"start": 134.0, "end": 210.0, "vol_mean": 10_000_000, "shrout": 2_900_000},
    "JNJ":  {"start": 176.0, "end": 155.0, "vol_mean": 7_500_000,  "shrout": 2_420_000},
    "XOM":  {"start": 104.0, "end": 115.0, "vol_mean": 16_000_000, "shrout": 4_100_000},
    "WMT":  {"start": 145.0, "end": 170.0, "vol_mean": 8_000_000,  "shrout": 2_700_000},
}

result = {}

for ticker, cfg in tickers.items():
    start_p = cfg["start"]
    end_p = cfg["end"]

    # Compute drift needed to get from start to end over n_days
    # ln(end/start) = n * mu + sqrt(n) * sigma * Z  =>  mu ~ ln(end/start) / n
    total_log_return = np.log(end_p / start_p)
    daily_drift = total_log_return / n_days
    daily_vol = 0.015  # ~1.5% daily vol, realistic

    # Generate log returns with drift
    log_returns = daily_drift + daily_vol * np.random.randn(n_days)

    # Build price series
    log_prices = np.log(start_p) + np.cumsum(log_returns)
    prices = np.exp(log_prices)

    # Scale so last price is close to target (adjust for random walk deviation)
    # Linearly blend to hit the endpoint
    actual_end = prices[-1]
    correction = np.linspace(0, np.log(end_p / actual_end), n_days)
    prices = np.exp(np.log(prices) + correction)

    # Recompute returns from prices
    returns = np.diff(np.log(np.concatenate([[start_p], prices])))
    simple_returns = np.exp(returns) - 1.0

    # Generate volumes (log-normal around mean)
    vol_mean = cfg["vol_mean"]
    volumes = np.random.lognormal(
        mean=np.log(vol_mean) - 0.5 * 0.3**2,
        sigma=0.3,
        size=n_days
    ).astype(int)

    # Build records
    records = []
    for i in range(n_days):
        records.append({
            "date": trading_days[i],
            "prc": round(float(prices[i]), 2),
            "ret": round(float(simple_returns[i]), 6),
            "vol": int(volumes[i]),
            "shrout": cfg["shrout"]
        })

    result[ticker] = records

OUT = Path(__file__).resolve().parent / "price_data.json"
with open(OUT, "w") as f:
    json.dump(result, f, indent=2)

print(f"Written {OUT}")
print(f"Tickers: {list(result.keys())}")
print(f"Trading days: {n_days}")
for t in result:
    recs = result[t]
    print(f"  {t}: {len(recs)} days, price {recs[0]['prc']:.2f} -> {recs[-1]['prc']:.2f}")
