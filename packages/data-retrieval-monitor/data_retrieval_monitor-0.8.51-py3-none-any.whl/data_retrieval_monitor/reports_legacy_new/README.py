# example_run_pl_ready.py
from __future__ import annotations
import numpy as np
import pandas as pd
import polars as pl
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Local package layout expected:
#   /mnt/data/scores/base.py
#   /mnt/data/scores/metrics.py
#   /mnt/data/scores/validation.py  (exports qs_full_metrics_table and/or polars functions)
from scores.base import ScoreCollection
from scores.metrics import Sharpe, Sortino, VolatilityAnn, CAGR, MaxDrawdown, CustomScore
# We'll use the Polars-native metrics table if present

    # If you've merged the large Polars functions into scores/validation.py, they will be here:
from scores.metrics_pl import metrics_polars, monthly_returns_polars, compare_polars, to_pl_returns_df

    # # Fall back to minimal wrappers if your validation.py provides only qs_full_metrics_table
    # from scores.validation import qs_full_metrics_table as _qs_metrics
    # def to_pl_returns_df(x):
    #     if isinstance(x, pd.Series):
    #         return pl.DataFrame({"date": x.index.to_numpy(), "r": x.values})
    #     elif isinstance(x, pd.DataFrame):
    #         return pl.from_pandas(x.reset_index().rename(columns={"index":"date"}))
    #     elif isinstance(x, pl.DataFrame):
    #         return x
    #     else:
    #         raise TypeError("Unsupported type")
    # def metrics_polars(returns, benchmark=None, rf=0.0, display=False, mode="full", periods_per_year=252, **kwargs):
    #     # Compatibility wrapper: call QS if Polars version isn't available
    #     r_pd = returns.to_pandas().set_index("date")["r"] if "date" in returns.columns else returns.to_pandas()["r"]
    #     b_pd = None
    #     if benchmark is not None:
    #         b_pd = benchmark.to_pandas().set_index("date")["r"] if "date" in benchmark.columns else benchmark.to_pandas()["r"]
    #     return _qs_metrics(r_pd, b_pd, periods_per_year=periods_per_year)

# ----------------- dummy data (pandas first, then cast to polars) -----------------
np.random.seed(29)
dates = pd.bdate_range("2020-01-01", periods=50000)
ret1 = pd.Series(np.random.normal(0.0005, .01, len(dates)), index=dates, name="r")

bench = pd.Series(np.random.normal(0.0003, 0.009, len(dates)), index=dates, name="r")
rf = 0.02  # annual RF as float; you can pass a pd/pl series as well

# Cast to Polars with a proper 'date' column
ret_pl = pl.DataFrame({"date": pl.Series(dates), "r": ret.values})
bench_pl = pl.DataFrame({"date": pl.Series(dates), "r": bench.values})

# ----------------- compute a few scores with ScoreCollection (optional) -----------
# scores = ScoreCollection([Sharpe(), Sortino(), VolatilityAnn(), CAGR(), MaxDrawdown(), CustomScore()])
# score_table = scores.compute_for_frame(ret_pl["r"], rf=rf, periods_per_year=252)
# print("ScoreCollection (single series) ->", score_table)

# # ----------------- Polars-native QuantStats-style tables --------------------------
# metrics_df = metrics_polars(ret_pl, benchmark=bench_pl, rf=rf, display=False, mode="full", periods_per_year=252)
# print("\nmetrics_polars table (columns):", list(metrics_df.columns))

# # Monthly returns wide table (QS-compatible shape/labels)
# try:
#     monthly = monthly_returns_polars(ret_pl, eoy=True, compounded=True)
#     print("monthly_returns_polars shape:", monthly.shape)
# except Exception as e:
#     print("monthly_returns_polars not available in your validation module:", e)

# # Compare vs benchmark (QS-style)
# try:
#     cmp_df = compare_polars(ret_pl, bench_pl, aggregate=None, compounded=True, round_vals=4)
#     print("compare_polars columns:", list(cmp_df.columns))
# except Exception as e:
#     print("compare_polars not available:", e)

# ----------------- (Optional) Hook into your dashboard ----------------------------
# If your dashboard.QuantStatsDashboard expects pandas inputs, just convert:

from dashboard import QuantStatsDashboard, DashboardManifest
manifest = DashboardManifest(
figures=[
    "snapshot","earnings","returns","log_returns","yearly_returns",
    "daily_returns","rolling_beta","rolling_volatility",
    "rolling_sharpe","rolling_sortino","drawdowns_periods",
    "drawdown","monthly_heatmap","histogram","distribution",
],
metric_rows=[],  # canonical keys (case-insensitive, no spaces), e.g. ["startperiod","endperiod","sharpe"]
tables=["metrics","eoy","drawdown_details"],
metric_cols=["Benchmark","Strategy","Multi-Weighted"],  # uncomment to filter columns
# show the composite only
# composites={"Multi-Weighted": {"Strategy":0.6,"Strategy2":0.4}},
metric_groups=[
    {"": ["Risk-Free Rate", "Time in Market"]},
    {"": ["Cumulative Return", "CAGR﹪"]},
    {"": ["Sharpe", "Prob. Sharpe Ratio", "Smart Sharpe", "Sortino", "Smart Sortino", "Sortino/√2", "Smart Sortino/√2", "Omega"]},
    {"": ["Max Drawdown", "Max DD Date", "Max DD Period Start", "Max DD Period End", "Longest DD Days"]},
    {"": ["Volatility (ann.)", "R^2", "Information Ratio", "Calmar", "Skew", "Kurtosis"]},
    {"": ["Expected Daily", "Expected Monthly", "Expected Yearly"]},
    {"": ["Kelly Criterion", "Risk of Ruin"]},
    {"": ["Daily Value-at-Risk", "Expected Shortfall (cVaR)"]},
    {"": ["Max Consecutive Wins", "Max Consecutive Losses"]},
    {"": ["Gain/Pain Ratio", "Gain/Pain (1M)"]},
    {"": ["Payoff Ratio", "Profit Factor", "Common Sense Ratio", "CPC Index", "Tail Ratio", "Outlier Win Ratio", "Outlier Loss Ratio"]},
    {"": ["MTD", "3M", "6M", "YTD", "1Y", "3Y (ann.)", "5Y (ann.)", "10Y (ann.)", "All-time (ann.)"]},
    {"": ["Best Day", "Worst Day", "Best Month", "Worst Month", "Best Year", "Worst Year"]},
    {"": ["Avg. Drawdown", "Avg. Drawdown Days", "Recovery Factor", "Ulcer Index", "Serenity Index"]},
    {"": ["Avg. Up Month", "Avg. Down Month"]},
    {"": ["Win Days", "Win Month", "Win Quarter", "Win Year"]},
    {"": ["Beta", "Alpha", "Correlation", "Treynor Ratio"]}
    ],
)

QuantStatsDashboard(
    returns_df=ret.to_frame('Strategy'),
    benchmark=bench,
    rf=rf,
    title="Strategy Tearsheet (Polars metrics backend)",
    output_dir="output/comprehensive_reports",
    manifest=manifest,
    periods_per_year=252,
)

