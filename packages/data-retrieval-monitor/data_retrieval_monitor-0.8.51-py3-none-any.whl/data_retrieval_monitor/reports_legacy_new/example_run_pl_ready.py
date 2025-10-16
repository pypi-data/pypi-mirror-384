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
from scores.metrics_polars import metrics_polars, monthly_returns_polars, compare_polars, to_pl_returns_df

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
np.random.seed(42)
dates = pd.bdate_range("2020-01-01", periods=1000)
ret = pd.Series(np.random.normal(0.0005, 0.01, len(dates)), index=dates, name="r")
bench = pd.Series(np.random.normal(0.0003, 0.009, len(dates)), index=dates, name="r")
rf = 0.02  # annual RF as float; you can pass a pd/pl series as well

# Cast to Polars with a proper 'date' column
ret_pl = pl.DataFrame({"date": pl.Series(dates), "r": ret.values})
bench_pl = pl.DataFrame({"date": pl.Series(dates), "r": bench.values})

# ----------------- compute a few scores with ScoreCollection (optional) -----------
scores = ScoreCollection([Sharpe(), Sortino(), VolatilityAnn(), CAGR(), MaxDrawdown(), CustomScore()])
score_table = scores.compute_for_frame(ret_pl["r"], rf=rf, periods_per_year=252)
print("ScoreCollection (single series) ->", score_table)

# ----------------- Polars-native QuantStats-style tables --------------------------
metrics_df = metrics_polars(ret_pl, benchmark=bench_pl, rf=rf, display=False, mode="full", periods_per_year=252)
print("\nmetrics_polars table (columns):", list(metrics_df.columns))

# Monthly returns wide table (QS-compatible shape/labels)
try:
    monthly = monthly_returns_polars(ret_pl, eoy=True, compounded=True)
    print("monthly_returns_polars shape:", monthly.shape)
except Exception as e:
    print("monthly_returns_polars not available in your validation module:", e)

# Compare vs benchmark (QS-style)
try:
    cmp_df = compare_polars(ret_pl, bench_pl, aggregate=None, compounded=True, round_vals=4)
    print("compare_polars columns:", list(cmp_df.columns))
except Exception as e:
    print("compare_polars not available:", e)

# ----------------- (Optional) Hook into your dashboard ----------------------------
# If your dashboard.QuantStatsDashboard expects pandas inputs, just convert:
try:
    from dashboard import QuantStatsDashboard, DashboardManifest
    manifest = DashboardManifest(
        figures=[
            "rolling_sharpe", "drawdowns", "monthly_returns_heatmap",
            "distribution", "rolling_sortino", "rolling_vol"
        ],
        tables=["metrics", "eoy", "drawdown_details"],
    )
    QuantStatsDashboard(
        returns_df=ret.to_frame("r"),
        benchmark=bench,
        rf=rf,
        title="Strategy Tearsheet (Polars metrics backend)",
        output_dir="output/comprehensive_reports",
        manifest=manifest,
        periods_per_year=252,
    )
except Exception as e:
    # dashboard.py may be incomplete here; in your environment it should work.
    print("Dashboard invocation skipped:", e)
