# dashboard.py
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Dict, Optional, Union
from datetime import datetime
import numpy as np
import pandas as pd
import quantstats as qs
from quantstats import stats as qs_stats
from quantstats import plots as qs_plots
import json
import matplotlib.pyplot as plt
import polars as pl

# -----------------------
# Helper: filesystem
# -----------------------
def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def _pl_frame_from_index(idx: pd.DatetimeIndex, values: np.ndarray,
                         date_col: str = "date", val_col: str = "ret") -> pl.DataFrame:
    """
    Build a Polars frame with a guaranteed Datetime column so .dt.year/.dt.month work.
    """
    idx = pd.DatetimeIndex(idx).tz_localize(None)
    # Use Python datetimes; Polars will happily cast these to pl.Datetime
    py_dt = list(idx.to_pydatetime())
    date_s = pl.Series(date_col, py_dt).cast(pl.Datetime)
    val_s  = pl.Series(val_col, np.asarray(values, dtype=np.float64))
    return pl.DataFrame({date_col: date_s, val_col: val_s})


# -----------------------
# Risk-free + alignment
# -----------------------
def _align_like(obj: Union[pd.Series, pd.DataFrame, float, int],
                index: pd.DatetimeIndex,
                fill: float = 0.0) -> pd.Series:
    """
    Align rf-like object to index.
    - float/int -> constant Series
    - Series -> reindex fill
    - DataFrame -> first column
    """
    if isinstance(obj, (float, int)):
        return pd.Series(float(obj), index=index, name="rf")
    if isinstance(obj, pd.DataFrame):
        s = obj.iloc[:, 0] if obj.shape[1] > 1 else obj.squeeze("columns")
        s = s.reindex(index).fillna(fill)
        s.name = "rf"
        return s
    if isinstance(obj, pd.Series):
        s = obj.reindex(index).fillna(fill)
        s.name = "rf"
        return s
    return pd.Series(fill, index=index, name="rf")


def _maybe_excess_returns(returns_pd: pd.DataFrame,
                          rf: Optional[Union[float, int, pd.Series, pd.DataFrame]],
                          periods_per_year: int) -> pd.DataFrame:
    """
    Convert returns to excess returns if rf provided.
    float/int -> treated as ANNUAL rf, converted to per-period.
    Series/DataFrame -> assumed per-period and aligned.
    """
    rets = returns_pd.copy()
    try:
        rets.index = rets.index.tz_localize(None)
    except Exception:
        pass

    if rf is None:
        return rets

    if isinstance(rf, (float, int)):
        pprf = (1.0 + float(rf)) ** (1.0 / periods_per_year) - 1.0
        return rets - pprf

    rf_series = _align_like(rf, rets.index, fill=0.0)
    return rets.sub(rf_series, axis=0)


# -----------------------
# Canonical figure & table lists
# -----------------------
DEFAULT_FIGURES = [
    "snapshot",
    "earnings",
    "returns",
    "log_returns",
    "yearly_returns",
    "daily_returns",
    "rolling_beta",
    "rolling_volatility",
    "rolling_sharpe",
    "rolling_sortino",
    "drawdowns_periods",
    "drawdown",
    "monthly_heatmap",
    "histogram",
    "distribution",
]

ALL_TABLES = ["metrics", "eoy", "monthly_returns", "drawdown_details"]


# -----------------------
# Manifest: choose subsets
# -----------------------


from dataclasses import dataclass
from typing import List, Dict, Optional, Union

@dataclass
class DashboardManifest:
    figures: Optional[List[str]] = None                  # subset of DEFAULT_FIGURES
    metric_rows: Optional[List[str]] = None              # canonical row keys (case-insensitive, alnum-only)
    metric_cols: Optional[List[str]] = None              # which columns to show in metrics (default = Benchmark + rendered strats)
    tables: Optional[List[str]] = None                   # subset of ALL_TABLES
    tables_same_length_group: Optional[List[str]] = None # e.g. ["metrics","eoy","drawdown_details"]

    # Show only these strategies in figures & per-strategy tables (case-insensitive).
    # If omitted and composites are defined, we'll render ONLY the composite(s).
    strategy_filter: Optional[List[str]] = None

    # Grouped metrics — order respected; draws separators between groups.
    # Example:
    # metric_groups = [
    #   {"Risk/Return": ["sharpe","sortino","cagr","volatility (ann.)"]},
    #   {"Drawdowns":   ["max drawdown","recovery factor","avg. down month"]}
    # ]
    metric_groups: Optional[List[Dict[str, List[str]]]] = None

    # Define composite “multi” columns from your strategies.
    # Examples:
    #   {"Multi": "equal"}                             -> equal-weight across all strategies (nan-safe)
    #   {"Multi": {"Strategy1":0.6,"Strategy2":0.4}}  -> static weights (auto-normalized)
    composites: Optional[Dict[str, Union[str, Dict[str, float]]]] = None
    # NEW: optional correlation filters you can reference by name in figures
    # e.g. figures=["corr_monthly","corr_monthly_RegimeA"]
    # correlation_filters={"RegimeA":[("2020-01-01","2020-12-31"),("2022-01-01","2022-06-30")]}
    correlation_filters: Optional[Dict[str, Union[
        List[tuple],     # list of (start,end) ISO strings
        pd.Series        # boolean mask indexed by date
    ]]] = None

# -----------------------
# Main Dashboard
# -----------------------
class QuantStatsDashboard:
    # -----------------------
    # Small helpers
    # -----------------------
    @staticmethod
    def _norm_key(s: str) -> str:
        return "".join(ch.lower() for ch in s if ch.isalnum())

    def _norm_name_list(self, names: List[str], pool: List[str]) -> List[str]:
        """Case-insensitive exact match of names against pool, preserving pool order."""
        want = {n.lower() for n in names}
        return [p for p in pool if p.lower() in want]

    def _percent_metric_keys(self) -> set[str]:
        """
        Metric names that should render as percentages — aligned with QS.
        Uses your available metrics list and the conventional QS rows that
        are shown with '%' in the stock report.
        """
        percent_like = {
            # rates/returns/exposures
            "Risk-Free Rate", "Time in Market", "Cumulative Return", "CAGR﹪",
            "Volatility (ann.)", "Max Drawdown",
            "Expected Daily", "Expected Monthly", "Expected Yearly",
            "Daily Value-at-Risk", "Expected Shortfall (cVaR)",
            "MTD", "3M", "6M", "YTD", "1Y",
            "3Y (ann.)", "5Y (ann.)", "10Y (ann.)", "All-time (ann.)",
            "Best Day", "Worst Day", "Best Month", "Worst Month", "Best Year", "Worst Year",
            "Avg. Drawdown", "Avg. Up Month", "Avg. Down Month",
            "Win Days", "Win Month", "Win Quarter", "Win Year",
            "Risk of Ruin",
        }
        # Keep only ones that exist in the current metrics index
        idx = {self._norm_key(i): i for i in getattr(self, "metrics_df", pd.DataFrame()).index} if hasattr(self, "metrics_df") else {}
        return {self._norm_key(n) for n in percent_like if self._norm_key(n) in idx}

    def _pct(self, v, places: int = 2) -> str:
        """Format a float as a percentage, trimming trailing .0s (e.g., 3.00% -> 3%)."""
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return "-"
        if not isinstance(v, (int, float, np.floating)):
            return str(v)
        s = f"{v * 100:.{places}f}".rstrip("0").rstrip(".")
        return f"{s}%"
    
    def _format_metrics_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return a copy of df where percent-like rows are rendered with %."""
        pct_keys = self._percent_metric_keys()
        if df is None or df.empty or not pct_keys:
            return df

        def fmt_row(label: str, values: pd.Series) -> pd.Series:
            nk = self._norm_key(label)
            if nk in pct_keys:
                return values.map(lambda v: self._pct(v, 2))
            return values

        out = df.copy()
        out = pd.DataFrame([fmt_row(lbl, out.loc[lbl]) for lbl in out.index], index=out.index, columns=out.columns)
        return out
    def _compute_composites(
        self,
        df: pd.DataFrame,
        spec: Dict[str, Union[str, Dict[str, float]]]
    ) -> pd.DataFrame:
        """
        Append composite strategy columns to df.

        - 'equal' -> equal-weight across current df columns per date (nan-safe)
        - dict weights -> static weights by column name (auto-normalized)
        """
        if not spec:
            return df

        base = df.copy()
        cols = list(base.columns)

        for name, rule in spec.items():
            if isinstance(rule, str) and rule.lower() in ("equal", "ew", "eq"):
                # equal weight each date among available columns (nan-safe)
                w = pd.DataFrame(1.0 / len(cols), index=base.index, columns=cols)
                comp = (base * w).sum(axis=1, min_count=1)

            elif isinstance(rule, dict):
                # static weights
                use = {k: float(v) for k, v in rule.items() if k in cols}
                if not use:
                    continue
                s = sum(use.values())
                if s == 0:
                    continue
                use = {k: v / s for k, v in use.items()}
                comp = sum(base[k] * use[k] for k in use.keys())

            else:
                continue

            comp.name = name
            base[name] = comp

        return base

    def __init__(
        self,
        returns_df: pd.DataFrame,
        benchmark: Optional[pd.Series] = None,
        rf: Optional[Union[float, int, pd.Series, pd.DataFrame]] = None,
        title: str = "Strategy Tearsheet",
        output_dir: str = "output/comprehensive_reports",
        manifest: Optional[DashboardManifest] = None,
        periods_per_year: int = 252,
    ) -> None:
        import json
        self.ppy = periods_per_year
        self.title = title
        self.output_dir = output_dir
        self.manifest = manifest
        _ensure_dir(self.output_dir)

        # --- clean inputs
        self.returns_pd = returns_df.copy()
        if isinstance(self.returns_pd, pd.Series):
            self.returns_pd = self.returns_pd.to_frame()
        self.returns_pd.index = pd.DatetimeIndex(self.returns_pd.index).tz_localize(None)
        self.returns_pd = self.returns_pd.sort_index()

        self.benchmark = benchmark.copy() if benchmark is not None else None
        if self.benchmark is not None:
            self.benchmark.index = pd.DatetimeIndex(self.benchmark.index).tz_localize(None)
            self.benchmark = self.benchmark.sort_index()

        # --- add composite(s) on ORIGINAL returns if requested
        if manifest and manifest.composites:
            self.returns_pd = self._compute_composites(self.returns_pd, manifest.composites)

        # All strategies (including composites if any)
        self.strategies = list(self.returns_pd.columns)

        # Align with benchmark if present
        if self.benchmark is not None:
            common_idx = self.returns_pd.index.intersection(self.benchmark.index)
            self.returns_pd = self.returns_pd.loc[common_idx]
            self.benchmark = self.benchmark.loc[common_idx]

        # --- Convert to EXCESS once; we keep rf=0.0 in QS calls for consistency
        self.returns_excess = _maybe_excess_returns(self.returns_pd, rf, self.ppy)
        self.benchmark_excess = None
        if self.benchmark is not None:
            self.benchmark_excess = _maybe_excess_returns(self.benchmark.to_frame("bench"), rf, self.ppy)["bench"]

        # --- What to render?
        # If composites are provided and strategy_filter is NOT set,
        # Default: render EVERYTHING that exists in returns_pd (originals + composites).
        # Only restrict if user passes an explicit strategy_filter, or later via metric_cols.
        if manifest and manifest.strategy_filter:
            self.render_strategies = self._norm_name_list(manifest.strategy_filter, self.strategies) or self.strategies[:]
        else:
            self.render_strategies = self.strategies[:]

        # date range
        self.start = self.returns_excess.index.min().strftime("%Y-%m-%d")
        self.end = self.returns_excess.index.max().strftime("%Y-%m-%d")
        self.date_range_str = f"{self.start} — {self.end}"

        # manifest
        self.fig_list = (manifest.figures if manifest and manifest.figures else DEFAULT_FIGURES)

        # tables subset
        if manifest and manifest.tables:
            self.tables_list = [t for t in manifest.tables if t in ALL_TABLES]
            if not self.tables_list:
                self.tables_list = ALL_TABLES.copy()
        else:
            self.tables_list = ALL_TABLES.copy()

        # metric rows filter (canonical exact keys)
        self.metric_rows_filter = None
        if manifest and manifest.metric_rows:
            self.metric_rows_filter = [self._norm_key(k) for k in manifest.metric_rows]

        # metric columns filter: default = Benchmark + render_strategies, unless provided
        self.default_metric_cols = (["Benchmark"] if self.benchmark_excess is not None else []) + self.render_strategies
        self.metric_cols_filter = None
        if manifest and manifest.metric_cols:
            self.metric_cols_filter = self._norm_name_list(
                manifest.metric_cols,
                (["Benchmark"] if self.benchmark_excess is not None else []) + self.strategies
            )
            figs_cols = [c for c in self.metric_cols_filter if c.lower() != "benchmark" and c in self.strategies]
            if figs_cols:
                self.render_strategies = figs_cols
        
        # output paths
        self.fig_dir = os.path.join(self.output_dir, "figures")
        _ensure_dir(self.fig_dir)
        self.html_path = os.path.join(self.output_dir, "dashboard.html")
        self.manifest_path = os.path.join(self.output_dir, "available_manifest.json")

        # build
        self._save_manifest()
        self._build_figures()
        self._build_tables()
        self._write_html()

    # -----------------------
    # Manifest of available things
    # -----------------------
    def _save_manifest(self) -> None:
        import json
        full_metrics = self._compute_metrics_table(full=True)
        keys = list(full_metrics.index)
        manifest = {
            "figures_available": DEFAULT_FIGURES,
            "tables_available": ALL_TABLES,
            "metric_rows": keys,
            "metric_cols": (["Benchmark"] if self.benchmark_excess is not None else []) + self.strategies,
            "date_range": [self.start, self.end],
        }
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        print(f"[manifest] wrote: {self.manifest_path}")

    # -----------------------
    # Metrics (QS on ORIGINAL returns; QS preps internally)
    # -----------------------
    def _compute_metrics_table(self, full: bool = False) -> pd.DataFrame:
        """
        Metrics via QuantStats on EXCESS returns (rf already removed),
        so Sharpe/Sortino match the plots. Handles 1-column and multi-column.
        """
        mode = "full" if full else "basic"
        ret_in = self.returns_excess.copy()
        bench_in = self.benchmark_excess.copy() if self.benchmark_excess is not None else None

        # QS: pass a Series for single-column case
        if isinstance(ret_in, pd.DataFrame) and ret_in.shape[1] == 1:
            ret_in = ret_in.iloc[:, 0]

        try:
            m = qs.reports.metrics(
                returns=ret_in,
                benchmark=bench_in,
                rf=0.0,
                display=False,
                mode=mode,
                compounded=True,
                prepare_returns=False,   # already excess/prepared
                periods_per_year=self.ppy,
            )
        except Exception as e:
            print(f"[metrics] fallback due to: {e}")
            if isinstance(ret_in, pd.Series):
                ret_in = ret_in.to_frame(ret_in.name or "Strategy")
            cols = []
            for c in ret_in.columns:
                s = ret_in[c].dropna()
                if s.empty:
                    cols.append(pd.Series({
                        "Start Period": np.nan, "End Period": np.nan,
                        "CAGR": np.nan, "Volatility (ann.)": np.nan, "Sharpe": np.nan
                    }, name=c))
                    continue
                ann_ret = (1 + s).prod() ** (self.ppy / max(1, len(s))) - 1.0
                ann_vol = s.std(ddof=0) * np.sqrt(self.ppy)
                sharpe  = (s.mean() * self.ppy) / ann_vol if ann_vol != 0 else np.nan
                cols.append(pd.Series({
                    "Start Period": s.index.min(), "End Period": s.index.max(),
                    "CAGR": ann_ret, "Volatility (ann.)": ann_vol, "Sharpe": sharpe
                }, name=c))
            m = pd.concat(cols, axis=1)

        if isinstance(m, pd.Series):
            # name for 1-col result
            name = ret_in.name if isinstance(ret_in, pd.Series) else (ret_in.columns[0] if ret_in.shape[1] else "Strategy")
            m = m.to_frame(name=name)

        m.index.name = "Metric"
        return m

    
    
    # -----------------------
    # EOY Returns (per strategy)
    # -----------------------
    def _eoy_table(self) -> Dict[str, pd.DataFrame]:
        """
        Per-strategy EOY comparison (on EXCESS returns):
        columns = Year | Benchmark | Strategy | Multiplier | Won
        Implemented with Polars; returned as pandas for rendering.
        """
        out: Dict[str, pd.DataFrame] = {}

        # ---- Benchmark map by year (Polars; ensure real Datetime dtype)
        bench_map: Dict[int, float] = {}
        if self.benchmark_excess is not None:
            b = self.benchmark_excess.dropna()
            if not b.empty:
                bpl = _pl_frame_from_index(b.index, b.values)  # date: Datetime, ret: Float64
                by = (
                    bpl.with_columns(pl.col("date").dt.year().alias("year"))
                    .group_by("year")
                    .agg(((pl.col("ret") + 1.0).product() - 1.0).alias("bench_eoy"))
                    .sort("year")
                )
                bench_map = dict(zip(by["year"].to_list(), by["bench_eoy"].to_list()))

        # ---- Strategies
        for col in self.strategies:
            s = self.returns_excess[col].dropna()
            if s.empty:
                out[col] = pd.DataFrame(columns=["Year", "Benchmark", "Strategy", "Multiplier", "Won"])
                continue

            spl = _pl_frame_from_index(s.index, s.values)
            sy = (
                spl.with_columns(pl.col("date").dt.year().alias("year"))
                .group_by("year")
                .agg(((pl.col("ret") + 1.0).product() - 1.0).alias("strat_eoy"))
                .sort("year")
            )

            df = sy.to_pandas().rename(columns={"year": "Year", "strat_eoy": "Strategy"})

            if bench_map:
                df["Benchmark"] = df["Year"].map(bench_map).astype(float)
            else:
                df["Benchmark"] = np.nan

            bench = df["Benchmark"].to_numpy()
            strat = df["Strategy"].to_numpy()
            with np.errstate(divide="ignore", invalid="ignore"):
                mult = np.where(np.isfinite(bench) & (np.abs(bench) > 1e-12), strat / bench, np.nan)
            df["Multiplier"] = mult
            df["Won"] = np.where(np.isfinite(strat) & np.isfinite(bench),
                                np.where(strat > bench, "+", "–"), "")

            out[col] = df[["Year", "Benchmark", "Strategy", "Multiplier", "Won"]].reset_index(drop=True)

        return out

    def _monthly_tables(self) -> Dict[str, pd.DataFrame]:
        """
        Per-strategy monthly returns on EXCESS returns, computed with Polars,
        returned as pandas (rows = year, cols = Jan..Dec).
        """
        res: Dict[str, pd.DataFrame] = {}
        for col in self.strategies:
            ser = self.returns_excess[col].dropna()
            if ser.empty:
                res[col] = pd.DataFrame()
                continue

            dfpl = _pl_frame_from_index(ser.index, ser.values)

            m = (
                dfpl.with_columns([
                        pl.col("date").dt.year().alias("year"),
                        pl.col("date").dt.month().alias("month"),
                    ])
                    .group_by(["year", "month"])
                    .agg(((pl.col("ret") + 1.0).product() - 1.0).alias("mret"))
                    .sort(["year", "month"])
            )

            wide = m.pivot(index="year", columns="month", values="mret").sort("year")
            pdf = wide.to_pandas().set_index("year")

            from datetime import datetime as _dt
            pdf.columns = [_dt(2000, int(c), 1).strftime("%b") for c in pdf.columns]
            res[col] = pdf

        return res

    # -----------------------
    # Drawdown details per strategy
    # -----------------------
    def _drawdown_tables(self) -> Dict[str, pd.DataFrame]:
        """
        Worst drawdowns per strategy computed fully in Polars, returned as pandas.
        Also left-align the 'Recovered' header and cell contents without touching CSS/HTML writers.
        """
        out: Dict[str, pd.DataFrame] = {}

        for col in self.strategies:
            s = self.returns_excess[col].dropna()
            if s.empty:
                out[col] = pd.DataFrame()
                continue

            # Build Polars frame: date (Datetime), ret (Float64)
            dfpl = _pl_frame_from_index(s.index, s.values).sort("date")

            # equity curve, peak, drawdown, episode grouping
            dfpl = (
                dfpl
                .with_columns((1.0 + pl.col("ret")).cum_prod().alias("equity"))
                .with_columns(pl.col("equity").cum_max().alias("peak"))
                .with_columns((pl.col("equity") / pl.col("peak") - 1.0).alias("dd"))
                .with_columns((pl.col("dd") < -1e-12).alias("is_dd"))
                .with_columns(((pl.col("is_dd") & (~pl.col("is_dd").shift(1).fill_null(False))).cast(pl.Int64)).alias("start_flag"))
                .with_columns(pl.col("start_flag").cum_sum().alias("grp"))
            )

            dd_only = dfpl.filter(pl.col("is_dd"))
            if dd_only.height == 0:
                out[col] = pd.DataFrame()
                continue

            # Aggregate each drawdown episode
            blocks = (
                dd_only
                .group_by("grp")
                .agg([
                    pl.col("date").first().alias("Started"),
                    pl.col("date").last().alias("EndBlock"),
                    # trough date == date at min dd (workaround: sort by dd and take first)
                    pl.col("date").sort_by(pl.col("dd")).first().alias("Trough"),
                    pl.col("dd").min().alias("min_dd"),
                    pl.count().alias("Days"),
                ])
                .sort("min_dd")  # most negative first
            )

            # First recovery date >= EndBlock where dd >= 0
            zeros = (
                dfpl
                .filter(pl.col("dd") >= -1e-12)
                .select([pl.col("date").alias("join_key"), pl.col("date").alias("Recovered")])
                .sort("join_key")
            )
            joined = (
                blocks
                .with_columns(pl.col("EndBlock").alias("join_key"))
                .sort("join_key")
                .join_asof(zeros, on="join_key", strategy="forward")
            )

            pdf = (
                joined
                .select([
                    pl.col("Started"),
                    pl.col("Recovered"),
                    (pl.col("min_dd") * 100.0).alias("Drawdown"),
                    pl.col("Days"),
                ])
                .head(10)
                .to_pandas()
            )

            # Pretty + left-aligned dates for 'Recovered'
            def _fmt_date_left(x):
                if pd.isna(x):
                    return "-"
                d = pd.to_datetime(x)
                txt = d.strftime("%Y-%m-%d")
                return f"<span style='display:block;text-align:left'>{txt}</span>"

            if "Recovered" in pdf.columns:
                pdf["Recovered"] = pdf["Recovered"].map(_fmt_date_left)

            # Left-align the *header* too (no CSS change needed)
            new_cols = []
            for c in pdf.columns:
                if c == "Recovered":
                    new_cols.append("<span style='display:block;text-align:left'>Recovered</span>")
                else:
                    new_cols.append(c)
            pdf.columns = new_cols

            out[col] = pdf

        return out

    # -----------------------
    # Build figures (per rendered strategy) — QuantStats defaults.
    # Cumulative-return style plots include benchmark when available.
    # -----------------------
    def _build_figures(self) -> None:
        self.fig_paths: Dict[str, Dict[str, str]] = {col: {} for col in self.render_strategies}
        bench = self.benchmark_excess  # may be None

        def _save(fig, fname: str):
            if fig is None:
                return
            p = os.path.join(self.fig_dir, fname)
            fig.savefig(p, dpi=144, bbox_inches="tight")
            try:
                plt.close(fig)
            except Exception:
                pass
            return p

        for col in self.render_strategies:
            s = self.returns_excess[col].dropna()
            if s.empty:
                continue

            for f in self.fig_list:
                fig_obj = None
                try:
                    if f == "snapshot":
                        fig_obj = qs_plots.snapshot(s, show=False)
                    elif f == "earnings":
                        fig_obj = qs_plots.earnings(s, show=False)
                    elif f == "returns":
                        fig_obj = qs_plots.returns(s, benchmark=bench, show=False)
                    elif f == "log_returns":
                        fig_obj = qs_plots.log_returns(s, benchmark=bench, show=False)
                    elif f == "yearly_returns":
                        fig_obj = qs_plots.yearly_returns(s, benchmark=bench, show=False)
                    elif f == "daily_returns":
                        fig_obj = qs_plots.daily_returns(s, benchmark=bench, show=False)
                    elif f == "rolling_beta":
                        if bench is not None:
                            fig_obj = qs_plots.rolling_beta(s, bench, show=False)
                    elif f == "rolling_volatility":
                        try:
                            fig_obj = qs_plots.rolling_volatility(s, benchmark=bench, show=False)
                        except TypeError:
                            fig_obj = qs_plots.rolling_volatility(s, show=False)
                    elif f == "rolling_sharpe":
                        fig_obj = qs_plots.rolling_sharpe(s, show=False)
                    elif f == "rolling_sortino":
                        fig_obj = qs_plots.rolling_sortino(s, show=False)
                    elif f == "drawdowns_periods":
                        fig_obj = qs_plots.drawdowns_periods(s, show=False)
                    elif f == "drawdown":
                        fig_obj = qs_plots.drawdown(s, show=False)
                    elif f == "monthly_heatmap":
                        if bench is not None:
                            try:
                                fig_obj = qs_plots.monthly_heatmap(s, benchmark=bench, show=False)
                            except TypeError:
                                fig_obj = qs_plots.monthly_heatmap(s, show=False)
                        else:
                            fig_obj = qs_plots.monthly_heatmap(s, show=False)
                    elif f == "histogram":
                        fig_obj = qs_plots.histogram(s, benchmark=bench, show=False)
                    elif f == "distribution":
                        fig_obj = qs_plots.distribution(s, show=False)
                    else:
                        continue

                    if fig_obj is not None:
                        fp = _save(fig_obj, f"{f}_{col}.png")
                        if fp:
                            self.fig_paths[col][f] = fp
                except Exception as e:
                    print(f"[plot] failed: {f}({col}) -> {e}")

    def _build_tables(self) -> None:
        # Metrics
        full_m = self._compute_metrics_table(full=True)

        # Row filter
        if self.metric_rows_filter:
            idx_map = {self._norm_key(i): i for i in full_m.index}
            keep_keys = [idx_map[k] for k in self.metric_rows_filter if k in idx_map]
            metrics_df = full_m.loc[keep_keys] if keep_keys else full_m
        else:
            metrics_df = full_m

        # Column filter default = Benchmark + render_strategies
        default_cols = (["Benchmark"] if self.benchmark_excess is not None else []) + getattr(self, "render_strategies", self.strategies)
        if self.metric_cols_filter:
            keep_cols = [c for c in self.metric_cols_filter if c in metrics_df.columns]
        else:
            keep_cols = [c for c in default_cols if c in metrics_df.columns]
        if keep_cols:
            metrics_df = metrics_df[keep_cols]

        # Benchmark first
        cols = list(metrics_df.columns)
        if "Benchmark" in cols:
            cols = ["Benchmark"] + [c for c in cols if c != "Benchmark"]
            metrics_df = metrics_df[cols]
        self.metrics_df = metrics_df
        # Pre-render grouped metrics (if provided)
        self.metrics_html = None
        if self.manifest and self.manifest.metric_groups:
            self.metrics_html = self._render_metrics_grouped(self.metrics_df, self.manifest.metric_groups)
        else:
            # Plain table: still pretty-print percent rows like QS
            pretty = self._format_metrics_dataframe(self.metrics_df)
            self.metrics_html = pretty.to_html(border=0, escape=False)
        # Pre-render grouped metrics (if provided)
        self.metrics_html = None
        if self.manifest and self.manifest.metric_groups:
            self.metrics_html = self._render_metrics_grouped(self.metrics_df, self.manifest.metric_groups)

        # Restrict to render_strategies for per-strategy tables
        wanted = set(getattr(self, "render_strategies", self.strategies))

        # EOY / Monthly / Drawdown
        self.eoy_map = {k: v for k, v in self._eoy_table().items() if k in wanted}
        self.monthly_map = {k: v for k, v in self._monthly_tables().items() if k in wanted}
        self.dd_map = {k: v for k, v in self._drawdown_tables().items() if k in wanted}
    # -----------------------
    # Grouped metrics renderer (custom HTML/CSS per your spec)
    # -----------------------
    def _render_metrics_grouped(self, df: pd.DataFrame, groups: List[Dict[str, List[str]]]) -> str:
        if df is None or df.empty:
            return "<div style='color:#888;'>No metrics.</div>"

        idx_map = {self._norm_key(i): i for i in df.index}
        cols = list(df.columns)

        html = []
        html.append('<table class="metrics-grouped">')
        # header
        html.append('<thead><tr>')
        html.append('<th>Metric</th>')
        for c in cols:
            html.append(f'<th>{c}</th>')
        html.append('</tr></thead>')
        # body
        html.append('<tbody>')

        first_group = True
        for grp in groups:
            (gname, keys) = next(iter(grp.items()))
            if not first_group:
                # horizontal separator between groups
                html.append(f'<tr class="sep"><td colspan="{len(cols)+1}"></td></tr>')
            first_group = False

            # (Optional) group label as a faint row (no bold)
            html.append(f'<tr class="glabel"><td class="mname" colspan="{len(cols)+1}">{gname}</td></tr>')

            for key in keys:
                nk = self._norm_key(key)
                if nk not in idx_map:
                    continue
                label = idx_map[nk]
                row = df.loc[label]
                html.append('<tr>')
                html.append(f'<td class="mname">{label}</td>')
                pct_keys = self._percent_metric_keys()
                for c in cols:
                    val = row.get(c, "")
                    if isinstance(val, (float, int, np.floating)) and self._norm_key(label) in pct_keys:
                        cell = self._pct(val, 2)
                    else:
                        cell = f"{val}" if pd.notna(val) else "-"
                    html.append(f'<td class="mval">{cell}</td>')
                html.append('</tr>')

        html.append('</tbody></table>')
        return "".join(html)

    # -----------------------
    # Build tables
    # -----------------------
    def _compute_metrics_table(self, full: bool = False) -> pd.DataFrame:
        """
        Metrics via QuantStats on EXCESS returns (rf already removed),
        so Sharpe/Sortino match the plots. Handles 1-column and multi-column.
        """
        mode = "full" if full else "basic"
        ret_in = self.returns_excess.copy()
        bench_in = self.benchmark_excess.copy() if self.benchmark_excess is not None else None

        # QS: pass a Series for single-column case
        if isinstance(ret_in, pd.DataFrame) and ret_in.shape[1] == 1:
            ret_in = ret_in.iloc[:, 0]

        try:
            m = qs.reports.metrics(
                returns=ret_in,
                benchmark=bench_in,
                rf=0.0,
                display=False,
                mode=mode,
                compounded=True,
                prepare_returns=False,   # already excess/prepared
                periods_per_year=self.ppy,
            )
        except Exception as e:
            print(f"[metrics] fallback due to: {e}")
            if isinstance(ret_in, pd.Series):
                ret_in = ret_in.to_frame(ret_in.name or "Strategy")
            cols = []
            for c in ret_in.columns:
                s = ret_in[c].dropna()
                if s.empty:
                    cols.append(pd.Series({
                        "Start Period": np.nan, "End Period": np.nan,
                        "CAGR": np.nan, "Volatility (ann.)": np.nan, "Sharpe": np.nan
                    }, name=c))
                    continue
                ann_ret = (1 + s).prod() ** (self.ppy / max(1, len(s))) - 1.0
                ann_vol = s.std(ddof=0) * np.sqrt(self.ppy)
                sharpe  = (s.mean() * self.ppy) / ann_vol if ann_vol != 0 else np.nan
                cols.append(pd.Series({
                    "Start Period": s.index.min(), "End Period": s.index.max(),
                    "CAGR": ann_ret, "Volatility (ann.)": ann_vol, "Sharpe": sharpe
                }, name=c))
            m = pd.concat(cols, axis=1)

        if isinstance(m, pd.Series):
            # name for 1-col result
            name = ret_in.name if isinstance(ret_in, pd.Series) else (ret_in.columns[0] if ret_in.shape[1] else "Strategy")
            m = m.to_frame(name=name)

        m.index.name = "Metric"
        return m

    # -----------------------
    # HTML writer
    # -----------------------

    def _write_html(self) -> None:
        import json
        # which tables the right slider should keep in sync
        if getattr(self, "manifest", None) and getattr(self.manifest, "tables_same_length_group", None):
            group_keys = list(self.manifest.tables_same_length_group)
        else:
            group_keys = ["metrics", "eoy", "drawdown_details"]
        # initial left/right split based on rendered strategies count
        n = max(1, len(getattr(self, "render_strategies", self.strategies)))
        left_pct = round(min(n, 3) * (100.0 / 3.0), 2) # 1→33%, 2→66%, 3+→100%
        left_pct = min(left_pct, 75.0)
        right_pct = round(100.0 - left_pct, 2)
        # -------- Figures HTML (unchanged layout)
        fig_rows_html = []
        for f in self.fig_list:
            tiles, headers, have = [], [], 0
            for col in getattr(self, "render_strategies", self.strategies):
                p = self.fig_paths.get(col, {}).get(f)
                if p and os.path.isfile(p):
                    have += 1
                    # headers.append(f"""<div class="fig-header">Strategy: {col}</div>""")
                    tiles.append(
                        f"""<div class="thumb"><img src="{os.path.relpath(p, self.output_dir)}" alt="{f.replace('_',' ').title()} for {col}" data-zoom="1"/></div>"""
                    )
            if have == 0:
                continue
            fig_rows_html.append(f"""
                <div class="fig-row">
                    <div class="fig-headers" style="grid-template-columns: repeat({have}, 1fr);">
                        {''.join(headers)}
                    </div>
                    <div class="fig-grid" style="grid-template-columns: repeat({have}, 1fr);">
                        {''.join(tiles)}
                    </div>
                </div>
                """)
        figures_html = "\n".join(fig_rows_html) if fig_rows_html else "<div style='padding:12px;color:#888;'>No figures generated.</div>"
        # % formatter
        def _as_pct(df: pd.DataFrame, sig: int = 2) -> pd.DataFrame:
            if df is None or df.empty:
                return pd.DataFrame()
            d = df.copy()
            def fmt(x):
                if pd.isna(x): return "-"
                if isinstance(x, (int, float, np.floating)): return f"{x*100.0:.{sig}f}%"
                return str(x)
            try: return d.map(fmt)
            except: return d.applymap(fmt)
        # -------- Main tables (controlled by right slider): metrics/eoy/drawdown
        blocks = []
        if "metrics" in self.tables_list:
            metrics_html = self.metrics_html if getattr(self, "metrics_html", None) \
                else self.metrics_df.to_html(border=0, escape=False)
            blocks.append(f"""
                <div class="table-block" data-table="metrics" data-group="{'controlled' if 'metrics' in group_keys else 'free'}">
                    <h3>Key Performance Metrics</h3>
                    {metrics_html}
                </div>
                """)
        if "eoy" in self.tables_list and getattr(self, "eoy_map", None):
            for col, df in self.eoy_map.items():
                if df is None or df.empty:
                    continue
                disp = df.copy()
                # Pretty format
                if "Benchmark" in disp.columns: disp["Benchmark"] = disp["Benchmark"].map(lambda v: "-" if pd.isna(v) else f"{v*100:.2f}%")
                if "Strategy" in disp.columns: disp["Strategy"] = disp["Strategy"].map(lambda v: "-" if pd.isna(v) else f"{v*100:.2f}%")
                if "Multiplier" in disp.columns: disp["Multiplier"] = disp["Multiplier"].map(lambda v: "-" if pd.isna(v) else f"{v:.2f}x")
                eoy_html = disp.to_html(border=0, escape=False, index=False)
                blocks.append(f"""
                    <div class="table-block" data-table="eoy" data-group="{'controlled' if 'eoy' in group_keys else 'free'}">
                        <h3>End of Year — {col}</h3>
                        {eoy_html}
                    </div>
                    """)
        if "drawdown_details" in self.tables_list and getattr(self, "dd_map", None):
            for col in getattr(self, "render_strategies", self.strategies):
                ddf = self.dd_map.get(col, pd.DataFrame())
                if ddf is None or ddf.empty:
                    continue
                ddisp = ddf.copy()
                if "Drawdown" in ddisp.columns:
                    ddisp["Drawdown"] = ddisp["Drawdown"].map(lambda v: f"{v:.2f}%" if isinstance(v, (int, float, np.floating)) else v)
                dd_html = ddisp.to_html(border=0, escape=False, index=False)
                blocks.append(f"""
                    <div class="table-block" data-table="drawdown_details" data-group="{'controlled' if 'drawdown_details' in group_keys else 'free'}">
                        <h3>Worst 10 Drawdowns — {col}</h3>
                        {dd_html}
                    </div>
                    """)
        tables_html = "\n".join(blocks) if blocks else "<div style='padding:12px;color:#888;'>No tables selected.</div>"
        # -------- Monthly Returns: put into a bottom drawer (full width of right pane)
        monthly_blocks = []
        if "monthly_returns" in self.tables_list and getattr(self, "monthly_map", None):
            for col in getattr(self, "render_strategies", self.strategies):
                m = self.monthly_map.get(col, pd.DataFrame())
                if m is None or m.empty:
                    continue
                m_disp = _as_pct(m, sig=2).to_html(border=0, escape=False)
                monthly_blocks.append(f"""
                    <div class="table-block monthly">
                        <h3>Monthly Returns — {col}</h3>
                        {m_disp}
                    </div>
                    """)
        monthly_html = "\n".join(monthly_blocks)
        # -------- CSS (header tweaks, right slider, drawer)
        bench_name = (self.benchmark.name if self.benchmark is not None and getattr(self.benchmark, "name", None) else "—")
        css_tpl = r"""
            <style>
            :root{
            --gutter:10px; --left-col: __LEFT__; --right-col: __RIGHT__;
            --tables-w: 720px; --handle-left: var(--tables-w);
            }
        *{box-sizing:border-box}
            body{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;background:#fff}
            .page{padding:16px}
            .titlebar{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
            .titlebar h1{margin:0;font-size:20px}
            .titlebar .sub{color:#555;font-size:13px}
            .meta{margin:4px 0 0 0;color:#666;font-size:12px}
            .meta-bench{margin:4px 0 8px 0;color:#555;font-size:12px}
            .outer-split{display:grid;grid-template-columns:var(--left-col) var(--gutter) var(--right-col);width:100%;height:calc(100vh - 120px);min-height:540px}
            .left-pane,.right-pane{overflow:auto}
            .gutter{background:transparent;cursor:col-resize;width:var(--gutter)}
            .gutter:hover{background:rgba(0,0,0,0.06)}
            /* Figures */
            .fig-row{margin:6px 8px 18px 2px}
            .fig-headers{display:grid;gap:10px}
            .fig-header{font-size:12px;font-weight:600;text-align:left;color:#333}
            .fig-grid{display:grid;gap:10px}
            .thumb{border:1px solid #e4e4e4;border-radius:6px;overflow:hidden;background:#fff}
            .thumb img{display:block;width:100%;height:auto;cursor:zoom-in}
            /* Tables panel + sticky right handle */
            .tables-wrap{position:relative;height:100%;overflow:hidden}
            .tables-content{position:absolute;left:0;top:0;bottom:0;width:calc(max(var(--tables-w),360px) + 30px);overflow:auto;padding:4px 20px 12px 10px;background:transparent}
            .right-handle{position:absolute;top:0;bottom:0;left:var(--handle-left);width:8px;cursor:col-resize;background:transparent;z-index:5}
            .right-handle:hover{background:rgba(0,0,0,0.06)}
            /* Base table */
            .table-block table{border-collapse:collapse;background:#fff;width:auto;table-layout:auto;font-size:12px}
            .table-block th,.table-block td{padding:6px 8px;text-align:right;border:none;font-size:12px}
            .table-block th{background:#f6f6f6;color:#333}
            .table-block td:first-child,.table-block th:first-child{text-align:left}
            .table-block{margin:8px 4px 18px 4px}
            .table-block h3{font-size:14px;margin:0 0 6px 0}
            /* Grouped metrics table: header colored, separators, no borders */
            .metrics-grouped{border-collapse:collapse;background:#fff;width:auto;table-layout:auto;font-size:12px}
            .metrics-grouped thead th{background:#f6f6f6;font-weight:600;padding:6px 10px;border:none;text-align:right;font-size:12px}
            .metrics-grouped thead th:first-child{text-align:left}
            .metrics-grouped tbody td{padding:6px 10px;border:none;font-weight:400;font-size:12px}
            .metrics-grouped td.mname{text-align:left;color:#333}
            .metrics-grouped td.mval{text-align:right}
            .metrics-grouped tr.sep td{border-bottom:1px solid #d0d0d0;height:6px;padding:0}
            .metrics-grouped tr.glabel td{color:#666;font-size:12px;padding-top:10px}
            /* CONTROLLED set (right slider applies) */
            __CONTROLLED_SELECTOR__{width:var(--tables-w);white-space:nowrap}
            /* Monthly drawer (bottom, full width of right pane) */
            .drawer-bar{display:flex;justify-content:flex-end;gap:10px;margin:6px 6px 8px 6px}
            .drawer-btn{padding:6px 10px;font-size:12px;border:1px solid #ddd;border-radius:6px;background:#fafafa;cursor:pointer}
            .drawer-btn:hover{background:#f0f0f0}
            .drawer{border-top:1px solid #e6e6e6;margin-top:8px;padding-top:8px;max-height:0;overflow:hidden;transition:max-height .25s ease}
            .drawer.open{max-height:60vh;overflow:auto}
            .drawer .table-block.monthly table{width:auto;min-width:max-content;white-space:nowrap}
            /* Zoom modal */
            .modal{position:fixed;inset:0;display:none;align-items:center;justify-content:center;background:rgba(0,0,0,0.76);z-index:1000}
            .modal img{max-width:98vw;max-height:96vh;display:block;box-shadow:0 10px 26px rgba(0,0,0,0.45);border-radius:10px}
            .modal.show{display:flex}
            </style>
            """
        controlled_selector = ",".join([f'.table-block[data-table="{k}"] table' for k in group_keys]) or "/* none */"
        css = (css_tpl
                    .replace("__LEFT__", f"{left_pct}%")
                    .replace("__RIGHT__", f"{right_pct}%")
                    .replace("__CONTROLLED_SELECTOR__", controlled_selector))
        # -------- JS (right handle + monthly drawer toggle + header note already in HTML)
        js_tpl = r"""
            <script>
        (function(){
            const root = document.documentElement;
            const outer = document.querySelector('.outer-split');
            const gutter = document.getElementById('left-gutter');
            const wrap = document.getElementById('tables-wrap');
            const handle = document.getElementById('right-handle');
            function cssPx(name, fallback=0){
                const v = getComputedStyle(root).getPropertyValue(name).trim();
                if (!v) return fallback;
                return v.endsWith('px') ? parseFloat(v) : (parseFloat(v) || fallback);
            }
            function setVarPx(name, px){ root.style.setProperty(name, px + 'px'); }
            function setLeftRightPx(leftPx, rightPx){
                const total = leftPx + cssPx('--gutter',10) + rightPx;
                root.style.setProperty('--left-col', (leftPx/total*100) + '%');
                root.style.setProperty('--right-col', (rightPx/total*100) + '%');
            }
            function clampTablesW(px){
                const r = wrap.getBoundingClientRect();
                const minW = 420;
                const maxW = Math.max(minW, r.width - 42);
                return Math.max(minW, Math.min(maxW, px));
            }
            function positionHandle(){
                const r = wrap.getBoundingClientRect();
                const tw = cssPx('--tables-w', 720);
                const left = Math.max(0, Math.min(r.width - 8, tw));
                setVarPx('--handle-left', left);
            }
            // Left splitter
            let dragL=false;
            gutter.addEventListener('mousedown', e => { dragL=true; e.preventDefault(); document.body.style.userSelect='none'; });
            window.addEventListener('mousemove', e => {
                if (!dragL) return;
                const rect = outer.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const minL = 260, maxL = rect.width - 360;
                const clamped = Math.max(minL, Math.min(maxL, x));
                const leftPx = clamped;
                const rightPx = rect.width - clamped - cssPx('--gutter',10);
                setLeftRightPx(leftPx, rightPx);
                positionHandle();
            });
            window.addEventListener('mouseup', () => { if (dragL){ dragL=false; document.body.style.userSelect=''; } });
            // Right handle (for controlled tables)
            let dragR=false;
            handle.addEventListener('mousedown', e => { dragR=true; e.preventDefault(); document.body.style.userSelect='none'; });
            window.addEventListener('mousemove', e => {
                if (!dragR) return;
                const r = wrap.getBoundingClientRect();
                let x = e.clientX - r.left;
                x = clampTablesW(x);
                setVarPx('--tables-w', x);
                positionHandle();
            });
            window.addEventListener('mouseup', () => { if (dragR){ dragR=false; document.body.style.userSelect=''; } });
            // Monthly drawer toggle
            const btn = document.getElementById('toggle-monthly');
            const draw = document.getElementById('monthly-drawer');
            if (btn && draw){
                btn.addEventListener('click', () => {
                    const open = draw.classList.toggle('open');
                    btn.textContent = open ? 'Hide Monthly Returns' : 'Show Monthly Returns';
                });
            }
            window.addEventListener('load', positionHandle);
            window.addEventListener('resize', positionHandle);
            // Zoom modal
            const modal = document.getElementById('zoom-modal');
            const modalImg = document.getElementById('zoom-image');
            document.querySelectorAll('img[data-zoom="1"]').forEach(img => {
                img.addEventListener('click', () => { modalImg.src = img.src; modal.classList.add('show'); });
            });
            modal.addEventListener('click', (e) => { if (e.target === modal || e.target.id === 'zoom-image') modal.classList.remove('show'); });
            window.addEventListener('keydown', (e) => { if (e.key === 'Escape') modal.classList.remove('show'); });
            })();
            </script>
            """
        js = js_tpl
        # -------- Header text
        tz = datetime.now().astimezone().tzinfo
        generated_str = datetime.now().astimezone().strftime(f"%Y-%m-%d %H:%M:%S {tz}")
        html = f"""<!doctype html>
            <html>
            <head>
            <meta charset="utf-8"/>
            <title>{self.title}</title>
            {css}
            <link rel="stylesheet" href="assets/zoom.css"/>
            </head>
            <body>
            <div class="page">
                <div class="titlebar">
                <h1>{self.title}</h1>
                </div>
                <div class="meta"> <strong>Benchmark: {bench_name}</strong>, Generated: {generated_str}</div>
                <div class="titlebar">
                <div class="meta">Sample Period: {self.date_range_str}</div>
                </div>
                <div class="meta"> Strategy: {', '.join(getattr(self, "render_strategies", self.strategies))}</div>
                <div class="outer-split">
                <div class="left-pane">
        {figures_html}
                </div>
                <div class="gutter" id="left-gutter" title="Drag to resize"></div>
                <div class="right-pane">
                    <div class="tables-wrap" id="tables-wrap">
                    <div class="tables-content" id="tables-content">
        {tables_html}
                        <div class="drawer-bar">
                        </div>
                    </div>
                    <div class="right-handle" id="right-handle" title="Drag to resize"></div>
                    </div>
                </div>
                </div>
            </div>
            <div class="modal" id="zoom-modal">
                <img id="zoom-image" src="" alt="Zoom"/>
            </div>
        {js}
            </body>
            </html>
            """
        with open(self.html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Dashboard written to: {self.html_path}")