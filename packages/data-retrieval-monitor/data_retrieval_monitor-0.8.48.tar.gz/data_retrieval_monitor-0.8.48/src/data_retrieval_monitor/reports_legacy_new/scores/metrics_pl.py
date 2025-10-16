import pandas as pd
import numpy as np
import polars as pl
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from quantstats.reports import _calc_dd
import quantstats as qs
from math import sqrt, ceil, floor
from scipy.stats import norm, linregress
from typing import Union, Optional, Literal, Iterable
import unittest
from quantstats.stats import (
    sharpe, smart_sharpe, rolling_sharpe, sortino, smart_sortino,
    rolling_sortino, adjusted_sortino, probabilistic_ratio,
    probabilistic_sharpe_ratio, probabilistic_sortino_ratio,
    probabilistic_adjusted_sortino_ratio,
    to_drawdown_series as to_drawdown_series_pandas,
    ulcer_index as ulcer_index_pandas,
    calmar as calmar_ratio_pandas,
    drawdown_details as drawdown_details_pandas,
)
import math
from datetime import datetime

# ==============================
# Utility Functions (Modularized)
# ==============================

def to_pl_returns_df(x, date_col="date", value_col="r"):
    if isinstance(x, pd.Series):
        idx = pd.to_datetime(x.index, errors="coerce")
        values = x.astype(float).to_numpy(copy=False)
        date_np = idx.to_numpy(dtype="datetime64[us]")
        return (
            pl.DataFrame({"date": date_np, value_col: values})
            .with_columns(
                pl.col("date").cast(pl.Datetime("us")),
                pl.col(value_col).cast(pl.Float64),
            )
            .drop_nulls(["date", value_col])
            .sort("date")
        )
    elif isinstance(x, pd.DataFrame):
        return (
            pl.from_pandas(x.reset_index().rename(columns={"index": "date"}))
            .with_columns(pl.col("date").cast(pl.Datetime("us")))
            .select(pl.col("date"), pl.exclude("date").cast(pl.Float64))
            .drop_nulls()
            .sort("date")
        )
    elif isinstance(x, pl.Series):
        return (
            x.to_frame("r")
            .with_columns(pl.col("r").cast(pl.Float64))
            .drop_nulls("r")
        )
    elif isinstance(x, pl.DataFrame):
        if date_col not in x.columns:
            return (
                x.with_columns(pl.all().cast(pl.Float64))
                .drop_nulls()
            )
        else:
            return (
                x.with_columns(pl.col(date_col).cast(pl.Datetime("us")))
                .select(pl.col(date_col), pl.exclude(date_col).cast(pl.Float64))
                .drop_nulls()
                .sort(date_col)
            )
    raise TypeError("Input must be pd.Series, pd.DataFrame, pl.Series, or pl.DataFrame")

def _to_pandas_series_for_qs(x) -> pd.Series:
    """
    Normalize any x (pl.Series/DataFrame, pd.Series/DataFrame) to a pandas Series
    with a DatetimeIndex. If no 'date' col is present, synthesize a daily index.
    """
    df = to_pl_returns_df(x)
    vals = df["r"].to_numpy() if "r" in df.columns else df[df.columns[0]].to_numpy()
    if "date" in df.columns:
        idx = pd.to_datetime(df["date"].to_numpy(), errors="coerce")
    else:
        idx = pd.date_range("2000-01-01", periods=len(vals), freq="D")
    s = pd.Series(vals.astype(float, copy=False), index=idx)
    if isinstance(s.index, pd.DatetimeIndex) and s.index.hasnans:
        s = s[~s.index.isna()]
    return s

def _find_return_col_in_pd(df: pd.DataFrame, value_col: Optional[str] = None) -> str:
    if value_col:
        return value_col
    possible = [c for c in df.columns if c.lower() in ['return', 'returns', 'r', 'ret', 'close']]
    if possible:
        return possible[0]
    raise ValueError("No return column found in pandas DataFrame.")

def _find_return_col_in_pl(df: pl.DataFrame, value_col: Optional[str] = None) -> str:
    if value_col:
        return value_col
    possible = [c for c in df.columns if c.lower() in ['return', 'returns', 'r', 'ret', 'close']]
    if possible:
        return possible[0]
    raise ValueError("No return column found in polars DataFrame.")

def _coerce_series_to_pl(
    x,
    *,
    name: str = "r",
    date_col: str = "date",
    value_col: Optional[str] = None,
) -> pl.DataFrame:
    """
    Convenience: returns a Polars DataFrame with ['date', name].
    Internally uses to_pl_returns_df and renames if needed.
    """
    df = to_pl_returns_df(x)
    if "r" in df.columns and name != "r":
        df = df.rename({"r": name})
    return df

def _align_two_series_pl(
    a: Union[pl.Series, pl.DataFrame],
    b: Union[pl.Series, pl.DataFrame],
    col_a: str = "r",
    col_b: str = "b"
) -> pl.DataFrame:

    # ensure pl.DataFrame/Series have the desired value column names
    if isinstance(a, pl.Series):
        da = a.to_frame(col_a)
    elif isinstance(a, pl.DataFrame):
        if col_a in a.columns:
            da = a
        else:
            val = [c for c in a.columns if c != "date"][0]
            da = a.rename({val: col_a})
    else:
        raise ValueError("Review left pl.dataframe input `a` passed onto `_align_two_series_pl`", a)

    if isinstance(b, pl.Series):
        db = b.to_frame(col_b)
    elif isinstance(b, pl.DataFrame):
        if col_b in b.columns:
            db = b
        else:
            val = [c for c in b.columns if c != "date"][0]
            db = b.rename({val: col_b})
    else:
        raise ValueError("Review right pl.dataframe input `b` passed onto `_align_two_series_pl`", b)

    # join by date if present, otherwise align by rowid
    if "date" in da.columns and "date" in db.columns:
        joined = da.join(db, on="date", how="inner").select(["date", col_a, col_b])
    else:
        joined = (
            da.with_row_count("rowid")
              .join(db.with_row_count("rowid"), on="rowid", how="inner")
              .select([col_a, col_b])
        )
    return joined

def _rf_series_should_be_annual(rf: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame]) -> bool:
    try:
        rf_df = _coerce_series_to_pl(rf, name="rf")
    except Exception:
        return True
    try:
        nunique = rf_df.select(pl.col("rf").n_unique()).to_numpy().ravel()[0]
        return bool(nunique == 1)
    except Exception:
        return True

def prepare_returns_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame],
    rf: Union[float, pl.Series, pl.DataFrame, pd.Series, pd.DataFrame] = 0.0,
    nperiods: Optional[int] = None,
    rf_is_annual: bool = True
) -> Union[pl.Series, pl.DataFrame]:
    df = _coerce_series_to_pl(returns, name="returns")
    has_date = 'date' in df.columns
    numeric_cols = [c for c in df.columns if c != 'date']
    returns_num = df.select(numeric_cols) if has_date else df
    if isinstance(rf, (float, int, np.floating)):
        if rf_is_annual and nperiods is not None:
            rf = (1 + float(rf)) ** (1 / nperiods) - 1
        else:
            rf = float(rf)
        returns_num = returns_num.with_columns([(pl.col(col) - rf).alias(col) for col in numeric_cols])
    else:
        rf_df = _coerce_series_to_pl(rf, name="rf")
        if has_date:
            returns_num = df.join(rf_df, on='date', how='inner')
            if rf_is_annual and nperiods is not None:
                returns_num = returns_num.with_columns(
                    ((1 + pl.col("rf")) ** (1 / nperiods) - 1).alias("rf")
                )
            returns_num = returns_num.with_columns([
                (pl.col(col) - pl.col("rf")).alias(col) for col in numeric_cols
            ]).select(numeric_cols)
        else:
            if len(rf_df) != len(returns_num):
                raise ValueError("rf series must match returns length when no date column")
            if rf_is_annual and nperiods is not None:
                rf_df = rf_df.with_columns(((1 + pl.col("rf")) ** (1 / nperiods) - 1).alias("rf"))
            returns_num = returns_num.with_columns([
                (pl.col(col) - rf_df["rf"]).alias(col) for col in numeric_cols
            ])
    returns_num = returns_num.fill_null(0)
    if has_date:
        returns_num = returns_num.with_columns(df["date"].alias('date'))
        returns_num = returns_num.select(['date'] + numeric_cols)
    if len(numeric_cols) == 1 and not has_date:
        return returns_num[numeric_cols[0]]
    return returns_num

def drop_date_if_present(df):
    if isinstance(df, pl.DataFrame) and 'date' in df.columns:
        numeric_cols = [c for c in df.columns if c != 'date']
        return df.select(numeric_cols)
    return df

def cumprod_polars(
    values: Union[pl.Series, pl.DataFrame],
    add_one: bool = True
) -> Union[pl.Series, pl.DataFrame]:
    if add_one:
        values = values + 1
    if isinstance(values, pl.Series):
        return values.cum_prod()
    else:
        return values.with_columns([pl.col(col).cum_prod().alias(col) for col in values.columns])

def cummax_polars(
    values: Union[pl.Series, pl.DataFrame]
) -> Union[pl.Series, pl.DataFrame]:
    if isinstance(values, pl.Series):
        return values.cum_max()
    else:
        return values.with_columns([pl.col(col).cum_max().alias(col) for col in values.columns])

def drawdown_from_peaks_polars(
    equity: Union[pl.Series, pl.DataFrame],
    peaks: Union[pl.Series, pl.DataFrame]
) -> Union[pl.Series, pl.DataFrame]:
    if isinstance(equity, pl.Series):
        return (equity / peaks) - 1
    else:
        return equity.with_columns([((pl.col(col) / peaks[col]) - 1).alias(col) for col in equity.columns])

def mean_squared_drawdown_polars(
    drawdowns: Union[pl.Series, pl.DataFrame]
) -> Union[float, pl.DataFrame]:
    if isinstance(drawdowns, pl.DataFrame):
        return pl.DataFrame({col: mean_squared_drawdown_polars(drawdowns[col]) for col in drawdowns.columns})
    return float(np.nanmean(pd.Series(drawdowns.to_numpy()) ** 2))

def sqrt_mean_squared_polars(
    mean_squared: Union[float, pl.DataFrame]
) -> Union[float, pl.DataFrame]:
    if isinstance(mean_squared, pl.DataFrame):
        return pl.DataFrame({col: sqrt_mean_squared_polars(mean_squared[col]) for col in mean_squared.columns})
    return sqrt(mean_squared) if mean_squared is not None else None

def max_drawdown_polars(
    drawdowns: Union[pl.Series, pl.DataFrame]
) -> Union[float, pl.DataFrame]:
    if isinstance(drawdowns, pl.DataFrame):
        return pl.DataFrame({col: max_drawdown_polars(drawdowns[col]) for col in drawdowns.columns})
    return abs(drawdowns.min()) if drawdowns.min() is not None else 0.0

def calmar_polars(returns: Union[pl.Series, pl.DataFrame], periods_per_year: int = 252) -> Union[float, pd.Series]:
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: calmar_polars(returns[col], periods_per_year) for col in returns.columns}
        return pd.Series(results)
    cagr_val = cagr_polars(returns, periods_per_year)
    dd = to_drawdown_series_polars(returns)
    mdd = dd.min()
    mdd = abs(mdd) if mdd is not None else 0.0
    return float(cagr_val / mdd) if mdd != 0.0 else float("nan")

# --- PURE NUMPY DRAW-DOWNS (no pandas) ---------------------------
_EPS = 1e-15

def _dd_from_returns_numpy(ret_np: np.ndarray) -> np.ndarray:
    eq = np.cumprod(1.0 + ret_np.astype(np.float64, copy=False))
    peaks = np.maximum.accumulate(np.concatenate(([1.0], eq)))[1:]
    dd = eq / peaks - 1.0
    dd[np.abs(dd) < _EPS] = 0.0
    dd[dd > 0.0] = 0.0
    return dd

def to_drawdown_series_polars(
    returns: Union[pl.Series, pl.DataFrame]
) -> Union[pl.Series, pl.DataFrame]:
    r = prepare_returns_polars(returns)
    if isinstance(r, pl.Series):
        equity = (r + 1.0).cum_prod()
        peaks_prev = equity.cum_max().shift(1).fill_null(1.0)
        dd = (equity / peaks_prev) - 1.0
        dd = dd.map_elements(lambda x: x if x <= 0.0 else 0.0, return_dtype=pl.Float64)
        return dd
    else:
        has_date = 'date' in r.columns
        if has_date:
            cols = [c for c in r.columns if c != "date"]
            out = r.select("date").with_columns(
                (
                    ((pl.col(c) + 1.0).cum_prod()
                     / (pl.col(c) + 1.0).cum_prod().cum_max().shift(1).fill_null(1.0)
                    ) - 1.0
                ).clip(upper_bound=0.0).alias(c)
                for c in cols
            )
        else:
            cols = r.columns
            out = r.with_columns(
                (
                    ((pl.col(c) + 1.0).cum_prod()
                     / (pl.col(c) + 1.0).cum_prod().cum_max().shift(1).fill_null(1.0)
                    ) - 1.0
                ).clip(upper_bound=0.0).alias(c)
                for c in cols
            )
        return out

def mean_squared_drawdown_polars(drawdowns: Union[pl.Series, pl.DataFrame]) -> Union[float, pl.DataFrame]:
    if isinstance(drawdowns, pl.DataFrame):
        return pl.DataFrame({c: mean_squared_drawdown_polars(drawdowns[c]) for c in drawdowns.columns if c != "date"})
    arr = drawdowns.to_numpy().astype(np.float64, copy=False)
    return float(np.nanmean(arr * arr))

def ulcer_index_pl(returns) -> Union[float, pd.Series]:
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: ulcer_index_pl(returns[col]) for col in returns.columns}
        return pd.Series(results)
    dd = to_drawdown_series_polars(returns)
    n = len(dd)
    if n < 2:
        return float("nan")
    ms = float((dd**2).mean())
    return math.sqrt(ms)

def aggregate_returns_polars(
    df: pl.DataFrame,
    period: str,
    compounded: bool = True
) -> pl.DataFrame:
    if 'date' not in df.columns:
        raise ValueError("date column required")
    numeric_cols = [c for c in df.columns if c != 'date']
    every = {'D': '1d', 'W': '1w', 'M': '1mo', 'Q': '3mo', 'Y': '1y'}.get(period.upper(), '1mo')
    offset = '1d' if period.upper() == 'W' else '0d'
    if compounded:
        agg_expr = [(pl.col(col).add(1).product() - 1).alias(col) for col in numeric_cols]
    else:
        agg_expr = [pl.col(col).sum().alias(col) for col in numeric_cols]
    agg = df.sort("date").group_by_dynamic("date", every=every, offset=offset).agg(agg_expr)
    return agg

def get_outliers_polars(data: pl.Series) -> dict:
    q1 = data.quantile(0.25)
    q3 = data.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    values = data.filter((data >= lower) & (data <= upper)).to_list()
    outliers = data.filter((data < lower) | (data > upper)).to_list()
    return {"values": values, "outliers": outliers}

def pct_rank_polars(
    prices: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame],
    window: int = 60
) -> Union[pl.Series, pl.DataFrame]:
    df = to_pl_returns_df(prices)
    numeric_cols = [c for c in df.columns if c != 'date']
    def _pct_rank(col_series: pl.Series) -> pl.Series:
        def rank_func(window_data):
            if len(window_data) == 0:
                return np.nan
            pd_ser = pd.Series(window_data)
            return pd_ser.rank(pct=True).iloc[-1]
        return col_series.rolling_map(rank_func, window_size=window)
    result = df.with_columns(
        _pct_rank(pl.col(col)).alias(col) for col in numeric_cols
    )
    result = result.with_columns(
        (pl.col(col) * 100.0).alias(col) for col in numeric_cols
    )
    return result.select(numeric_cols)[numeric_cols[0]] if len(numeric_cols) == 1 else result.select(numeric_cols)

def compsum_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame]
) -> Union[pl.Series, pl.DataFrame]:
    returns = prepare_returns_polars(returns)
    return cumprod_polars(returns, add_one=True) - 1

def comp_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame]
) -> Union[float, pd.Series]:
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: comp_polars(returns[col]) for col in returns.columns}
        return pd.Series(results)
    return (1 + returns).product() - 1

def distribution_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame],
    compounded: bool = True
) -> dict:
    df = to_pl_returns_df(returns)
    daily = df["r"]
    weekly = aggregate_returns_polars(df, 'W', compounded)["r"]
    monthly = aggregate_returns_polars(df, 'M', compounded)["r"]
    quarterly = aggregate_returns_polars(df, 'Q', compounded)["r"]
    yearly = aggregate_returns_polars(df, 'Y', compounded)["r"]
    return {
        "Daily": get_outliers_polars(daily),
        "Weekly": get_outliers_polars(weekly),
        "Monthly": get_outliers_polars(monthly),
        "Quarterly": get_outliers_polars(quarterly),
        "Yearly": get_outliers_polars(yearly),
    }

def expected_return_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame],
    aggregate: Optional[str] = None,
    compounded: bool = True
) -> Union[float, pd.Series]:
    if aggregate:
        return expected_return_polars(aggregate_returns_polars(returns, aggregate, compounded), compounded=compounded)
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: expected_return_polars(returns[col], compounded=compounded) for col in returns.columns}
        return pd.Series(results)
    n = returns.len()
    return (1 + returns).product() ** (1 / n) - 1 if n > 0 else 0.0

def geometric_mean_polars(returns, aggregate=None, compounded=True):
    return expected_return_polars(returns, aggregate, compounded)

def ghpr_polars(returns, aggregate=None, compounded=True):
    return expected_return_polars(returns, aggregate, compounded)

def outliers_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame],
    quantile: float = 0.95
) -> Union[pl.Series, pl.DataFrame]:
    df = to_pl_returns_df(returns)
    q = df["r"].quantile(quantile)
    return df.filter(pl.col("r") > q)["r"]

def remove_outliers_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame],
    quantile: float = 0.95
) -> Union[pl.Series, pl.DataFrame]:
    df = to_pl_returns_df(returns)
    q = df["r"].quantile(quantile)
    return df.filter(pl.col("r") < q)["r"]

def best_polars(
    returns: Union[pl.Series, pl.DataFrame],
    aggregate: Optional[str] = None,
    compounded: bool = True
) -> Union[float, pd.Series]:
    if aggregate:
        return best_polars(aggregate_returns_polars(returns, aggregate, compounded))
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: best_polars(returns[col]) for col in returns.columns}
        return pd.Series(results)
    return returns.max() if returns.len() > 0 else 0.0

def worst_polars(
    returns: Union[pl.Series, pl.DataFrame],
    aggregate: Optional[str] = None,
    compounded: bool = True
) -> Union[float, pd.Series]:
    if aggregate:
        return worst_polars(aggregate_returns_polars(returns, aggregate, compounded))
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: worst_polars(returns[col]) for col in returns.columns}
        return pd.Series(results)
    return returns.min() if returns.len() > 0 else 0.0

def consecutive_wins_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame],
    aggregate: Optional[str] = None,
    compounded: bool = True
) -> Union[int, pd.Series]:
    if aggregate:
        return consecutive_wins_polars(aggregate_returns_polars(returns, aggregate, compounded))
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: consecutive_wins_polars(returns[col], aggregate, compounded) for col in returns.columns}
        return pd.Series(results)
    # now returns is Series
    temp_df = pl.DataFrame({"returns": returns})
    temp_df = temp_df.with_columns(
        (pl.col("returns") > 0).cast(pl.Int32).alias("pos")
    ).with_columns(
        (pl.col("pos").diff().ne(0).fill_null(True)).cast(pl.Int32).alias("change")
    ).with_columns(
        pl.col("change").cum_sum().alias("group_id")
    )
    streaks = temp_df.filter(pl.col("pos") == 1).group_by("group_id").agg(pl.len().alias("streak"))["streak"]
    max_streak = streaks.max() or 0
    return int(max_streak)

def consecutive_losses_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame],
    aggregate: Optional[str] = None,
    compounded: bool = True
) -> Union[int, pd.Series]:
    if aggregate:
        return consecutive_losses_polars(aggregate_returns_polars(returns, aggregate, compounded))
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: consecutive_losses_polars(returns[col], aggregate, compounded) for col in returns.columns}
        return pd.Series(results)
    # now returns is Series
    temp_df = pl.DataFrame({"returns": returns})
    temp_df = temp_df.with_columns(
        (pl.col("returns") < 0).cast(pl.Int32).alias("neg")
    ).with_columns(
        (pl.col("neg").diff().ne(0).fill_null(True)).cast(pl.Int32).alias("change")
    ).with_columns(
        pl.col("change").cum_sum().alias("group_id")
    )
    streaks = temp_df.filter(pl.col("neg") == 1).group_by("group_id").agg(pl.len().alias("streak"))["streak"]
    max_streak = streaks.max() or 0
    return int(max_streak)

def exposure_polars(
    returns: Union[pl.Series, pl.DataFrame]
) -> Union[float, pd.Series]:
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: exposure_polars(returns[col]) for col in returns.columns}
        return pd.Series(results)
    non_zero = returns.filter(returns != 0).len()
    total = returns.len()
    ex = non_zero / total if total > 0 else 0.0
    return ceil(ex * 100) / 100.0

def avg_return_polars(
    returns: Union[pl.Series, pl.DataFrame],
    aggregate: Optional[str] = None,
    compounded: bool = True
) -> Union[float, pd.Series]:
    if aggregate:
        return avg_return_polars(aggregate_returns_polars(returns, aggregate, compounded))
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: avg_return_polars(returns[col]) for col in returns.columns}
        return pd.Series(results)
    non_zero = returns.filter(returns != 0)
    return non_zero.mean() if non_zero.len() > 0 else 0.0

def win_rate_polars(
    returns: Union[pl.Series, pl.DataFrame],
    aggregate: Optional[str] = None,
    compounded: bool = True
) -> Union[float, pd.Series]:
    if aggregate:
        return win_rate_polars(aggregate_returns_polars(returns, aggregate, compounded))
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: win_rate_polars(returns[col]) for col in returns.columns}
        return pd.Series(results)
    non_zero = returns.filter(returns != 0).len()
    positive = returns.filter(returns > 0).len()
    return positive / non_zero if non_zero > 0 else 0.0

def avg_win_polars(
    returns: Union[pl.Series, pl.DataFrame],
    aggregate: Optional[str] = None,
    compounded: bool = True
) -> Union[float, pd.Series]:
    if aggregate:
        return avg_win_polars(aggregate_returns_polars(returns, aggregate, compounded))
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: avg_win_polars(returns[col]) for col in returns.columns}
        return pd.Series(results)
    positive = returns.filter(returns > 0)
    return positive.mean() if positive.len() > 0 else 0.0

def avg_loss_polars(
    returns: Union[pl.Series, pl.DataFrame],
    aggregate: Optional[str] = None,
    compounded: bool = True
) -> Union[float, pd.Series]:
    if aggregate:
        return avg_loss_polars(aggregate_returns_polars(returns, aggregate, compounded))
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: avg_loss_polars(returns[col]) for col in returns.columns}
        return pd.Series(results)
    negative = returns.filter(returns < 0)
    return negative.mean() if negative.len() > 0 else 0.0

def volatility_polars(
    returns: Union[pl.Series, pl.DataFrame],
    periods: int = 252,
    annualize: bool = True
) -> Union[float, pd.Series]:
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: volatility_polars(returns[col], periods, annualize) for col in returns.columns}
        return pd.Series(results)
    std = returns.std(ddof=1)
    if annualize:
        return std * sqrt(periods)
    return std

def rolling_volatility_polars(
    returns: Union[pl.Series, pl.DataFrame],
    rolling_period: int = 126,
    periods_per_year: int = 252
) -> Union[pl.Series, pl.DataFrame]:
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        return pl.DataFrame({col: rolling_volatility_polars(returns[col], rolling_period, periods_per_year) for col in returns.columns})
    rolling_std = returns.rolling_std(window_size=rolling_period, min_samples=rolling_period, ddof=1)
    if periods_per_year:
        rolling_std = rolling_std * sqrt(periods_per_year)
    return rolling_std

def implied_volatility_polars(
    returns: Union[pl.Series, pl.DataFrame],
    periods: int = 252,
    annualize: bool = True
) -> Union[float, pd.Series]:
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: implied_volatility_polars(returns[col], periods, annualize) for col in returns.columns}
        return pd.Series(results)
    log_ret = (1 + returns).log()
    std = log_ret.std(ddof=1)
    if annualize:
        return std * sqrt(periods)
    return std

def autocorr_penalty_polars(
    returns: Union[pl.Series, pl.DataFrame]
) -> Union[float, pd.Series]:
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: autocorr_penalty_polars(returns[col]) for col in returns.columns}
        return pd.Series(results)
    n = returns.len()
    if n <= 1 or returns.std(ddof=1) < 1e-10:
        return np.nan
    lagged = returns.shift(1)
    mask = lagged.is_not_null()
    returns_masked = returns.filter(mask)
    lagged_masked = lagged.filter(mask)
    if returns_masked.len() <= 1:
        coef = 0.0
    else:
        pair_df = pl.DataFrame({"a": returns_masked, "b": lagged_masked})
        coef = pair_df.select(pl.corr("a", "b")).item()
        coef = abs(coef) if not np.isnan(coef) else 0.0
    corr = sum(((n - i) / n) * (coef ** i) for i in range(1, n))
    return sqrt(1 + 2 * corr)

def sharpe_polars(returns, rf=0.0, periods=252, annualize=True, smart=False):
    returns = drop_date_if_present(prepare_returns_polars(returns, rf=rf, nperiods=periods if _rf_series_should_be_annual(rf) else None, rf_is_annual=_rf_series_should_be_annual(rf)))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: sharpe_polars(returns[col], rf, periods, annualize, smart) for col in returns.columns}
        return pd.Series(results)
    mean = returns.mean()
    sd = returns.std(ddof=1)
    if sd == 0:
        if mean > 0:
            val = np.inf
        elif mean < 0:
            val = -np.inf
        else:
            val = np.nan
    else:
        val = mean / sd
    if smart and np.isfinite(val) and sd != 0:
        val /= autocorr_penalty_polars(returns)
    if annualize:
        val *= sqrt(periods)
    return float(val)

def smart_sharpe_polars(returns, rf=0.0, periods=252, annualize=True):
    returns = drop_date_if_present(prepare_returns_polars(returns, rf=rf, nperiods=periods if _rf_series_should_be_annual(rf) else None, rf_is_annual=_rf_series_should_be_annual(rf)))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: smart_sharpe_polars(returns[col], rf, periods, annualize) for col in returns.columns}
        return pd.Series(results)
    return sharpe_polars(returns, rf, periods, annualize, smart=True)

def sortino_polars(returns, rf=0.0, periods=252, annualize=True, smart=False):
    returns = drop_date_if_present(prepare_returns_polars(returns, rf=rf, nperiods=periods if _rf_series_should_be_annual(rf) else None, rf_is_annual=_rf_series_should_be_annual(rf)))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: sortino_polars(returns[col], rf, periods, annualize, smart) for col in returns.columns}
        return pd.Series(results)
    mean = returns.mean()
    downside = returns.clip(upper_bound=0.0).pow(2).mean()
    lpsd = sqrt(downside) if downside > 0 else 0.0
    if lpsd == 0:
        return np.nan
    val = mean / lpsd
    if smart and np.isfinite(val):
        val /= autocorr_penalty_polars(returns)
    if annualize:
        val *= sqrt(periods)
    return float(val)

def smart_sortino_polars(returns, rf=0.0, periods=252, annualize=True):
    returns = drop_date_if_present(prepare_returns_polars(returns, rf=rf, nperiods=periods if _rf_series_should_be_annual(rf) else None, rf_is_annual=_rf_series_should_be_annual(rf)))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: smart_sortino_polars(returns[col], rf, periods, annualize) for col in returns.columns}
        return pd.Series(results)
    return sortino_polars(returns, rf, periods, annualize, smart=True)

def adjusted_sortino_polars(returns, rf=0.0, periods=252, annualize=True, smart=False):
    returns = drop_date_if_present(prepare_returns_polars(returns, rf=rf, nperiods=periods if _rf_series_should_be_annual(rf) else None, rf_is_annual=_rf_series_should_be_annual(rf)))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: adjusted_sortino_polars(returns[col], rf, periods, annualize, smart) for col in returns.columns}
        return pd.Series(results)
    srt = sortino_polars(returns, rf, periods, annualize, smart)
    if np.isnan(srt):
        return np.nan
    return float(srt / sqrt(2))

def probabilistic_ratio_polars(series, rf=0.0, base="sharpe", periods=252, annualize=False, smart=False):
    returns = drop_date_if_present(prepare_returns_polars(series, rf=rf, nperiods=periods if _rf_series_should_be_annual(rf) else None, rf_is_annual=_rf_series_should_be_annual(rf)))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: probabilistic_ratio_polars(returns[col], rf, base, periods, annualize, smart) for col in returns.columns}
        return pd.Series(results)
    n = returns.len()
    if n < 2:
        return np.nan
    if base.lower() == "sharpe":
        base_ratio = sharpe_polars(returns, 0.0, periods, annualize=False, smart=smart)
    elif base.lower() == "sortino":
        base_ratio = sortino_polars(returns, 0.0, periods, annualize=False, smart=smart)
    elif base.lower() == "adjusted_sortino":
        base_ratio = adjusted_sortino_polars(returns, 0.0, periods, annualize=False, smart=smart)
    else:
        raise ValueError("base must be 'sharpe', 'sortino', or 'adjusted_sortino'")
    skew = returns.skew(bias=False)
    kurt_ex = returns.kurtosis(bias=False)
    sigma_sr = np.sqrt((1 + (0.5 * base_ratio**2) - (skew * base_ratio) + (((kurt_ex - 3) / 4) * base_ratio**2)) / (n - 1))
    z = base_ratio / sigma_sr if sigma_sr != 0 else np.nan
    psr = norm.cdf(z)
    if annualize:
        psr *= sqrt(periods)
    return float(psr)

def probabilistic_sharpe_ratio_polars(series, rf=0.0, periods=252, annualize=False, smart=False):
    returns = drop_date_if_present(prepare_returns_polars(series, rf=rf, nperiods=periods if _rf_series_should_be_annual(rf) else None, rf_is_annual=_rf_series_should_be_annual(rf)))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: probabilistic_sharpe_ratio_polars(returns[col], rf, periods, annualize, smart) for col in returns.columns}
        return pd.Series(results)
    return probabilistic_ratio_polars(returns, rf, "sharpe", periods, annualize, smart)

def probabilistic_sortino_ratio_polars(series, rf=0.0, periods=252, annualize=False, smart=False):
    returns = drop_date_if_present(prepare_returns_polars(series, rf=rf, nperiods=periods if _rf_series_should_be_annual(rf) else None, rf_is_annual=_rf_series_should_be_annual(rf)))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: probabilistic_sortino_ratio_polars(returns[col], rf, periods, annualize, smart) for col in returns.columns}
        return pd.Series(results)
    return probabilistic_ratio_polars(returns, rf, "sortino", periods, annualize, smart)

def probabilistic_adjusted_sortino_ratio_polars(series, rf=0.0, periods=252, annualize=False, smart=False):
    returns = drop_date_if_present(prepare_returns_polars(series, rf=rf, nperiods=periods if _rf_series_should_be_annual(rf) else None, rf_is_annual=_rf_series_should_be_annual(rf)))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: probabilistic_adjusted_sortino_ratio_polars(returns[col], rf, periods, annualize, smart) for col in returns.columns}
        return pd.Series(results)
    return probabilistic_ratio_polars(returns, rf, "adjusted_sortino", periods, annualize, smart)

def rolling_sharpe_polars(returns, rf=0.0, rolling_period=126, annualize=True, periods_per_year=252):
    rf_annual = _rf_series_should_be_annual(rf)
    r = prepare_returns_polars(returns, rf, nperiods=(rolling_period if rf_annual else None), rf_is_annual=rf_annual)
    r = drop_date_if_present(r)
    if isinstance(r, pl.DataFrame) and r.shape[1] == 1:
        r = r[r.columns[0]]
    if isinstance(r, pl.DataFrame):
        return pl.DataFrame({col: rolling_sharpe_polars(r[col], rf, rolling_period, annualize, periods_per_year) for col in r.columns})
    rm = r.rolling_mean(window_size=rolling_period, min_samples=rolling_period)
    rs = r.rolling_std(window_size=rolling_period, min_samples=rolling_period, ddof=1)
    out = rm / rs
    if annualize:
        out = out * sqrt(periods_per_year)
    return out

def rolling_sortino_polars(returns, rf=0.0, rolling_period=126, annualize=True, periods_per_year=252):
    rf_annual = _rf_series_should_be_annual(rf)
    r = prepare_returns_polars(returns, rf, nperiods=(rolling_period if rf_annual else None), rf_is_annual=rf_annual)
    r = drop_date_if_present(r)
    if isinstance(r, pl.DataFrame) and r.shape[1] == 1:
        r = r[r.columns[0]]
    if isinstance(r, pl.DataFrame):
        return pl.DataFrame({col: rolling_sortino_polars(r[col], rf, rolling_period, annualize, periods_per_year) for col in r.columns})
    rm = r.rolling_mean(window_size=rolling_period, min_samples=rolling_period)
    down_mean = r.clip(upper_bound=0.0).pow(2).rolling_mean(window_size=rolling_period, min_samples=rolling_period)
    lpsd = down_mean.sqrt()
    out = rm / lpsd
    if annualize:
        out = out * sqrt(periods_per_year)
    return out

def treynor_ratio_polars(
    returns,
    benchmark,
    periods: int = 252,
    rf: Union[float, pl.Series, pd.Series, pl.DataFrame, pd.DataFrame] = 0.0,
) -> float:
    """
    Treynor ratio computed as total compounded return divided by beta.
    (Matches the previous behavior in your code: total return / beta; no extra rf adjustment here.)

    Robust to inputs as pl/pd Series/DataFrame, with or without 'date'.
    Falls back to row alignment if dates are not available.
    """
    # Coerce both to Polars DataFrames
    r_df = to_pl_returns_df(returns)   # -> ['date', <val>] or [<val>]
    b_df = to_pl_returns_df(benchmark) # -> ['date', <val>] or [<val>]

    # Identify value columns and standardize their names to 'r' and 'b'
    r_val_cols = [c for c in r_df.columns if c != "date"]
    b_val_cols = [c for c in b_df.columns if c != "date"]
    if not r_val_cols or not b_val_cols:
        return float("nan")

    r_val = r_val_cols[0]
    b_val = b_val_cols[0]
    if r_val != "r":
        r_df = r_df.rename({r_val: "r"})
    if b_val != "b":
        b_df = b_df.rename({b_val: "b"})

    # Align by date if possible, otherwise align by row id
    if "date" in r_df.columns and "date" in b_df.columns:
        joined = (
            r_df.join(b_df, on="date", how="inner")
               .select(["date", "r", "b"])
               .drop_nulls()
               .sort("date")
        )
    else:
        joined = (
            r_df.with_row_count("rowid")
                .join(b_df.with_row_count("rowid"), on="rowid", how="inner")
                .select(["r", "b"])
                .drop_nulls()
        )

    if joined.height < 2:
        return float("nan")

    rr = joined["r"].to_numpy()
    bb = joined["b"].to_numpy()

    # Beta via covariance / variance
    var_b = float(np.var(bb, ddof=1))
    if var_b == 0.0 or np.isnan(var_b):
        return float("nan")
    cov_rb = float(np.cov(rr, bb, ddof=1)[0, 1])
    beta = cov_rb / var_b
    if beta == 0.0 or np.isnan(beta):
        return float("nan")

    # Total compounded return over the sample
    # (Keep consistent with your previous implementation.)
    total_r = float((1.0 + pl.Series(rr)).cum_prod()[-1] - 1.0)
    return float(total_r / beta)

def omega_polars(
    returns: Union[pl.Series, pl.DataFrame],
    rf: Union[float, pl.Series, pl.DataFrame] = 0.0,
    required_return: float = 0.0,
    periods: int = 252
) -> Union[float, pd.Series]:
    returns = drop_date_if_present(prepare_returns_polars(returns, rf=rf, nperiods=periods if _rf_series_should_be_annual(rf) else None, rf_is_annual=_rf_series_should_be_annual(rf)))
    required_return = required_return / periods if periods else required_return
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: omega_polars(returns[col], rf, required_return, periods) for col in returns.columns}
        return pd.Series(results)
    n = returns.len()
    if n < 2:
        return np.nan
    if required_return <= -1:
        return np.nan
    returns_less_thresh = returns - required_return
    numer = returns_less_thresh.filter(returns_less_thresh > 0.0).sum()
    denom = -1.0 * returns_less_thresh.filter(returns_less_thresh < 0.0).sum()
    return numer / denom if denom > 0.0 else np.nan

def gain_to_pain_ratio_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame],
    rf: Union[float, pl.Series, pl.DataFrame, pd.Series, pd.DataFrame] = 0.0,
    resolution: str = "D",
    dates: Optional[pl.Series] = None
) -> Union[float, pd.Series]:
    returns = prepare_returns_polars(returns)
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: gain_to_pain_ratio_polars(returns[col], rf, resolution, dates) for col in returns.columns}
        return pd.Series(results)
    # now returns is Series
    if resolution != "D":
        if dates is None:
            raise ValueError("dates required for resolution != D")
        df = pl.DataFrame({"r": returns, "date": dates})
        df = df.with_columns(pl.col("date").cast(pl.Datetime("us")))
        # Aggregate: group by month, sum (not compounded, as per QS)
        df = df.group_by_dynamic("date", every="1mo").agg(pl.col("r").sum()).sort("date")
        returns = df["r"]
    pos_sum = returns.filter(returns > 0).sum()
    neg_sum = abs(returns.filter(returns < 0).sum())
    return (pos_sum / neg_sum - 1) if neg_sum != 0 else np.nan

def cagr_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame],
    periods_per_year: int = 252
) -> Union[float, pd.Series]:
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: cagr_polars(returns[col], periods_per_year) for col in returns.columns}
        return pd.Series(results)
    total_return = (1 + returns).product() - 1
    years = returns.len() / periods_per_year
    return (1 + total_return) ** (1 / years) - 1 if years > 0 else 0.0

def rar_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame],
    rf: Union[float, pl.Series, pl.DataFrame, pd.Series, pd.DataFrame] = 0.0
) -> Union[float, pd.Series]:
    cagr_val = cagr_polars(returns)
    exp = exposure_polars(returns)
    return cagr_val / exp if exp != 0 else np.nan

def skew_polars(
    returns: Union[pl.Series, pl.DataFrame]
) -> Union[float, pd.Series]:
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: skew_polars(returns[col]) for col in returns.columns}
        return pd.Series(results)
    if returns.len() < 3 or returns.std(ddof=1) < 1e-10:
        return 0.0
    return float(returns.skew(bias=False))

def kurtosis_polars(
    returns: Union[pl.Series, pl.DataFrame]
) -> Union[float, pd.Series]:
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: kurtosis_polars(returns[col]) for col in returns.columns}
        return pd.Series(results)
    if returns.len() < 4 or returns.std(ddof=1) < 1e-10:
        return 0.0
    return float(returns.kurtosis(bias=False))


def calmar_polars(returns: Union[pl.Series, pl.DataFrame], periods_per_year: int = 252) -> Union[float, pd.Series]:
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: calmar_polars(returns[col], periods_per_year) for col in returns.columns}
        return pd.Series(results)
    cagr_val = cagr_polars(returns, periods_per_year)
    dd = to_drawdown_series_polars(returns)
    mdd = dd.min()
    mdd = abs(mdd) if mdd is not None else 0.0
    return float(cagr_val / mdd) if mdd != 0.0 else float("nan")

def ulcer_performance_index_polars(
    returns: Union[pl.Series, pl.DataFrame],
    rf: Union[float, pl.Series, pl.DataFrame] = 0.0
) -> Union[float, pd.Series]:
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: ulcer_performance_index_polars(returns[col], rf) for col in returns.columns}
        return pd.Series(results)
    comp_val = comp_polars(returns)
    ui = ulcer_index_pl(returns)
    return (comp_val - rf) / ui if ui != 0 else np.nan

def serenity_index_polars(
    returns: Union[pl.Series, pl.DataFrame],
    rf: Union[float, pl.Series, pl.DataFrame] = 0.0
) -> Union[float, pd.Series]:
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: serenity_index_polars(returns[col], rf) for col in returns.columns}
        return pd.Series(results)
    dd = to_drawdown_series_polars(returns)
    std_r = returns.std()
    mu = dd.mean()
    std_dd = dd.std()
    var = norm.ppf(0.05, mu, std_dd)
    below = dd.filter(dd < var)
    cvar = below.mean() if len(below) > 0 else var
    pitfall = -cvar / std_r if std_r != 0 else np.nan
    ui = ulcer_index_pl(returns)
    denom = ui * pitfall
    numer = returns.sum() - rf
    return numer / denom if denom != 0 else np.nan

def upi_polars(returns, rf=0.0):
    return ulcer_performance_index_polars(returns, rf)

def risk_of_ruin_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame]
) -> Union[float, pd.Series]:
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: risk_of_ruin_polars(returns[col]) for col in returns.columns}
        return pd.Series(results)
    wins = win_rate_polars(returns)
    return ((1 - wins) / (1 + wins)) ** len(returns) if len(returns) > 0 else 0.0

def ror_polars(returns):
    return risk_of_ruin_polars(returns)

def value_at_risk_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame],
    sigma: float = 1.0,
    confidence: float = 0.95
) -> Union[float, pd.Series]:
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: value_at_risk_polars(returns[col], sigma, confidence) for col in returns.columns}
        return pd.Series(results)
    pd_series = pd.Series(returns.to_numpy())
    mu = pd_series.mean()
    std = pd_series.std(ddof=1) * sigma
    return norm.ppf(1 - confidence, mu, std)

def var_polars(returns, sigma=1.0, confidence=0.95):
    return value_at_risk_polars(returns, sigma, confidence)

def conditional_value_at_risk_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame],
    sigma: float = 1.0,
    confidence: float = 0.95
) -> Union[float, pd.Series]:
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: conditional_value_at_risk_polars(returns[col], sigma, confidence) for col in returns.columns}
        return pd.Series(results)
    var_val = value_at_risk_polars(returns, sigma, confidence)
    below_var = returns.filter(returns < var_val)
    c_var = below_var.mean() if len(below_var) > 0 else var_val
    return c_var

def cvar_polars(returns, sigma=1.0, confidence=0.95):
    return conditional_value_at_risk_polars(returns, sigma, confidence)

def expected_shortfall_polars(returns, sigma=1.0, confidence=0.95):
    return conditional_value_at_risk_polars(returns, sigma, confidence)

def tail_ratio_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame],
    cutoff: float = 0.95
) -> Union[float, pd.Series]:
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: tail_ratio_polars(returns[col], cutoff) for col in returns.columns}
        return pd.Series(results)
    if returns.len() < 2:
        return np.nan
    pd_ser = pd.Series(returns.to_numpy())
    upper = pd_ser.quantile(cutoff)
    lower = abs(pd_ser.quantile(1 - cutoff))
    return upper / lower if lower != 0 else np.nan

def payoff_ratio_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame]
) -> Union[float, pd.Series]:
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: payoff_ratio_polars(returns[col]) for col in returns.columns}
        return pd.Series(results)
    avg_win = avg_win_polars(returns)
    avg_loss = avg_loss_polars(returns)
    return avg_win / abs(avg_loss) if avg_loss != 0 else np.nan

def win_loss_ratio_polars(returns):
    return payoff_ratio_polars(returns)

def profit_factor_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame]
) -> Union[float, pd.Series]:
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: profit_factor_polars(returns[col]) for col in returns.columns}
        return pd.Series(results)
    pos = returns.filter(returns > 0).sum() or 0.0
    neg = (-returns.filter(returns < 0)).sum() or 0.0
    return pos / neg if neg != 0 else np.inf

def cpc_index_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame]
) -> Union[float, pd.Series]:
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: cpc_index_polars(returns[col]) for col in returns.columns}
        return pd.Series(results)
    pf = profit_factor_polars(returns)
    wr = win_rate_polars(returns)
    wlr = win_loss_ratio_polars(returns)
    return pf * wr * wlr

def common_sense_ratio_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame]
) -> Union[float, pd.Series]:
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: common_sense_ratio_polars(returns[col]) for col in returns.columns}
        return pd.Series(results)
    pf = profit_factor_polars(returns)
    tr = tail_ratio_polars(returns)
    return pf * tr

def outlier_win_ratio_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame],
    quantile: float = 0.99
) -> Union[float, pd.Series]:
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: outlier_win_ratio_polars(returns[col], quantile) for col in returns.columns}
        return pd.Series(results)
    if returns.len() < 2:
        return np.nan
    pd_ser = pd.Series(returns.to_numpy())
    q = pd_ser.quantile(quantile)
    mean_pos = pd_ser[pd_ser > 0].mean()
    return q / mean_pos if mean_pos != 0 else np.nan

def outlier_loss_ratio_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame],
    quantile: float = 0.01
) -> Union[float, pd.Series]:
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: outlier_loss_ratio_polars(returns[col], quantile) for col in returns.columns}
        return pd.Series(results)
    if returns.len() < 2:
        return np.nan
    pd_ser = pd.Series(returns.to_numpy())
    q = pd_ser.quantile(quantile)
    mean_neg = pd_ser[pd_ser < 0].mean()
    return q / mean_neg if mean_neg != 0 else np.nan

def recovery_factor_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame],
    rf: Union[float, pl.Series, pl.DataFrame, pd.Series, pd.DataFrame] = 0.0
) -> Union[float, pd.Series]:
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: recovery_factor_polars(returns[col], rf) for col in returns.columns}
        return pd.Series(results)
    total_r = returns.sum() - rf
    max_dd = abs(max_drawdown_polars(to_drawdown_series_polars(returns)))
    return abs(total_r) / max_dd if max_dd != 0 else np.nan

def risk_return_ratio_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame]
) -> Union[float, pd.Series]:
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: risk_return_ratio_polars(returns[col]) for col in returns.columns}
        return pd.Series(results)
    pd_series = pd.Series(returns.to_numpy())
    mean = pd_series.mean()
    std = pd_series.std(ddof=1)
    return mean / std if std != 0 else np.nan

def kelly_criterion_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame]
) -> Union[float, pd.Series]:
    returns = drop_date_if_present(prepare_returns_polars(returns))
    if isinstance(returns, pl.DataFrame) and returns.shape[1] == 1:
        returns = returns[returns.columns[0]]
    if isinstance(returns, pl.DataFrame):
        results = {col: kelly_criterion_polars(returns[col]) for col in returns.columns}
        return pd.Series(results)
    wlr = win_loss_ratio_polars(returns)
    wr = win_rate_polars(returns)
    return wr - (1 - wr) / wlr if wlr != 0 else np.nan

def r_squared_polars(
    returns, benchmark, *, epsilon: float = 1e-12
) -> float:    
    aligned = _align_two_series_pl(returns, benchmark, col_a="y", col_b="x")
    # drop null pairs
    aligned = aligned.drop_nulls()
    pairs = drop_date_if_present(aligned)
    if pairs.width != 2 or pairs.height == 0:
        return 0.0

    y = pairs["y"].cast(pl.Float64).to_numpy()
    x = pairs["x"].cast(pl.Float64).to_numpy()

    x_mean = x.mean()
    y_mean = y.mean()
    sxx = ((x - x_mean) ** 2).sum()
    syy = ((y - y_mean) ** 2).sum()
    sxy = ((x - x_mean) * (y - y_mean)).sum()

    if sxx <= epsilon or syy <= epsilon:
        return 0.0
    r = sxy / np.sqrt(sxx * syy)
    return float(max(0.0, min(1.0, r * r)))

def r2_polars(returns, benchmark):
    return r_squared_polars(returns, benchmark)

def tracking_error_polars(
    returns, benchmark, *, periods: int = 252, annualize: bool = True, epsilon: float = 1e-12
) -> float:
    """
    Calculate the tracking error as the standard deviation of active returns (portfolio - benchmark),
    with optional annualization to match quantstats.stats.tracking_error.

    Args:
        returns: Portfolio returns (pl.Series, pl.DataFrame, pd.Series, or pd.DataFrame)
        benchmark: Benchmark returns (pl.Series, pl.DataFrame, pd.Series, or pd.DataFrame)
        periods: Number of periods per year for annualization (default: 252)
        annualize: Whether to annualize the tracking error (default: True)
        epsilon: Small value to avoid division by zero issues (default: 1e-12)

    Returns:
        float: Tracking error (annualized if annualize=True)
    """
    aligned = _align_two_series_pl(returns, benchmark, col_a="p", col_b="b")
    aligned = aligned.drop_nulls()
    pairs = drop_date_if_present(aligned)
    if pairs.width != 2 or pairs.height == 0:
        return 0.0
    te = float((pairs["p"] - pairs["b"]).cast(pl.Float64).std(ddof=0))
    if te <= epsilon or np.isnan(te):
        return 0.0
    if annualize:
        te *= np.sqrt(periods)  # Annualize tracking error to match QuantStats
    return float(te)

def information_ratio_polars(
    returns, benchmark, *, periods: int = 252, annualize: bool = True, epsilon: float = 1e-12
) -> float:
    """
    Calculate the Information Ratio as (mean(active_returns) * periods) / tracking_error
    to match quantstats.stats.information_ratio.
    
    Args:
        returns: Portfolio returns (pl.Series, pl.DataFrame, pd.Series, or pd.DataFrame)
        benchmark: Benchmark returns (pl.Series, pl.DataFrame, pd.Series, or pd.DataFrame)
        periods: Number of periods per year for annualization (default: 252)
        annualize: Whether to annualize the result (default: True)
        epsilon: Small value to avoid division by zero (default: 1e-12)
    
    Returns:
        float: Information Ratio
    """
    # Align returns and benchmark
    aligned = _align_two_series_pl(returns, benchmark, col_a="p", col_b="b")
    aligned = aligned.drop_nulls()
    pairs = drop_date_if_present(aligned)
    
    # Check for valid input
    if pairs.width != 2 or pairs.height == 0:
        return 0.0
    
    # Calculate active returns (portfolio - benchmark)
    active = (pairs["p"] - pairs["b"]).cast(pl.Float64)
    
    # Compute mean of active returns
    mu = float(active.mean())
    
    # Compute tracking error (standard deviation of active returns)
    te = active.std()
    
    # Handle edge cases
    if te <= epsilon or np.isnan(te) or np.isnan(mu):
        return 0.0
    
    # Calculate Information Ratio
    if annualize:
        # Annualize the mean by multiplying by periods, as per QuantStats
        ir = (mu * math.sqrt(periods)) / te
    else:
        ir = mu / te
    
    return float(ir)
def greeks_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame],
    benchmark: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame],
    periods: float = 252.0
) -> pd.DataFrame:
    aligned = _align_two_series_pl(returns, benchmark, col_a="r", col_b="b").drop_nulls()
    if aligned.height < 2:
        return pd.DataFrame({"beta": [0.0], "alpha": [0.0]})

    stats = aligned.select(
        pl.col("r").mean().alias("mean_r"),
        pl.col("b").mean().alias("mean_b"),
        pl.cov("r", "b").alias("cov_rb"),
        pl.col("b").var(ddof=1).alias("var_b")
    )

    mean_r, mean_b, cov_rb, var_b = stats.row(0)

    if not np.isfinite(var_b) or abs(var_b) < 1e-18:
        beta = np.nan
    else:
        beta = cov_rb / var_b

    alpha = (mean_r - beta * mean_b) * periods if np.isfinite(beta) else np.nan

    return pd.DataFrame({"beta": [beta], "alpha": [alpha]}).fillna(0)


def rolling_greeks_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame],
    benchmark: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame],
    periods: int = 252
) -> pl.DataFrame:
    window = int(periods)
    if window <= 1:
        raise ValueError("periods must be greater than 1 for rolling greeks")

    aligned = (
        _align_two_series_pl(returns, benchmark, col_a="r", col_b="b")
        .drop_nulls()
        .sort("date")
    )

    if aligned.height < window:
        return pl.DataFrame({"date": [], "beta": [], "alpha": []})

    rolling_means = aligned.with_columns([
        pl.col("r").rolling_mean(window_size=window, min_samples=window).alias("mean_r"),
        pl.col("b").rolling_mean(window_size=window, min_samples=window).alias("mean_b"),
        (pl.col("r") * pl.col("b")).rolling_mean(window_size=window, min_samples=window).alias("mean_rb"),
        (pl.col("b") ** 2).rolling_mean(window_size=window, min_samples=window).alias("mean_b2"),
    ])

    cov_expr = pl.col("mean_rb") - pl.col("mean_r") * pl.col("mean_b")
    var_b_expr = pl.col("mean_b2") - pl.col("mean_b") ** 2
    eps = 1e-18

    rolling_stats = rolling_means.with_columns([
        pl.when(var_b_expr.abs() <= eps)
        .then(pl.lit(np.nan))
        .otherwise(cov_expr / var_b_expr)
        .alias("beta")
    ])

    mean_r_full = float(aligned["r"].mean())
    mean_b_full = float(aligned["b"].mean())

    result = (
        rolling_stats
        .with_columns(
            (pl.lit(mean_r_full) - pl.col("beta") * pl.lit(mean_b_full)).alias("alpha")
        )
        .select(["date", "beta", "alpha"])
        .drop_nulls(["beta"])
    )

    return result


def compare_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame],
    benchmark: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame],
    aggregate: Optional[str] = None,
    compounded: bool = True,
    round_vals: Optional[int] = None
) -> pl.DataFrame:
    returns = prepare_returns_polars(returns)
    benchmark = prepare_returns_polars(benchmark)
    aligned = _align_two_series_pl(returns, benchmark, col_a="r", col_b="b")
    if aggregate:
        agg_r = aggregate_returns_polars(aligned.select(["date", "r"]), aggregate, compounded)
        date,agg_r = agg_r['date'] = agg_r["date"], agg_r["r"]
        agg_b = aggregate_returns_polars(aligned.select(["date", "b"]), aggregate, compounded)["r"]
        data = pl.DataFrame({"date":date,"Benchmark": agg_b * 100, "Returns": agg_r * 100})
    else:
        data = pl.DataFrame({"date":aligned["date"], "Benchmark": aligned["b"] * 100, "Returns": aligned["r"] * 100})
    
    data = data.with_columns(
        pl.col("Benchmark").replace(0.0, np.nan).alias("Benchmark")
    ).with_columns(
        (pl.col("Returns") / pl.col("Benchmark")).alias("Multiplier")
    )
    data = data.with_columns(
        pl.when(pl.col("Returns") >= pl.col("Benchmark"))
        .then(pl.lit("+"))
        .otherwise(pl.lit("-"))
        .alias("Won")
    )
    
    if round_vals is not None:
        data = data.with_columns([pl.col(col).round(round_vals) for col in ["Benchmark", "Returns", "Multiplier"]])
    return data

def mtd_polars(
    returns: Union[pl.Series, pl.DataFrame, pd.Series, pd.DataFrame],
    returns_index: Optional[pd.Index] = None,
    compounded: bool = True,
    date_col: Optional[str] = "date"
) -> Union[float, pd.Series]:
    returns = prepare_returns_polars(returns)
    if isinstance(returns, pl.DataFrame):
        if date_col not in returns.columns:
            if returns_index is None:
                raise ValueError("date_col not found and returns_index not provided")
            returns = returns.with_columns(pl.Series(date_col, returns_index))
        last_date = returns[date_col].max()
        if last_date is None:
            return pd.Series({col: 0.0 for col in returns.columns if col != date_col})
        last_month = last_date.month
        last_year = last_date.year
        df = returns.filter((pl.col(date_col).dt.month() == last_month) & (pl.col(date_col).dt.year() == last_year))
        return_cols = [col for col in df.columns if col != date_col]
        if df.height == 0:
            return pd.Series({col: 0.0 for col in return_cols})
        if compounded:
            results = {col: (1 + df[col]).product() - 1 for col in return_cols}
            return pd.Series(results)
        results = {col: df[col].sum() for col in return_cols}
        return pd.Series(results)
    else:
        if returns_index is None:
            raise ValueError("returns_index must be provided for Series input")
        df = pl.DataFrame({"returns": returns, date_col: returns_index})
        last_date = df[date_col].max()
        if last_date is None:
            return 0.0
        last_month = last_date.month
        last_year = last_date.year
        df = df.filter((pl.col(date_col).dt.month() == last_month) & (pl.col(date_col).dt.year() == last_year))
        if df.height == 0:
            return 0.0
        return ((1 + df["returns"]).product() - 1) if compounded else df["returns"].sum()

def month_label_expr(
    date_expr: pl.Expr,
    *,
    style: Literal["short", "upper", "num"] = "upper"
) -> pl.Expr:
    """
    Return a Polars expression that renders the month label:
    - 'short' -> 'Jan', 'Feb', ...
    - 'upper' -> 'JAN', 'FEB', ...
    - 'num'   -> 1..12 (Int)
    """
    if style == "short":
        return date_expr.dt.strftime("%b")
    if style == "upper":
        return date_expr.dt.strftime("%b").str.to_uppercase()
    if style == "num":
        return date_expr.dt.month()
    raise ValueError("style must be 'short' | 'upper' | 'num'")

def add_period_keys(
    df: pl.DataFrame,
    *,
    date_col: str,
    out_year_col: str,
    out_month_col: str,
    month_style: Literal["short", "upper", "num"] = "upper"
) -> pl.DataFrame:
    """Add period key columns (year + month label) without hard-coded names."""
    return df.with_columns([
        pl.col(date_col).dt.year().alias(out_year_col),
        month_label_expr(pl.col(date_col), style=month_style).alias(out_month_col),
    ])

def group_returns(
    df: pl.DataFrame,
    *,
    year_col: str,
    month_col: str,
    value_col: str,
    out_col: str = "agg",
    compounded: bool = True
) -> pl.DataFrame:
    """
    Group by (year, month) with either compounded product (∏(1+r)-1) or mean.
    """
    if compounded:
        expr = ((1.0 + pl.col(value_col)).product() - 1.0).alias(out_col)
    else:
        expr = pl.col(value_col).mean().alias(out_col)
    return df.group_by([year_col, month_col]).agg(expr)

def to_long_table(
    grouped: pl.DataFrame,
    *,
    year_col: str,
    month_col: str,
    value_col: str,
    out_year: str = "Year",
    out_month: str = "Month",
    out_value: str = "Returns"
) -> pl.DataFrame:
    """Rename to a canonical long table and sort."""
    return (
        grouped.rename({year_col: out_year, month_col: out_month, value_col: out_value})
               .select([pl.col(out_year).cast(pl.Utf8), pl.col(out_month), pl.col(out_value).cast(pl.Float64)])
               .sort([out_year, out_month])
    )

def pivot_months_wide(
    long_df: pl.DataFrame,
    *,
    year_col: str = "Year",
    month_col: str = "Month",
    value_col: str = "Returns"
) -> pl.DataFrame:
    """Pivot long -> wide by month labels."""
    return long_df.pivot(index=year_col, on=month_col, values=value_col).sort(year_col)

def ensure_month_columns(
    wide_df: pl.DataFrame,
    *,
    year_col: str = "Year",
    month_labels: Iterable,
    fill_value: float = 0.0
) -> pl.DataFrame:
    """
    Ensure target list of month labels exists as columns, adding missing as fill_value,
    and return with columns ordered as [year_col] + list(month_labels)
    """
    for m in month_labels:
        if m not in wide_df.columns:
            wide_df = wide_df.with_columns(pl.lit(fill_value).alias(str(m)))
    return wide_df.select([year_col] + [str(m) for m in month_labels])

def yearly_aggregate(
    df: pl.DataFrame,
    *,
    date_col: str,
    value_col: str,
    out_year: str = "Year",
    out_col: str = "EOY",
    compounded: bool = True
) -> pl.DataFrame:
    """Annual aggregate (compounded or mean)."""
    y = df.with_columns(pl.col(date_col).dt.year().alias(out_year))
    if compounded:
        expr = ((1.0 + pl.col(value_col)).product() - 1.0).alias(out_col)
    else:
        expr = pl.col(value_col).mean().alias(out_col)
    agg = y.group_by(out_year).agg(expr)
    return agg.with_columns(pl.col(out_year).cast(pl.Utf8), pl.col(out_col).cast(pl.Float64)).sort(out_year)


# ---------------- convenience wrappers (QS-parity) ----------------

MONTHS_UPPER = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"]

def monthly_returns_long(
    returns: Union["pd.Series", pl.DataFrame, pl.Series],
    *,
    value_col: Optional[str] = None,
    compounded: bool = True,
    month_style: Literal["short", "upper", "num"] = "upper",
    # output names (you can override to fit other pipelines)
    out_year: str = "Year",
    out_month: str = "Month",
    out_value: str = "Returns",
) -> pl.DataFrame:
    """
    Polars-in/Polars-out LONG table: [out_year, out_month, out_value],
    with completely parametric internals.
    """
    df = returns  # ensures ['date', value_col]
    if value_col is None:
        value_col = _find_return_col_in_pl(df)
    keyed = add_period_keys(
        df, date_col="date", out_year_col="_y", out_month_col="_m", month_style=month_style
    )
    grp = group_returns(
        keyed, year_col="_y", month_col="_m", value_col=value_col, out_col="_ret", compounded=compounded
    )
    long_df = to_long_table(
        grp, year_col="_y", month_col="_m", value_col="_ret", out_year=out_year, out_month=out_month, out_value=out_value
    )
    return long_df

def monthly_returns_polars(
    returns: Union["pd.Series", pl.DataFrame, pl.Series],
    *,
    eoy: bool = True,
    compounded: bool = True,
    value_col: Optional[str] = None,
    month_style: Literal["short","upper","num"] = "upper",
    target_months: Optional[Iterable] = None,
    out_year: str = "Year",
    out_month: str = "Month",
    out_value: str = "Returns",
    out_eoy_col: str = "YTD",  # Changed to match QS
) -> pl.DataFrame:
    """
    QS-compatible wide monthly matrix (Polars).
    Columns are [out_year] + months (by `month_style`) + optional EOY.
    Values are *fractional* returns (QS uses fractional internally too).
    """
    # 1) long
    mon_long = monthly_returns_long(
        returns, value_col=value_col, compounded=compounded,
        month_style=month_style, out_year=out_year, out_month=out_month, out_value=out_value
    )

    # 2) wide
    wide = pivot_months_wide(mon_long, year_col=out_year, month_col=out_month, value_col=out_value)

    # 3) enforce target month columns + order
    if target_months is None:
        if month_style == "upper":
            target_months = MONTHS_UPPER
        elif month_style == "short":
            target_months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        else:  # 'num'
            target_months = list(range(1, 13))
    wide = ensure_month_columns(wide, year_col=out_year, month_labels=target_months, fill_value=0.0)

    # 4) EOY
    if eoy:
        df = returns #_coerce_series_to_pl(returns, name=value_col)
        value_col = _find_return_col_in_pl(df) if value_col is None else value_col
        yr = yearly_aggregate(df, date_col="date", value_col=value_col, out_year=out_year, out_col=out_eoy_col, compounded=compounded)
        wide = wide.join(yr, on=out_year, how="left")
    return wide

_EPS_ZERO = 1e-12

def _quantile_linear(sorted_vals: list[float], q: float) -> float:
    n = len(sorted_vals)
    if n == 0:
        return float("nan")
    if n == 1:
        return float(sorted_vals[0])
    if q <= 0.0:
        return float(sorted_vals[0])
    if q >= 1.0:
        return float(sorted_vals[-1])
    pos = (n - 1) * q



def compute_dd_durations_pl(episodes_dict):
    dur_dict = {}
    for strategy, episodes in episodes_dict.items():
        dur_dict[strategy] = episodes.with_columns(
            ((pl.col("end") - pl.col("start")).dt.total_days() + 1)
            .cast(pl.Int64)
            .alias("days")
        )
    return dur_dict

def compute_equity_curve_pl(df, ret_cols=None, out_suffix="_equity", add_phantom=True):
    if ret_cols is None:
        ret_cols = [c for c in df.columns if c != "date"]
    if add_phantom:
        min_date = df["date"].min()
        phantom = pl.DataFrame(
            {"date": [min_date - timedelta(days=1)], **{c: [0.0] for c in ret_cols}}
        )
        df = pl.concat([phantom, df], how="vertical")
    equity_cols = []
    for col in ret_cols:
        equity_col = col + out_suffix
        df = df.with_columns((1.0 + pl.col(col)).cum_prod().alias(equity_col))
        equity_cols.append(equity_col)
    return df, equity_cols

def compute_peaks_pl(df, equity_cols, out_suffix="_peaks"):
    peaks_cols = []
    for col in equity_cols:
        peak_col = col.replace("_equity", "") + out_suffix
        df = df.with_columns(pl.col(col).cum_max().alias(peak_col))
        peaks_cols.append(peak_col)
    return df, peaks_cols

def compute_drawdown_series_pl(df, equity_cols, peaks_cols, out_col="dd", remove_phantom=True):
    for equity_col, peak_col in zip(equity_cols, peaks_cols):
        dd_col = equity_col.replace("_equity", "") + f"_{out_col}"
        df = df.with_columns((pl.col(equity_col) / pl.col(peak_col) - 1.0).alias(dd_col))
    if remove_phantom:
        df = df.filter(pl.col("date") > df["date"].min())
    dd_cols = [c for c in df.columns if c.endswith(f"_{out_col}")]
    return df.select(["date"] + dd_cols)

def label_dd_episodes_pl(dd_df, dd_cols=None, eps=1e-12):
    if dd_cols is None:
        dd_cols = [c for c in dd_df.columns if c.endswith("_dd")]
    for col in dd_cols:
        zeroed = col + "_zeroed_dd"
        is_dd = col + "_is_dd"
        start_flag = col + "_start_flag"
        grp_col = col + "_grp"
        dd_df = dd_df.with_columns(
            pl.when(pl.col(col).abs() <= eps).then(0.0).otherwise(pl.col(col)).alias(zeroed)
        )
        dd_df = dd_df.with_columns((pl.col(zeroed) < 0).alias(is_dd))
        dd_df = dd_df.with_columns(
            (
                pl.col(is_dd)
                & (~pl.col(is_dd).shift(1).fill_null(False))
            ).cast(pl.Int64).alias(start_flag)
        )
        dd_df = dd_df.with_columns(pl.col(start_flag).cum_sum().alias(grp_col))
    return dd_df

def extract_dd_episodes_pl(labeled_dd, dd_cols):
    episodes = {}
    for col in dd_cols:
        zeroed = col + "_zeroed_dd"
        grp_col = col + "_grp"
        is_dd = col + "_is_dd"
        neg = labeled_dd.filter(pl.col(is_dd))
        base = neg.group_by(grp_col).agg(
            [
                pl.col("date").first().alias("start"),
                pl.col("date").last().alias("end"),
                pl.col(zeroed).min().alias("min_dd"),
                pl.col("date")
                .sort_by([pl.col(zeroed), pl.col("date")])
                .first()
                .alias("valley"),
            ]
        )
        base = base.rename({grp_col: "grp"})
        episodes[col.replace("_dd", "")] = base
    return episodes

def compute_tail_dd_pl(labeled_neg_dict, q_tail=0.99):
    tail_dict = {}
    for strategy, neg in labeled_neg_dict.items():
        zeroed = strategy + "_zeroed_dd"
        grp_col = "grp"
        cap = neg.group_by(grp_col).agg(
            (-pl.col(zeroed)).quantile(q_tail, "linear").alias("cap_q")
        )
        joined = neg.join(cap, on=grp_col, how="left")
        ddq = joined.group_by(grp_col).agg(
            pl.col(zeroed)
            .filter((-pl.col(zeroed)) < pl.col("cap_q"))
            .min()
            .alias("min_dd_q")
        )
        tail_dict[strategy] = ddq
    return tail_dict

def assemble_dd_details_pl(dur_dict, tail_dict, strategies, q_tail=0.99, as_pct=True):
    details = {}
    tail_col = f"{int(q_tail * 100)}% max drawdown"
    factor = 100 if as_pct else 1
    for strategy in strategies:
        table = dur_dict[strategy].join(
            tail_dict[strategy],
            on="grp",
            how="left",
        )
        table = table.with_columns(
            [
                (pl.col("min_dd") * factor).alias("max drawdown"),
                (pl.col("min_dd_q").fill_null(pl.col("min_dd")) * factor).alias(tail_col),
            ]
        )
        table = table.with_columns(
            pl.col("start").dt.strftime("%Y-%m-%d"),
            pl.col("valley").dt.strftime("%Y-%m-%d"),
            pl.col("end").dt.strftime("%Y-%m-%d"),
        )
        table = table.select(
            ["start", "valley", "end", "days", "max drawdown", tail_col]
        ).sort("start")
        details[strategy] = table
    return details

def drawdown_details_pl(returns, value_col="r", q_tail=0.99):
    df = to_pl_returns_df(returns)
    ret_cols = [c for c in df.columns if c != "date"]
    strategies = ret_cols[:]
    eq, equity_cols = compute_equity_curve_pl(df, ret_cols=ret_cols)
    peaks, peaks_cols = compute_peaks_pl(eq, equity_cols)
    dd_df = compute_drawdown_series_pl(peaks, equity_cols, peaks_cols)
    dd_cols = [f"{col}_dd" for col in ret_cols]
    labeled = label_dd_episodes_pl(dd_df.select(["date"] + dd_cols), dd_cols=dd_cols)
    episodes_dict = {}
    labeled_neg_dict = {}
    for col in dd_cols:
        strategy = col.replace("_dd", "")
        zeroed = col + "_zeroed_dd"
        is_dd = col + "_is_dd"
        grp_col = col + "_grp"
        labeled_dd = labeled.select(["date", col, zeroed, is_dd, grp_col])
        episodes_dict[strategy] = extract_dd_episodes_pl(labeled_dd, [col])[strategy]
        labeled_neg = labeled_dd.filter(pl.col(is_dd)).rename(
            {zeroed: strategy + "_zeroed_dd", grp_col: "grp"}
        )
        labeled_neg_dict[strategy] = labeled_neg
    dur_dict = compute_dd_durations_pl(episodes_dict)
    tail_dict = compute_tail_dd_pl(labeled_neg_dict, q_tail=q_tail)
    details = assemble_dd_details_pl(dur_dict, tail_dict, strategies, q_tail=q_tail, as_pct=True)
    if len(details) == 1:
        return next(iter(details.values()))
    return details

def _max_drawdown_abs_pl(returns_pd: pd.Series) -> float:
    df_pl = to_pl_returns_df(returns_pd)
    eq = (1.0 + pl.col("r")).cum_prod().alias("eq")
    dd = (pl.col("eq") / pl.col("eq").cum_max() - 1.0).alias("dd")
    dd_min = df_pl.select(dd.min()).item()
    return float(-dd_min) if dd_min is not None else 0.0

def max_drawdown_pl(details):
    if isinstance(details, dict):
        return {k: max_drawdown_pl(v) for k, v in details.items()}
    if details.height == 0:
        return 0.0
    return details["max drawdown"].min() / 100.0

def avg_drawdown_pl(details):
    if isinstance(details, dict):
        return {k: avg_drawdown_pl(v) for k, v in details.items()}
    if details.height == 0:
        return np.nan
    return details["max drawdown"].mean() / 100.0

def longest_dd_days_pl(details):
    if isinstance(details, dict):
        return {k: longest_dd_days_pl(v) for k, v in details.items()}
    if details.height == 0:
        return 0
    return details["days"].max()

def avg_dd_days_pl(details):
    if isinstance(details, dict):
        return {k: avg_dd_days_pl(v) for k, v in details.items()}
    if details.height == 0:
        return np.nan
    return float(np.round(details["days"].mean()))

def max_dd_date_pl(details):
    if isinstance(details, dict):
        return {k: max_dd_date_pl(v) for k, v in details.items()}
    if details.height == 0:
        return np.nan
    min_row = details.sort("max drawdown").head(1)
    return str(min_row["valley"].item())

def max_dd_start_pl(details):
    if isinstance(details, dict):
        return {k: max_dd_start_pl(v) for k, v in details.items()}
    if details.height == 0:
        return np.nan
    min_row = details.sort("max drawdown").head(1)
    return str(min_row["start"].item())

def max_dd_end_pl(details):
    if isinstance(details, dict):
        return {k: max_dd_end_pl(v) for k, v in details.items()}
    if details.height == 0:
        return np.nan
    min_row = details.sort("max drawdown").head(1)
    return str(min_row["end"].item())

def _calc_dd_polars(df_pl: pl.DataFrame, as_pct: bool = False) -> pd.DataFrame:
    cols = [c for c in df_pl.columns if c != 'date']
    details_dict = drawdown_details_pl(df_pl)
    data = {}
    for col in cols:
        details = details_dict[col] if isinstance(details_dict, dict) else details_dict
        max_dd = max_drawdown_pl(details) * (100 if as_pct else 1)
        avg_dd = avg_drawdown_pl(details) * (100 if as_pct else 1)
        longest_dd = longest_dd_days_pl(details)
        avg_dd_days = avg_dd_days_pl(details)
        max_dd_date = max_dd_date_pl(details)
        max_dd_start = max_dd_start_pl(details)
        max_dd_end = max_dd_end_pl(details)
        data[col] = [max_dd, avg_dd, longest_dd, avg_dd_days, max_dd_date, max_dd_start, max_dd_end]
    dd_df = pd.DataFrame(data, index=['Max Drawdown %' if as_pct else 'Max Drawdown', 'Avg. Drawdown %' if as_pct else 'Avg. Drawdown', 'Longest DD Days', 'Avg. Drawdown Days', 'Max DD Date', 'Max DD Period Start', 'Max DD Period End'])
    return dd_df

def metrics_polars(
    returns,
    benchmark=None,
    rf=0.0,
    display=True,
    mode="basic",
    sep=False,
    compounded=True,
    periods_per_year=252,
    prepare_returns=True,
    match_dates=True,
    **kwargs,
):
    """
    Polars-based version of metrics function. Computes using Polars, outputs pd.DataFrame for QS plotting compatibility.
    """
    import pandas as pd
    from tabulate import tabulate
    from math import sqrt as _sqrt

    # Convert inputs to Polars
    returns_pl = to_pl_returns_df(returns) if not isinstance(returns, pl.DataFrame) else returns
    # if benchmark is not None:
    # benchmark can be pd.Series/df, pl.Series/df
    if not isinstance(benchmark, pl.DataFrame):
        benchmark_pl = to_pl_returns_df(benchmark, value_col='benchmark')
    else:
        # rename the (single) value column to 'benchmark' and keep only date+benchmark
        val_cols = [c for c in benchmark.columns if c != 'date']
        if len(val_cols) != 1:
            raise ValueError("Ambiguous benchmark DataFrame: expected exactly one non-date column")
        benchmark_pl = (
            benchmark.rename({val_cols[0]: 'benchmark'})
                    .select(['date', 'benchmark'])
        )

    # finalize types and drop nulls
    benchmark_pl = (
        benchmark_pl
        .with_columns(
            pl.col('date').cast(pl.Datetime('us')),
            pl.col('benchmark').cast(pl.Float64),
        )
        .drop_nulls(['date', 'benchmark'])
    )

    # Clean if match_dates
    if match_dates:
        returns_pl = returns_pl.drop_nulls()

    # Remove tz
    if 'date' in returns_pl.columns:
        returns_pl = returns_pl.with_columns(pl.col('date').dt.replace_time_zone(None))
    if benchmark is not None and 'date' in benchmark_pl.columns:
        benchmark_pl = benchmark_pl.with_columns(pl.col('date').dt.replace_time_zone(None))

    win_year = periods_per_year

    benchmark_colname = kwargs.get("benchmark_title", "Benchmark")
    strategy_colname = kwargs.get("strategy_title", "Strategy")

    if 'date' in returns_pl.columns:
        return_cols = [c for c in returns_pl.columns if c != 'date']
    else:
        return_cols = returns_pl.columns

    if len(return_cols) > 1:
        strategy_colname = return_cols

    blank = [""] * (len(strategy_colname) if isinstance(strategy_colname, list) else 1)
    if benchmark is not None:
        blank += [""]

    # Prepare
    if prepare_returns:
        returns_pl = prepare_returns_polars(returns_pl, rf=rf, nperiods=periods_per_year)
        if benchmark is not None:
            benchmark_pl = prepare_returns_polars(benchmark_pl, rf=rf, nperiods=periods_per_year)

    # Align with benchmark if present
    if benchmark is not None:
        if 'date' not in returns_pl.columns or 'date' not in benchmark_pl.columns:
            raise ValueError("Date column required for benchmark alignment")
        df_pl = returns_pl.join(benchmark_pl, on='date', how='left').fill_null(0.0)
    else:
        df_pl = returns_pl.fill_null(0)

    # Match dates if requested
    if match_dates and benchmark is not None:
        return_cols = [c for c in df_pl.columns if c not in ['date', 'benchmark']]
        first_col = return_cols[0] if return_cols else None
        if first_col:
            returns_first = df_pl.filter(pl.col(first_col) != 0)['date'].min() or df_pl['date'].min()
            bench_first = df_pl.filter(pl.col('benchmark') != 0)['date'].min() or df_pl['date'].min()
            loc = max(returns_first, bench_first)
            df_pl = df_pl.filter(pl.col('date') >= loc)

    # Rename columns to titles
    if not isinstance(strategy_colname, list):
        strategy_colname = [strategy_colname]
    rename_map = {old: new for old, new in zip(return_cols, strategy_colname)}
    if benchmark is not None:
        rename_map['benchmark'] = benchmark_colname
    df_pl = df_pl.rename(rename_map)

    # Start/end/rf
    s_start = {}
    s_end = {}
    s_rf = {}
    cols = strategy_colname + [benchmark_colname] if benchmark is not None else strategy_colname
    for col in cols:
        col_df = df_pl.filter(pl.col(col).is_not_null())
        s_start[col] = col_df['date'].min().strftime("%Y-%m-%d") if 'date' in col_df.columns and col_df.height > 0 else "-"
        s_end[col] = col_df['date'].max().strftime("%Y-%m-%d") if 'date' in col_df.columns and col_df.height > 0 else "-"
        s_rf[col] = rf

    # Metrics pd DF
    metrics = pd.DataFrame()
    metrics["Start Period"] = pd.Series(s_start)
    metrics["End Period"] = pd.Series(s_end)
    metrics["Risk-Free Rate %"] = pd.Series(s_rf) * 100
    metrics["Time in Market %"] = exposure_polars(df_pl) * (100 if display else 1)

    metrics["~"] = blank

    if compounded:
        metrics["Cumulative Return %"] = comp_polars(df_pl) * (100 if display else 1)
    else:
        metrics["Total Return %"] = df_pl.sum().to_pandas().iloc[0] * (100 if display else 1)

    metrics["CAGR %"] = cagr_polars(df_pl, periods_per_year=periods_per_year) * (100 if display else 1)

    metrics["~~~~~~~~~~~~~~"] = blank

    metrics["Sharpe"] = sharpe_polars(df_pl, rf=rf, periods=periods_per_year, annualize=True)
    metrics["Prob. Sharpe Ratio %"] = probabilistic_sharpe_ratio_polars(df_pl, rf=rf, periods=periods_per_year, annualize=False) * (100 if display else 1)

    if mode.lower() == "full":
        metrics["Smart Sharpe"] = smart_sharpe_polars(df_pl, rf=rf, periods=periods_per_year, annualize=True)

    metrics["Sortino"] = sortino_polars(df_pl, rf=rf, periods=periods_per_year, annualize=True)
    if mode.lower() == "full":
        metrics["Smart Sortino"] = smart_sortino_polars(df_pl, rf=rf, periods=periods_per_year, annualize=True)

    metrics["Sortino/√2"] = adjusted_sortino_polars(df_pl, rf=rf, periods=periods_per_year, annualize=True)
    if mode.lower() == "full":
        metrics["Smart Sortino/√2"] = adjusted_sortino_polars(df_pl, rf=rf, periods=periods_per_year, annualize=True, smart=True)

    metrics["Omega"] = omega_polars(df_pl, rf=rf, periods=periods_per_year)

    metrics["~~~~~~~~"] = blank

    dd = _calc_dd_polars(df_pl, as_pct=True if display else False)
    for metric_name in dd.index:
        metrics[metric_name] = dd.loc[metric_name].values

    if mode.lower() == "full":
        metrics["Volatility (ann.) %"] = volatility_polars(df_pl, periods=periods_per_year, annualize=True) * (100 if display else 1)
        if benchmark is not None:
            # Ensure DataFrames have 'date' and renamed columns to match function expectations
            benchmark_df_r2 = pl.DataFrame({"date": df_pl["date"], "x": df_pl[benchmark_colname]})
            benchmark_df_ir = pl.DataFrame({"date": df_pl["date"], "b": df_pl[benchmark_colname]})
            benchmark_df_greeks = pl.DataFrame({"date": df_pl["date"], "b": df_pl[benchmark_colname]})
            if len(strategy_colname) == 1:
                strategy_df_r2 = pl.DataFrame({"date": df_pl["date"], "y": df_pl[strategy_colname[0]]})
                strategy_df_ir = pl.DataFrame({"date": df_pl["date"], "p": df_pl[strategy_colname[0]]})
                strategy_df_greeks = pl.DataFrame({"date": df_pl["date"], "r": df_pl[strategy_colname[0]]})
                metrics["R^2"] = [r_squared_polars(strategy_df_r2, benchmark_df_r2), '-']
                metrics["Information Ratio"] = [information_ratio_polars(strategy_df_ir, benchmark_df_ir), '-']
                greeks = greeks_polars(strategy_df_greeks, benchmark_df_greeks, periods=periods_per_year)
                metrics["Beta"] = [greeks['beta'].item(), "-"]
                metrics["Alpha"] = [greeks['alpha'].item(), "-"]
                metrics["Correlation"] = [df_pl.select(pl.corr(strategy_colname[0], benchmark_colname)).item(), "-"]
                metrics["Treynor Ratio"] = [treynor_ratio_polars(strategy_df_greeks, benchmark_df_greeks, periods=periods_per_year), "-"]
            else:
                metrics["R^2"] = [r_squared_polars(
                    pl.DataFrame({"date": df_pl["date"], "y": df_pl[col]}),
                    benchmark_df_r2
                ) for col in strategy_colname] + ['-']
                metrics["Information Ratio"] = [information_ratio_polars(
                    pl.DataFrame({"date": df_pl["date"], "p": df_pl[col]}),
                    benchmark_df_ir
                ) for col in strategy_colname] + ['-']
                metrics["Beta"] = [greeks_polars(
                    pl.DataFrame({"date": df_pl["date"], "r": df_pl[col]}),
                    benchmark_df_greeks,
                    periods=periods_per_year
                )['beta'].item() for col in strategy_colname] + ['-']
                metrics["Alpha"] = [greeks_polars(
                    pl.DataFrame({"date": df_pl["date"], "r": df_pl[col]}),
                    benchmark_df_greeks,
                    periods=periods_per_year
                )['alpha'].item() for col in strategy_colname] + ['-']
                metrics["Correlation"] = [df_pl.select(pl.corr(col, benchmark_colname)).item() for col in strategy_colname] + ['-']
                metrics["Treynor Ratio"] = [treynor_ratio_polars(
                    pl.DataFrame({"date": df_pl["date"], "r": df_pl[col]}),
                    benchmark_df_greeks,
                    periods=periods_per_year
                ) for col in strategy_colname] + ['-']

    if mode.lower() == "full":
        metrics["Calmar"] = calmar_polars(df_pl, periods_per_year=periods_per_year)
        metrics["Skew"] = skew_polars(df_pl)
        metrics["Kurtosis"] = kurtosis_polars(df_pl)

        metrics["~~~~~~~~~~"] = blank

        metrics["Expected Daily %"] = expected_return_polars(df_pl, compounded=compounded) * (100 if display else 1)
        metrics["Expected Monthly %"] = expected_return_polars(df_pl, aggregate='M', compounded=compounded) * (100 if display else 1)
        metrics["Expected Yearly %"] = expected_return_polars(df_pl, aggregate='Y', compounded=compounded) * (100 if display else 1)

        metrics["Kelly Criterion %"] = kelly_criterion_polars(df_pl) * (100 if display else 1)
        metrics["Risk of Ruin %"] = risk_of_ruin_polars(df_pl)

        metrics["Daily Value-at-Risk %"] = -abs(value_at_risk_polars(df_pl)) * (100 if display else 1)
        metrics["Expected Shortfall (cVaR) %"] = -abs(conditional_value_at_risk_polars(df_pl)) * (100 if display else 1)

    metrics["~~~~~~"] = blank

    if mode.lower() == "full":
        metrics["Max Consecutive Wins"] = consecutive_wins_polars(df_pl)
        metrics["Max Consecutive Losses"] = consecutive_losses_polars(df_pl)

    metrics["Gain/Pain Ratio"] = gain_to_pain_ratio_polars(df_pl, rf=rf)
    metrics["Gain/Pain (1M)"] = gain_to_pain_ratio_polars(df_pl, rf=rf, resolution="M", dates=df_pl['date'])

    metrics["~~~~~~~"] = blank

    metrics["Payoff Ratio"] = payoff_ratio_polars(df_pl)
    metrics["Profit Factor"] = profit_factor_polars(df_pl)
    metrics["Common Sense Ratio"] = common_sense_ratio_polars(df_pl)
    metrics["CPC Index"] = cpc_index_polars(df_pl)
    metrics["Tail Ratio"] = tail_ratio_polars(df_pl)
    metrics["Outlier Win Ratio"] = outlier_win_ratio_polars(df_pl)
    metrics["Outlier Loss Ratio"] = outlier_loss_ratio_polars(df_pl)

    metrics["~~"] = blank

    # Periods
    today = df_pl['date'].max()
    m3 = today - relativedelta(months=3)
    m6 = today - relativedelta(months=6)
    y1 = today - relativedelta(years=1)
    ytd_start = datetime(today.year, 1, 1)

    metrics["MTD %"] = mtd_polars(df_pl, compounded=compounded) * (100 if display else 1)
    metrics["3M %"] = comp_polars(df_pl.filter(pl.col("date") >= m3)) * (100 if display else 1)
    metrics["6M %"] = comp_polars(df_pl.filter(pl.col("date") >= m6)) * (100 if display else 1)
    metrics["YTD %"] = comp_polars(df_pl.filter(pl.col("date") >= ytd_start)) * (100 if display else 1)
    metrics["1Y %"] = comp_polars(df_pl.filter(pl.col("date") >= y1)) * (100 if display else 1)

    d = today - relativedelta(months=35)
    metrics["3Y (ann.) %"] = cagr_polars(df_pl.filter(pl.col("date") >= d), periods_per_year=periods_per_year) * (100 if display else 1)

    d = today - relativedelta(months=59)
    metrics["5Y (ann.) %"] = cagr_polars(df_pl.filter(pl.col("date") >= d), periods_per_year=periods_per_year) * (100 if display else 1)

    d = today - relativedelta(years=10)
    metrics["10Y (ann.) %"] = cagr_polars(df_pl.filter(pl.col("date") >= d), periods_per_year=periods_per_year) * (100 if display else 1)

    metrics["All-time (ann.) %"] = cagr_polars(df_pl, periods_per_year=periods_per_year) * (100 if display else 1)

    if mode.lower() == "full":
        metrics["~~~"] = blank
        metrics["Best Day %"] = best_polars(df_pl) * (100 if display else 1)
        metrics["Worst Day %"] = worst_polars(df_pl) * (100 if display else 1)
        metrics["Best Month %"] = best_polars(df_pl, aggregate='M', compounded=compounded) * (100 if display else 1)
        metrics["Worst Month %"] = worst_polars(df_pl, aggregate='M', compounded=compounded) * (100 if display else 1)
        metrics["Best Year %"] = best_polars(df_pl, aggregate='Y', compounded=compounded) * (100 if display else 1)
        metrics["Worst Year %"] = worst_polars(df_pl, aggregate='Y', compounded=compounded) * (100 if display else 1)

    metrics["~~~~"] = blank

    metrics["Recovery Factor"] = recovery_factor_polars(df_pl)
    metrics["Ulcer Index"] = ulcer_index_pl(df_pl)
    metrics["Serenity Index"] = serenity_index_polars(df_pl, rf=rf)

    if mode.lower() == "full":
        metrics["~~~~~"] = blank
        metrics["Avg. Up Month %"] = avg_win_polars(df_pl, aggregate='M', compounded=compounded) * (100 if display else 1)
        metrics["Avg. Down Month %"] = avg_loss_polars(df_pl, aggregate='M', compounded=compounded) * (100 if display else 1)
        metrics["Win Days %"] = win_rate_polars(df_pl) * (100 if display else 1)
        metrics["Win Month %"] = win_rate_polars(df_pl, aggregate='M', compounded=compounded) * (100 if display else 1)
        metrics["Win Quarter %"] = win_rate_polars(df_pl, aggregate='Q', compounded=compounded) * (100 if display else 1)
        metrics["Win Year %"] = win_rate_polars(df_pl, aggregate='Y', compounded=compounded) * (100 if display else 1)

        if benchmark is not None:
            metrics["~~~~~~~~~~~~"] = blank
            benchmark_df_r2 = pl.DataFrame({"date": df_pl["date"], "x": df_pl[benchmark_colname]})
            benchmark_df_ir = pl.DataFrame({"date": df_pl["date"], "b": df_pl[benchmark_colname]})
            benchmark_df_greeks = pl.DataFrame({"date": df_pl["date"], "b": df_pl[benchmark_colname]})
            if len(strategy_colname) == 1:
                strategy_df_r2 = pl.DataFrame({"date": df_pl["date"], "y": df_pl[strategy_colname[0]]})
                strategy_df_ir = pl.DataFrame({"date": df_pl["date"], "p": df_pl[strategy_colname[0]]})
                strategy_df_greeks = pl.DataFrame({"date": df_pl["date"], "r": df_pl[strategy_colname[0]]})
                metrics["R^2"] = [r_squared_polars(strategy_df_r2, benchmark_df_r2), '-']
                metrics["Information Ratio"] = [information_ratio_polars(strategy_df_ir, benchmark_df_ir), '-']
                greeks = greeks_polars(strategy_df_greeks, benchmark_df_greeks, periods=periods_per_year)
                metrics["Beta"] = [greeks['beta'].item(), "-"]
                metrics["Alpha"] = [greeks['alpha'].item(), "-"]
                metrics["Correlation"] = [df_pl.select(pl.corr(strategy_colname[0], benchmark_colname)).item(), "-"]
                metrics["Treynor Ratio"] = [treynor_ratio_polars(strategy_df_greeks, benchmark_df_greeks, periods=periods_per_year, rf=rf), "-"]
            else:
                metrics["R^2"] = [r_squared_polars(
                    pl.DataFrame({"date": df_pl["date"], "y": df_pl[col]}),
                    benchmark_df_r2
                ) for col in strategy_colname] + ['-']
                metrics["Information Ratio"] = [information_ratio_polars(
                    pl.DataFrame({"date": df_pl["date"], "p": df_pl[col]}),
                    benchmark_df_ir
                ) for col in strategy_colname] + ['-']
                metrics["Beta"] = [greeks_polars(
                    pl.DataFrame({"date": df_pl["date"], "r": df_pl[col]}),
                    benchmark_df_greeks,
                    periods=periods_per_year
                )['beta'].item() for col in strategy_colname] + ['-']
                metrics["Alpha"] = [greeks_polars(
                    pl.DataFrame({"date": df_pl["date"], "r": df_pl[col]}),
                    benchmark_df_greeks,
                    periods=periods_per_year
                )['alpha'].item() for col in strategy_colname] + ['-']
                metrics["Correlation"] = [df_pl.select(pl.corr(col, benchmark_colname)).item() for col in strategy_colname] + ['-']
                metrics["Treynor Ratio"] = [treynor_ratio_polars(
                    pl.DataFrame({"date": df_pl["date"], "r": df_pl[col]}),
                    benchmark_df_greeks,
                    periods=periods_per_year,
                    rf=rf
                ) for col in strategy_colname] + ['-']

    # Formatting (copy from original)
    for col in metrics.columns:
        try:
            metrics[col] = metrics[col].astype(float).round(2)
            if display:
                metrics[col] = metrics[col].astype(str)
        except:
            pass
        if display and "*int" in col:
            metrics[col] = metrics[col].str.replace(".0", "", regex=False)
            metrics.rename({col: col.replace("*int", "")}, axis=1, inplace=True)
        if display and "%" in col:
            metrics[col] = metrics[col] + "%"

    try:
        metrics["Longest DD Days"] = pd.to_numeric(metrics["Longest DD Days"]).astype("int")
        metrics["Avg. Drawdown Days"] = pd.to_numeric(metrics["Avg. Drawdown Days"]).astype("int")
        if display:
            metrics["Longest DD Days"] = metrics["Longest DD Days"].astype(str)
            metrics["Avg. Drawdown Days"] = metrics["Avg. Drawdown Days"].astype(str)
    except:
        metrics["Longest DD Days"] = "-"
        metrics["Avg. Drawdown Days"] = "-"

    metrics.columns = [col if "~" not in col else "" for col in metrics.columns]
    metrics.columns = [col[:-1] if "%" in col else col for col in metrics.columns]
    metrics = metrics.T

    if benchmark is not None:
        strategy_cols = strategy_colname if isinstance(strategy_colname, list) else [strategy_colname]
        metrics = metrics[strategy_cols + [benchmark_colname]]
    else:
        strategy_cols = strategy_colname if isinstance(strategy_colname, list) else [strategy_colname]
        metrics = metrics[strategy_cols]

    if display:
        print(tabulate(metrics, headers="keys", tablefmt="simple"))
        return None

    if not sep:
        metrics = metrics[metrics.index != ""]

    metrics = metrics.T
    metrics.columns = [c.replace(" %", "").replace(" *int", "").strip() for c in metrics.columns]
    # Ensure benchmark column (cleaned) appears first if present
    bench_col = benchmark_colname.replace(" %", "").replace(" *int", "").strip()
    if bench_col not in metrics.columns and benchmark_colname in metrics.columns:
        bench_col = benchmark_colname
    if bench_col in metrics.columns:
        metrics = metrics[[bench_col] + [c for c in metrics.columns if c != bench_col]]
    metrics = metrics.T
    columns = [benchmark_colname] + strategy_colname
    return metrics[columns]

# -----------------------------
# ADDITIONS: metric validations
# -----------------------------
def _dd_series_frac_np_pl(returns_pd: pd.Series) -> np.ndarray:
    df_pl = to_pl_returns_df(returns_pd)
    eq_df, eq_cols = compute_equity_curve_pl(df_pl)
    pk_df, pk_cols = compute_peaks_pl(eq_df, eq_cols)
    dd_df = compute_drawdown_series_pl(pk_df, eq_cols, pk_cols)
    dd_col = dd_df.columns[1]
    return dd_df[dd_col].to_numpy()

def _close(a, b, atol=1e-10, rtol=1e-3):
    if np.isinf(a) and np.isinf(b):
        return np.sign(a) == np.sign(b)
    return np.isclose(a, b, atol=atol, rtol=rtol, equal_nan=True)

def percent_diff(a, b):
    if np.isinf(a) and np.isinf(b) and np.sign(a) == np.sign(b):
        return 0.0
    if np.isnan(a) and np.isnan(b):
        return np.nan
    if b == 0:
        if a == 0:
            return 0.0
        else:
            return np.inf if a > 0 else -np.inf
    return ((a - b) / abs(b)) * 100 if abs(b) > 0 else np.nan

def check_drawdown_based_metrics(returns_pd: pd.Series, periods_per_year: int = 252, rf: float = 0.0):
    returns_pl = to_pl_returns_df(returns_pd)
    
    ui_o = ulcer_index_pl(returns_pl)
    upi_o = ulcer_performance_index_polars(returns_pl, rf=rf)
    ser_o = serenity_index_polars(returns_pl, rf=rf)
    rec_o = recovery_factor_polars(returns_pl)
    cal_o = calmar_polars(returns_pl)
    ui_q = float(qs.stats.ulcer_index(returns_pd))
    upi_q1 = float(qs.stats.ulcer_performance_index(returns_pd, rf=rf))
    upi_q2 = float(qs.stats.upi(returns_pd, rf=rf))
    ser_q = float(qs.stats.serenity_index(returns_pd, rf=rf))
    rec_q = float(qs.stats.recovery_factor(returns_pd))
    cal_q = float(qs.stats.calmar(returns_pd))
    print("— Drawdown-based metrics parity —")
    print(f"Ulcer Index: match={_close(ui_o, ui_q)} | ours={ui_o:.10f} qs={ui_q:.10f} | %diff={percent_diff(ui_o, ui_q):.4f}%")
    print(f"Ulcer Perf Index / UPI: match={_close(upi_o, upi_q1) and _close(upi_o, upi_q2)} | "
          f"ours={upi_o:.10f} qs_upi={upi_q1:.10f} / {upi_q2:.10f} | %diff={percent_diff(upi_o, upi_q1):.4f}%")
    print(f"Serenity Index: match={_close(ser_o, ser_q)} | ours={ser_o:.10f} qs={ser_q:.10f} | %diff={percent_diff(ser_o, ser_q):.4f}%")
    print(f"Recovery Factor: match={_close(rec_o, rec_q)} | ours={rec_o:.10f} qs={rec_q:.10f} | %diff={percent_diff(rec_o, rec_q):.4f}%")
    print(f"Calmar: match={_close(cal_o, cal_q)} | ours={cal_o:.10f} qs={cal_q:.10f} | %diff={percent_diff(cal_o, cal_q):.4f}%")

def check_sharpe_based_metrics(returns_pd: pd.Series, rf: float = 0.02 / 252, periods: int = 252, rolling_period: int = 126, annualize: bool = True, smart: bool = False):
    
    returns_pl = to_pl_returns_df(returns_pd)
    sharpe_o = sharpe_polars(returns_pl, rf=rf, periods=periods, annualize=annualize, smart=smart)
    smart_sharpe_o = smart_sharpe_polars(returns_pl, rf=rf, periods=periods, annualize=annualize)
    sortino_o = sortino_polars(returns_pl, rf=rf, periods=periods, annualize=annualize, smart=smart)
    smart_sortino_o = smart_sortino_polars(returns_pl, rf=rf, periods=periods, annualize=annualize)
    adjusted_sortino_o = adjusted_sortino_polars(returns_pl, rf=rf, periods=periods, annualize=annualize, smart=smart)
    prob_ratio_o = probabilistic_ratio_polars(returns_pl, rf=rf, base="sharpe", periods=periods, annualize=annualize, smart=smart)
    prob_sharpe_o = probabilistic_sharpe_ratio_polars(returns_pl, rf=rf, periods=periods, annualize=annualize, smart=smart)
    prob_sortino_o = probabilistic_sortino_ratio_polars(returns_pl, rf=rf, periods=periods, annualize=annualize, smart=smart)
    prob_adj_sortino_o = probabilistic_adjusted_sortino_ratio_polars(returns_pl, rf=rf, periods=periods, annualize=annualize, smart=smart)
    
    sharpe_q = qs.stats.sharpe(returns_pd, rf=rf, periods=periods, annualize=annualize, smart=smart)
    smart_sharpe_q = qs.stats.smart_sharpe(returns_pd, rf=rf, periods=periods, annualize=annualize)
    sortino_q = qs.stats.sortino(returns_pd, rf=rf, periods=periods, annualize=annualize, smart=smart)
    smart_sortino_q = qs.stats.smart_sortino(returns_pd, rf=rf, periods=periods, annualize=annualize)
    adjusted_sortino_q = qs.stats.adjusted_sortino(returns_pd, rf=rf, periods=periods, annualize=annualize, smart=smart)
    prob_ratio_q = qs.stats.probabilistic_ratio(returns_pd, rf=rf, base="sharpe", periods=periods, annualize=annualize, smart=smart)
    prob_sharpe_q = qs.stats.probabilistic_sharpe_ratio(returns_pd, rf=rf, periods=periods, annualize=annualize, smart=smart)
    prob_sortino_q = qs.stats.probabilistic_sortino_ratio(returns_pd, rf=rf, periods=periods, annualize=annualize, smart=smart)
    prob_adj_sortino_q = qs.stats.probabilistic_adjusted_sortino_ratio(returns_pd, rf=rf, periods=periods, annualize=annualize, smart=smart)

    print("— Sharpe-based metrics parity —")
    print(f"Sharpe: match={_close(sharpe_o, sharpe_q)} | ours={sharpe_o:.10f} qs={sharpe_q:.10f} | %diff={percent_diff(sharpe_o, sharpe_q):.4f}%")
    print(f"Smart Sharpe: match={_close(smart_sharpe_o, smart_sharpe_q)} | ours={smart_sharpe_o:.10f} qs={smart_sharpe_q:.10f} | %diff={percent_diff(smart_sharpe_o, smart_sharpe_q):.4f}%")
    print(f"Sortino: match={_close(sortino_o, sortino_q)} | ours={sortino_o:.10f} qs={sortino_q:.10f} | %diff={percent_diff(sortino_o, sortino_q):.4f}%")
    print(f"Smart Sortino: match={_close(smart_sortino_o, smart_sortino_q)} | ours={smart_sortino_o:.10f} qs={smart_sortino_q:.10f} | %diff={percent_diff(smart_sortino_o, smart_sortino_q):.4f}%")
    print(f"Adjusted Sortino: match={_close(adjusted_sortino_o, adjusted_sortino_q)} | ours={adjusted_sortino_o:.10f} qs={adjusted_sortino_q:.10f} | %diff={percent_diff(adjusted_sortino_o, adjusted_sortino_q):.4f}%")
    print(f"Probabilistic Ratio: match={_close(prob_ratio_o, prob_ratio_q)} | ours={prob_ratio_o:.10f} qs={prob_ratio_q:.10f} | %diff={percent_diff(prob_ratio_o, prob_ratio_q):.4f}%")
    print(f"Probabilistic Sharpe Ratio: match={_close(prob_sharpe_o, prob_sharpe_q)} | ours={prob_sharpe_o:.10f} qs={prob_sharpe_q:.10f} | %diff={percent_diff(prob_sharpe_o, prob_sharpe_q):.4f}%")
    print(f"Probabilistic Sortino Ratio: match={_close(prob_sortino_o, prob_sortino_q)} | ours={prob_sortino_o:.10f} qs={prob_sortino_q:.10f} | %diff={percent_diff(prob_sortino_o, prob_sortino_q):.4f}%")
    print(f"Probabilistic Adjusted Sortino Ratio: match={_close(prob_adj_sortino_o, prob_adj_sortino_q)} | ours={prob_adj_sortino_o:.10f} qs={prob_adj_sortino_q:.10f} | %diff={percent_diff(prob_adj_sortino_o, prob_adj_sortino_q):.4f}%")

    # Rolling series
    rolling_sharpe_o = rolling_sharpe_polars(returns_pl, rf=rf, rolling_period=rolling_period, annualize=annualize, periods_per_year=periods)
    rolling_sortino_o = rolling_sortino_polars(returns_pl, rf=rf, rolling_period=rolling_period, annualize=annualize, periods_per_year=periods)
    rolling_sharpe_q = qs.stats.rolling_sharpe(returns_pd, rf=rf, rolling_period=rolling_period, annualize=annualize, periods_per_year=periods)
    rolling_sortino_q = qs.stats.rolling_sortino(returns_pd, rf=rf, rolling_period=rolling_period, annualize=annualize, periods_per_year=periods)

    rolling_sharpe_match = np.allclose(rolling_sharpe_o.to_numpy(), rolling_sharpe_q.values, atol=1e-10, equal_nan=True)
    rolling_sharpe_max_diff = np.nanmax(np.abs(rolling_sharpe_o.to_numpy() - rolling_sharpe_q.values)) if not rolling_sharpe_match else 0.0
    mask_sharpe = np.abs(rolling_sharpe_q.values) > 1e-10
    if np.any(mask_sharpe):
        rel_diff_sharpe = np.abs((rolling_sharpe_o.to_numpy()[mask_sharpe] - rolling_sharpe_q.values[mask_sharpe]) / rolling_sharpe_q.values[mask_sharpe]) * 100
        rolling_sharpe_max_pct = np.nanmax(rel_diff_sharpe) if len(rel_diff_sharpe) > 0 else np.nan
    else:
        rolling_sharpe_max_pct = np.nan
    print(f"Rolling Sharpe: match={rolling_sharpe_match} | max abs diff={rolling_sharpe_max_diff:.10f} | max %diff={rolling_sharpe_max_pct:.4f}%")

    rolling_sortino_match = np.allclose(rolling_sortino_o.to_numpy(), rolling_sortino_q.values, atol=1e-10, equal_nan=True)
    rolling_sortino_max_diff = np.nanmax(np.abs(rolling_sortino_o.to_numpy() - rolling_sortino_q.values)) if not rolling_sortino_match else 0.0
    mask_sortino = np.abs(rolling_sortino_q.values) > 1e-10
    if np.any(mask_sortino):
        rel_diff_sortino = np.abs((rolling_sortino_o.to_numpy()[mask_sortino] - rolling_sortino_q.values[mask_sortino]) / rolling_sortino_q.values[mask_sortino]) * 100
        rolling_sortino_max_pct = np.nanmax(rel_diff_sortino) if len(rel_diff_sortino) > 0 else np.nan
    else:
        rolling_sortino_max_pct = np.nan
    print(f"Rolling Sortino: match={rolling_sortino_match} | max abs diff={rolling_sortino_max_diff:.10f} | max %diff={rolling_sortino_max_pct:.4f}%")


def check_statistical_metrics(returns_pl: pl.DataFrame, returns_pd: pd.Series):
    """
    Validate statistical metrics (skew, kurtosis).
    """
    print("\n— Statistical Metrics —")
    # print(returns_pl["returns"])
    skew_o = skew_polars(returns_pl)
    skew_q = qs.stats.skew(returns_pd)
    print(f"Skew: match={_close(skew_o, skew_q)} | ours={skew_o:.10f} qs={skew_q:.10f} | %diff={percent_diff(skew_o, skew_q):.4f}%")

    kurt_o = kurtosis_polars(returns_pl)
    kurt_q = qs.stats.kurtosis(returns_pd)
    print(f"Kurtosis: match={_close(kurt_o, kurt_q)} | ours={kurt_o:.10f} qs={kurt_q:.10f} | %diff={percent_diff(kurt_o, kurt_q):.4f}%")

def check_risk_metrics(returns_pl: pl.DataFrame, returns_pd: pd.Series, rf: float = 0.0):
    """
    Validate risk metrics (Kelly Criterion, Risk of Ruin, VaR, cVaR).
    """
    print("\n— Risk Metrics —")
    kelly_o = kelly_criterion_polars(returns_pl) * 100
    kelly_q = qs.stats.kelly_criterion(returns_pd) * 100
    print(f"Kelly Criterion %: match={_close(kelly_o, kelly_q)} | ours={kelly_o:.10f} qs={kelly_q:.10f} | %diff={percent_diff(kelly_o, kelly_q):.4f}%")

    ror_o = risk_of_ruin_polars(returns_pl) * 100
    ror_q = qs.stats.risk_of_ruin(returns_pd) * 100
    print(f"Risk of Ruin %: match={_close(ror_o, ror_q)} | ours={ror_o:.10f} qs={ror_q:.10f} | %diff={percent_diff(ror_o, ror_q):.4f}%")

    var_o = -abs(value_at_risk_polars(returns_pl)) * 100
    var_q = -abs(qs.stats.value_at_risk(returns_pd)) * 100
    print(f"Daily Value-at-Risk %: match={_close(var_o, var_q)} | ours={var_o:.10f} qs={var_q:.10f} | %diff={percent_diff(var_o, var_q):.4f}%")

    cvar_o = -abs(conditional_value_at_risk_polars(returns_pl)) * 100
    cvar_q = -abs(qs.stats.conditional_value_at_risk(returns_pd)) * 100
    print(f"Expected Shortfall (cVaR) %: match={_close(cvar_o, cvar_q)} | ours={cvar_o:.10f} qs={cvar_q:.10f} | %diff={percent_diff(cvar_o, cvar_q):.4f}%")

def check_trading_metrics(returns_pl: pl.DataFrame, returns_pd: pd.Series, rf: float = 0.0):
    print("\n— Trading Metrics —")
    
    gpr_o = gain_to_pain_ratio_polars(returns_pl["r"], rf)
    gpr_q = qs.stats.gain_to_pain_ratio(returns_pd, rf)
    print(f"Gain/Pain Ratio: match={_close(gpr_o, gpr_q)} | ours={gpr_o:.10f} qs={gpr_q:.10f} | %diff={percent_diff(gpr_o, gpr_q):.4f}%")
    gpr_1m_o = gain_to_pain_ratio_polars(returns_pl["r"], rf, resolution="M", dates=returns_pl["date"])
    gpr_1m_q = qs.stats.gain_to_pain_ratio(returns_pd, rf, "M")
    print(f"Gain/Pain (1M): match={_close(gpr_1m_o, gpr_1m_q)} | ours={gpr_1m_o:.10f} qs={gpr_1m_q:.10f} | %diff={percent_diff(gpr_1m_o, gpr_1m_q):.4f}%")
    payoff_o = payoff_ratio_polars(returns_pl["r"])
    payoff_q = qs.stats.payoff_ratio(returns_pd)
    print(f"Payoff Ratio: match={_close(payoff_o, payoff_q)} | ours={payoff_o:.10f} qs={payoff_q:.10f} | %diff={percent_diff(payoff_o, payoff_q):.4f}%")
    profit_factor_o = profit_factor_polars(returns_pl)
    profit_factor_q = qs.stats.profit_factor(returns_pd)
    print(f"Profit Factor: match={_close(profit_factor_o, profit_factor_q)} | ours={profit_factor_o:.10f} qs={profit_factor_q:.10f} | %diff={percent_diff(profit_factor_o, profit_factor_q):.4f}%")
    csr_o = common_sense_ratio_polars(returns_pl)
    csr_q = qs.stats.common_sense_ratio(returns_pd)
    print(f"Common Sense Ratio: match={_close(csr_o, csr_q)} | ours={csr_o:.10f} qs={csr_q:.10f} | %diff={percent_diff(csr_o, csr_q):.4f}%")
    cpc_o = cpc_index_polars(returns_pl)
    cpc_q = qs.stats.cpc_index(returns_pd)
    print(f"CPC Index: match={_close(cpc_o, cpc_q)} | ours={cpc_o:.10f} qs={cpc_q:.10f} | %diff={percent_diff(cpc_o, cpc_q):.4f}%")
    tail_o = tail_ratio_polars(returns_pl)
    tail_q = qs.stats.tail_ratio(returns_pd)
    print(f"Tail Ratio: match={_close(tail_o, tail_q)} | ours={tail_o:.10f} qs={tail_q:.10f} | %diff={percent_diff(tail_o, tail_q):.4f}%")
    outlier_win_o = outlier_win_ratio_polars(returns_pl)
    outlier_win_q = qs.stats.outlier_win_ratio(returns_pd)
    print(f"Outlier Win Ratio: match={_close(outlier_win_o, outlier_win_q)} | ours={outlier_win_o:.10f} qs={outlier_win_q:.10f} | %diff={percent_diff(outlier_win_o, outlier_win_q):.4f}%")
    outlier_loss_o = outlier_loss_ratio_polars(returns_pl)
    outlier_loss_q = qs.stats.outlier_loss_ratio(returns_pd)
    print(f"Outlier Loss Ratio: match={_close(outlier_loss_o, outlier_loss_q)} | ours={outlier_loss_o:.10f} qs={outlier_loss_q:.10f} | %diff={percent_diff(outlier_loss_o, outlier_loss_q):.4f}%")
    cons_wins_o = consecutive_wins_polars(returns_pl)
    cons_wins_q = qs.stats.consecutive_wins(returns_pd)
    print(f"Max Consecutive Wins: match={_close(cons_wins_o, cons_wins_q)} | ours={cons_wins_o} qs={cons_wins_q} | diff={cons_wins_o - cons_wins_q}")
    cons_losses_o = consecutive_losses_polars(returns_pl)
    cons_losses_q = qs.stats.consecutive_losses(returns_pd)
    print(f"Max Consecutive Losses: match={_close(cons_losses_o, cons_losses_q)} | ours={cons_losses_o} qs={cons_losses_q} | diff={cons_losses_o - cons_losses_q}")

def check_period_metrics(returns_pl: pl.DataFrame, returns_pd: pd.Series, periods_per_year: int = 252):
    print("\n— Period-Based Metrics —")
    last_date = returns_pd.index[-1]
    last_year = last_date.year
    last_month = last_date.month
    return_col = _find_return_col_in_pl(returns_pl)

    # MTD
    mtd_mask = (returns_pd.index.month == last_month) & (returns_pd.index.year == last_year) & (returns_pd.index <= last_date)
    mtd_o = comp_polars(returns_pl.filter((pl.col("date").dt.month() == last_month) & (pl.col("date").dt.year() == last_year) & (pl.col("date") <= last_date))[return_col])
    mtd_q = qs.stats.comp(returns_pd[mtd_mask])
    print(f"MTD: match={_close(mtd_o, mtd_q)} | ours={mtd_o:.10f} qs={mtd_q:.10f} | %diff={percent_diff(mtd_o, mtd_q):.4f}%")

    # 3M
    m3 = last_date - relativedelta(months=3)
    three_m_o = comp_polars(returns_pl.filter(pl.col("date") >= m3)[return_col])
    three_m_q = qs.stats.comp(returns_pd[returns_pd.index >= m3])
    print(f"3M: match={_close(three_m_o, three_m_q)} | ours={three_m_o:.10f} qs={three_m_q:.10f} | %diff={percent_diff(three_m_o, three_m_q):.4f}%")

    # 6M
    m6 = last_date - relativedelta(months=6)
    six_m_o = comp_polars(returns_pl.filter(pl.col("date") >= m6)[return_col])
    six_m_q = qs.stats.comp(returns_pd[returns_pd.index >= m6])
    print(f"6M: match={_close(six_m_o, six_m_q)} | ours={six_m_o:.10f} qs={six_m_q:.10f} | %diff={percent_diff(six_m_o, six_m_q):.4f}%")

    # YTD
    ytd_start = datetime(last_year, 1, 1)
    ytd_o = comp_polars(returns_pl.filter(pl.col("date") >= ytd_start)[return_col])
    ytd_q = qs.stats.comp(returns_pd[returns_pd.index.year == last_year])
    print(f"YTD: match={_close(ytd_o, ytd_q)} | ours={ytd_o:.10f} qs={ytd_q:.10f} | %diff={percent_diff(ytd_o, ytd_q):.4f}%")

    # 1Y
    y1 = last_date - relativedelta(years=1)
    one_y_o = comp_polars(returns_pl.filter(pl.col("date") >= y1)[return_col])
    one_y_q = qs.stats.comp(returns_pd[returns_pd.index >= y1])
    print(f"1Y: match={_close(one_y_o, one_y_q)} | ours={one_y_o:.10f} qs={one_y_q:.10f} | %diff={percent_diff(one_y_o, one_y_q):.4f}%")

    # 3Y ann.
    y3 = last_date - relativedelta(years=3)
    three_y_ann_o = cagr_polars(returns_pl.filter(pl.col("date") >= y3)[return_col], periods_per_year)
    three_y_ann_q = qs.stats.cagr(returns_pd[returns_pd.index >= y3])
    print(f"3Y (ann.): match={_close(three_y_ann_o, three_y_ann_q)} | ours={three_y_ann_o:.10f} qs={three_y_ann_q:.10f} | %diff={percent_diff(three_y_ann_o, three_y_ann_q):.4f}%")

    # 5Y ann.
    y5 = last_date - relativedelta(years=5)
    five_y_ann_o = cagr_polars(returns_pl.filter(pl.col("date") >= y5)[return_col], periods_per_year)
    five_y_ann_q = qs.stats.cagr(returns_pd[returns_pd.index >= y5])
    print(f"5Y (ann.): match={_close(five_y_ann_o, five_y_ann_q)} | ours={five_y_ann_o:.10f} qs={five_y_ann_q:.10f} | %diff={percent_diff(five_y_ann_o, five_y_ann_q):.4f}%")

    # 10Y ann.
    y10 = last_date - relativedelta(years=10)
    ten_y_ann_o = cagr_polars(returns_pl.filter(pl.col("date") >= y10)[return_col], periods_per_year) if len(returns_pl.filter(pl.col("date") >= y10)) > 0 else np.nan
    ten_y_ann_q = qs.stats.cagr(returns_pd[returns_pd.index >= y10]) if len(returns_pd[returns_pd.index >= y10]) > 0 else np.nan
    print(f"10Y (ann.): match={_close(ten_y_ann_o, ten_y_ann_q)} | ours={ten_y_ann_o:.10f} qs={ten_y_ann_q:.10f} | %diff={percent_diff(ten_y_ann_o, ten_y_ann_q):.4f}%")

    # All-time ann.
    all_time_ann_o = cagr_polars(returns_pl[return_col], periods_per_year)
    all_time_ann_q = qs.stats.cagr(returns_pd)
    print(f"All-time (ann.): match={_close(all_time_ann_o, all_time_ann_q)} | ours={all_time_ann_o:.10f} qs={all_time_ann_q:.10f} | %diff={percent_diff(all_time_ann_o, all_time_ann_q):.4f}%")

def check_monthly_returns(returns_pl: pl.DataFrame, returns_pd: pd.Series):
    """
    Validate monthly returns table.
    """
    print("\n— Monthly Returns —")
    monthly_o_pl = monthly_returns_polars(returns_pl, eoy=True, compounded=True)
    monthly_o = monthly_o_pl.to_pandas().set_index('Year').fillna(0.0)
    monthly_q = qs.stats.monthly_returns(returns_pd)
    all_close_monthly = np.allclose(monthly_o.values, monthly_q.values, atol=1e-10, equal_nan=True)
    max_diff_monthly = np.max(np.abs(monthly_o.values - monthly_q.values)) if not all_close_monthly else 0.0
    print(f"Monthly Returns: match={all_close_monthly} | shape={monthly_o.shape} | max abs diff={max_diff_monthly:.10f}")

def check_benchmark_metrics(returns_pl: pl.DataFrame, returns_pd: pd.Series, benchmark_pl: pl.DataFrame, benchmark_pd: pd.Series, periods_per_year: int = 252):
    """
    Validate benchmark-related metrics (R², Information Ratio, Greeks, Rolling Greeks, Compare).
    """
    print("\n— Benchmark-Related Metrics —")
    
    r2_o = r_squared_polars(returns_pl, benchmark_pl)
    r2_q = qs.stats.r_squared(returns_pd, benchmark_pd)
    print(f"R²: match={_close(r2_o, r2_q)} | ours={r2_o:.10f} qs={r2_q:.10f} | %diff={percent_diff(r2_o, r2_q):.4f}%")

    info_o = information_ratio_polars(returns_pl, benchmark_pl, annualize=False)
    info_q = qs.stats.information_ratio(returns_pd, benchmark_pd)
    print(f"Information Ratio: match={_close(info_o, info_q)} | ours={info_o:.10f} qs={info_q:.10f} | %diff={percent_diff(info_o, info_q):.4f}%")

    greeks_o = greeks_polars(returns_pl["r"], benchmark_pl["r"], periods=periods_per_year)#.to_dict(as_series=False)
    greeks_q = qs.stats.greeks(returns_pd, benchmark_pd, periods=periods_per_year).to_dict()
    alpha_o = greeks_o['alpha'][0]
    beta_o = greeks_o['beta'][0]
    alpha_q = greeks_q['alpha']
    beta_q = greeks_q['beta']
    print(f"Greeks Alpha: match={_close(alpha_o, alpha_q)} | ours={alpha_o:.10f} qs={alpha_q:.10f} | %diff={percent_diff(alpha_o, alpha_q):.4f}%")
    print(f"Greeks Beta: match={_close(beta_o, beta_q)} | ours={beta_o:.10f} qs={beta_q:.10f} | %diff={percent_diff(beta_o, beta_q):.4f}%")

    rolling_greeks_o = rolling_greeks_polars(returns_pl, benchmark_pl)
    rolling_greeks_q = qs.stats.rolling_greeks(returns_pd, benchmark_pd)
    o_np = rolling_greeks_o.drop('date').to_numpy()
    
    q_np = rolling_greeks_q.dropna().values
    all_close_rolling = np.allclose(o_np, q_np, atol=1e-10, equal_nan=True)
    max_diff_rolling = np.max(np.abs(o_np - q_np)) if not all_close_rolling else 0.0
    print(f"Rolling Greeks: match={all_close_rolling} | shape={o_np.shape} | max abs diff={max_diff_rolling:.10f}")

    compare_o = compare_polars(returns_pl, benchmark_pl).to_pandas().set_index('date')
    compare_q = qs.stats.compare(returns_pd, benchmark_pd)
    compare_q.index.name = 'date'
    all_close_compare = np.allclose(compare_o.iloc[:, :-1].values, compare_q.iloc[:, :-1].values, atol=1e-10, equal_nan=True)
    max_diff_compare = np.max(np.abs(compare_o.iloc[:, :-1].values - compare_q.iloc[:, :-1].values)) if not all_close_compare else 0.0
    print(f"Compare (Numerical Col): match={all_close_compare} | shape={compare_o.iloc[:, :-1].shape}| max abs diff={max_diff_compare:.10f}")
    string_compare = np.allclose(pd.get_dummies(compare_o.iloc[:, -1]), pd.get_dummies(compare_q.iloc[:, -1]), atol=1e-10, equal_nan=True)
    max_diff_compare = np.max(np.abs(compare_o.iloc[:, :-1].values - compare_q.iloc[:, :-1].values)) if not all_close_compare else 0.0
    print(f"Compare (String Col): match={string_compare } | shape={compare_o.iloc[:, -1].shape}| max abs diff={max_diff_compare:.10f}")
    

def check_additional_metrics(returns_pd: pd.Series, benchmark_pd: pd.Series = None, periods_per_year: int = 252, rf: float = 0.0):
    """
    Validate all additional metrics by calling specific group validation functions.
    """
    # Convert to Polars
    # Prepare Polars versions with fix
    returns_pl = to_pl_returns_df(returns_pd)
    if benchmark_pd is not None:
        benchmark_pl = to_pl_returns_df(benchmark_pd)

    # Validate statistical metrics
    check_statistical_metrics(returns_pl, returns_pd)

    # Validate risk metrics
    check_risk_metrics(returns_pl, returns_pd, rf)

    # Validate trading metrics
    check_trading_metrics(returns_pl, returns_pd, rf)

    # Validate period-based metrics
    check_period_metrics(returns_pl, returns_pd, periods_per_year)

    # Validate benchmark-related metrics if benchmark is provided
    # if benchmark_pd is not None and benchmark_pl is not None:
    if benchmark_pd is not None:
        check_benchmark_metrics(returns_pl, returns_pd, benchmark_pl, benchmark_pd, periods_per_year)

    # Validate monthly returns
    check_monthly_returns(returns_pl, returns_pd)

def parse_qs_metric(val):
    if pd.isna(val):
        return np.nan
    s = str(val).replace(',', '').replace('%', '')
    try:
        f = float(s)
    except ValueError:
        return np.nan
    return f /100 if '%' in str(val) else f

def detailed_metrics_compare(qs_df, pol_df, label=""):
    print(f"\n— Detailed Metrics Comparison {label} —")
    metrics_list = qs_df.index
    columns = qs_df.columns
    for col in columns:
        print(f"\nColumn: {col}")
        for metric in metrics_list:
            if metric not in pol_df.index:
                print(f"{metric}: skipped (not in polars df)")
                continue
            qs_val_str = qs_df.loc[metric, col]
            pol_val = pol_df.loc[metric, col] if col in pol_df.columns else np.nan
            qs_val = parse_qs_metric(qs_val_str)
            pol_val_parsed = parse_qs_metric(pol_val) if isinstance(pol_val, str) else pol_val
            match = _close(qs_val, pol_val_parsed)
            print(f"{metric}: match={match} | qs={qs_val:.10f} ({qs_val_str}) pol={pol_val_parsed:.10f} ({pol_val}) | %diff={percent_diff(qs_val, pol_val_parsed):.4f}%")

def run_all_metric_validations(seeds=[42], periods=10000):
    current_date = datetime(2025, 10, 12)
    for seed in seeds:
        np.random.seed(seed)
        dates = pd.date_range('2020-01-01', periods=periods)
        mask = dates <= pd.to_datetime(current_date)
        dates = dates[mask]
        returns1 = pd.Series(np.random.normal(0.001, 0.02, len(dates)), index=dates, name='returns')
        benchmark1 = pd.Series(np.random.normal(0.0005, 0.01, len(dates)), index=dates, name='benchmark')
        print(f"\nSeed {seed} — Metrics (Single):")
        check_drawdown_based_metrics(returns1)
        check_sharpe_based_metrics(returns1)
        check_additional_metrics(returns1, benchmark1)

        # qs_df_basic = qs.reports.metrics(returns1, benchmark=benchmark1, display=False, mode="basic")
        # returns1_pl = to_pl_returns_df(returns1)
        # benchmark1_pl =  to_pl_returns_df(benchmark1, value_col='benchmark')
        
        # pol_df_basic = metrics_polars(returns1_pl, benchmark=benchmark1_pl, display=False, mode="basic")
        # idx = qs_df_basic.index
        # # print(qs_df_basic, '\n',pol_df_basic)
        # try:
        #     # align rows/cols, coerce any string/non-numeric -> numeric (using parse_qs_metric)
        #     pol_sel = pol_df_basic.reindex(index=idx, columns=qs_df_basic.columns)
        #     q_num = qs_df_basic.applymap(parse_qs_metric).astype(float)
        #     p_num = pol_sel.applymap(parse_qs_metric).astype(float)
        #     basic_match = np.allclose(q_num.values, p_num.values, atol=1e-6, equal_nan=True)
        # except Exception as e:
        #     basic_match = False
        #     print("basic_match comparison failed:", e)
        # print("Basic metrics match: ", basic_match)
        # # if not basic_match:
        # #     print("Mismatches in basic:", qs_df_basic.compare(pol_df_basic))
        # detailed_metrics_compare(qs_df_basic, pol_df_basic, "Basic Single")

        # qs_df_full = qs.reports.metrics(returns1, benchmark=benchmark1, display=False, mode="full")
        # pol_df_full = metrics_polars(returns1_pl, benchmark=benchmark1_pl, display=False, mode="full")
        # idx = qs_df_full.index
        # # print(qs_df_basic, '\n',pol_df_basic)
        # try:
        #     # align rows/cols, coerce any string/non-numeric -> numeric (using parse_qs_metric)
        #     pol_sel = pol_df_full.reindex(index=idx, columns=qs_df_basic.columns)
        #     q_num = qs_df_full.applymap(parse_qs_metric).astype(float)
        #     p_num = pol_sel.applymap(parse_qs_metric).astype(float)
        #     full_match = np.allclose(q_num.values, p_num.values, atol=1e-6, equal_nan=True)
        # except Exception as e:
        #     full_match = False
        #     print("full_match comparison failed:", e)
        
        # if not full_match:
        #     print("Mismatches in full:", qs_df_full.compare(pol_df_full))
        # detailed_metrics_compare(qs_df_full, pol_df_full, "Full Single")

        # returns2 = pd.Series(np.random.normal(0.002, 0.015, len(dates)), index=dates, name='returns2')
        # multi_df = pd.concat([returns1.rename('returns1'), returns2], axis=1)
        # multi_df_pl = to_pl_returns_df(multi_df)
        # print(f"\nSeed {seed} — Metrics (Multi):")
        # for col in multi_df.columns:
        #     print(f"[{col}]")
        #     check_drawdown_based_metrics(multi_df[col])
        #     check_sharpe_based_metrics(multi_df[col])
        #     check_additional_metrics(multi_df[col],benchmark1)

        # # --- Multi: BASIC ---
        # qs_multi_basic = qs.reports.metrics(multi_df, benchmark=benchmark1, display=False, mode="basic")
        # pol_multi_basic = metrics_polars(multi_df_pl, benchmark=benchmark1_pl, display=False, mode="basic")

        # idx = qs_multi_basic.index
        # try:
        #     # align rows/cols, coerce to numeric (strip %, commas, etc.)
        #     pol_sel = pol_multi_basic.reindex(index=idx, columns=qs_multi_basic.columns)
        #     q_num = qs_multi_basic.applymap(parse_qs_metric).astype(float)
        #     p_num = pol_sel.applymap(parse_qs_metric).astype(float)
        #     multi_basic_match = np.allclose(q_num.values, p_num.values, atol=1e-6, equal_nan=True)
        # except Exception as e:
        #     multi_basic_match = False
        #     print("multi_basic_match comparison failed:", e)

        # print("Multi Basic metrics match: ", multi_basic_match)
        # detailed_metrics_compare(qs_multi_basic, pol_multi_basic, "Basic Multi")

        # # --- Multi: FULL ---
        # qs_multi_full = qs.reports.metrics(multi_df, benchmark=benchmark1, display=False, mode="full")
        # pol_multi_full = metrics_polars(multi_df_pl, benchmark=benchmark1, display=False, mode="full")

        # idx = qs_multi_full.index
        # try:
        #     # align rows/cols, coerce to numeric (strip %, commas, etc.)
        #     pol_sel = pol_multi_full.reindex(index=idx, columns=qs_multi_full.columns)
        #     q_num = qs_multi_full.applymap(parse_qs_metric).astype(float)
        #     p_num = pol_sel.applymap(parse_qs_metric).astype(float)
        #     multi_full_match = np.allclose(q_num.values, p_num.values, atol=1e-6, equal_nan=True)
        # except Exception as e:
        #     multi_full_match = False
        #     print("multi_full_match comparison failed:", e)

        # print("Multi Full metrics match: ", multi_full_match)
        # detailed_metrics_compare(qs_multi_full, pol_multi_full, "Full Multi")

        returns_edge = returns1.copy()
        returns_edge_pl = to_pl_returns_df(returns_edge)
        returns_edge.iloc[0] = -0.05
        print(f"\nSeed {seed} — Metrics (Single Edge):")
        check_drawdown_based_metrics(returns_edge)
        check_sharpe_based_metrics(returns_edge)
        check_additional_metrics(returns_edge)

        # # --- Edge: BASIC ---
        # qs_edge_basic = qs.reports.metrics(returns_edge, benchmark=benchmark1, display=False, mode="basic")
        # pol_edge_basic = metrics_polars(returns_edge_pl, benchmark=benchmark1_pl, display=False, mode="basic")
        # idx = qs_edge_basic.index
        # try:
        #     pol_sel = pol_edge_basic.reindex(index=idx, columns=qs_edge_basic.columns)
        #     q_num = qs_edge_basic.map(parse_qs_metric).astype(float)
        #     p_num = pol_sel.map(parse_qs_metric).astype(float)
        #     edge_basic_match = np.allclose(q_num.values, p_num.values, atol=1e-6, equal_nan=True)
        # except Exception as e:
        #     edge_basic_match = False
        #     print("edge_basic_match comparison failed:", e)
        # print("Edge Basic metrics match: ", edge_basic_match)
        # detailed_metrics_compare(qs_edge_basic, pol_sel if 'pol_sel' in locals() else pol_edge_basic, "Basic Edge")

        # # --- Edge: FULL ---
        # qs_edge_full = qs.reports.metrics(returns_edge, benchmark=benchmark1, display=False, mode="full")
        # pol_edge_full = metrics_polars(returns_edge_pl, benchmark=benchmark1_pl, display=False, mode="full")
        # print(qs_edge_full, pol_edge_full)
        # idx = qs_edge_full.index
        # try:
        #     pol_sel = pol_edge_full.reindex(index=idx, columns=qs_edge_full.columns)
        #     q_num = qs_edge_full.map(parse_qs_metric).astype(float)
        #     p_num = pol_sel.map(parse_qs_metric).astype(float)
        #     edge_full_match = np.allclose(q_num.values, p_num.values, atol=1e-6, equal_nan=True)
        # except Exception as e:
        #     edge_full_match = False
        #     print("edge_full_match comparison failed:", e)
        # print("Edge Full metrics match: ", edge_full_match)
        # detailed_metrics_compare(qs_edge_full, pol_sel if 'pol_sel' in locals() else pol_edge_full, "Full Edge")

        no_dd = pd.Series(np.full(len(dates), 0.01), index=dates, name='returns')
        no_dd_pl = to_pl_returns_df(no_dd)
        print(f"\nSeed {seed} — Metrics (No DD):")
        check_drawdown_based_metrics(no_dd)
        check_sharpe_based_metrics(no_dd)
        check_additional_metrics(no_dd)

        # # --- NoDD: BASIC ---
        # qs_nodd_basic = qs.reports.metrics(no_dd, benchmark=benchmark1, display=False, mode="basic")
        # pol_nodd_basic = metrics_polars(no_dd_pl, benchmark=benchmark1_pl, display=False, mode="basic")
        # idx = qs_nodd_basic.index
        # try:
        #     pol_sel = pol_nodd_basic.reindex(index=idx, columns=qs_nodd_basic.columns)
        #     q_num = qs_nodd_basic.map(parse_qs_metric).astype(float)
        #     p_num = pol_sel.map(parse_qs_metric).astype(float)
        #     nodd_basic_match = np.allclose(q_num.values, p_num.values, atol=1e-6, equal_nan=True)
        # except Exception as e:
        #     nodd_basic_match = False
        #     print("nodd_basic_match comparison failed:", e)
        # print("NoDD Basic metrics match: ", nodd_basic_match)
        # detailed_metrics_compare(qs_nodd_basic, pol_sel if 'pol_sel' in locals() else pol_nodd_basic, "Basic NoDD")

        # # --- NoDD: FULL (robust to QS linregress crash on constant series) ---
        # try:
        #     qs_nodd_full = qs.reports.metrics(no_dd, benchmark=benchmark1, display=False, mode="full")
        #     pol_nodd_full = metrics_polars(no_dd, benchmark=benchmark1, display=False, mode="full")
        #     idx = qs_nodd_full.index
        #     try:
        #         pol_sel = pol_nodd_full.reindex(index=idx, columns=qs_nodd_full.columns)
        #         q_num = qs_nodd_full.map(parse_qs_metric).astype(float)
        #         p_num = pol_sel.map(parse_qs_metric).astype(float)
        #         nodd_full_match = np.allclose(q_num.values, p_num.values, atol=1e-6, equal_nan=True)
        #     except Exception as e:
        #         nodd_full_match = False
        #         print("nodd_full_match comparison failed:", e)
        #     print("NoDD Full metrics match: ", nodd_full_match)
        #     detailed_metrics_compare(qs_nodd_full, pol_sel if 'pol_sel' in locals() else pol_nodd_full, "Full NoDD")
        # except ValueError as e:
        #     # QS fails when linregress sees identical x-values; fall back to comparing overlap-only rows
        #     print("qs_nodd_full failed:", e)
        #     pol_nodd_full = metrics_polars(no_dd, benchmark=benchmark1, display=False, mode="full")
        #     qs_nodd_basic_for_overlap = qs.reports.metrics(no_dd, benchmark=benchmark1, display=False, mode="basic")
        #     idx = qs_nodd_basic_for_overlap.index
        #     try:
        #         pol_sel = pol_nodd_full.reindex(index=idx, columns=qs_nodd_basic_for_overlap.columns)
        #         q_num = qs_nodd_basic_for_overlap.map(parse_qs_metric).astype(float)
        #         p_num = pol_sel.map(parse_qs_metric).astype(float)
        #         nodd_full_match = np.allclose(q_num.values, p_num.values, atol=1e-6, equal_nan=True)
        #     except Exception as e2:
        #         nodd_full_match = False
        #         print("nodd_full_match (fallback) comparison failed:", e2)
        #     print("NoDD Full metrics match: ", nodd_full_match)
        #     detailed_metrics_compare(qs_nodd_basic_for_overlap, pol_sel if 'pol_sel' in locals() else pol_nodd_full, "Full NoDD (overlap only)")
# Run the expanded validation
# run_validations()
# NEW: run the metric parity validations (added)
run_all_metric_validations()