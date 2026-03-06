# backend/compute.py

import numpy as np
import pandas as pd
import streamlit as st
from statsmodels.tsa.stattools import acf, pacf
from config import FACTORS, TRADING_DAYS_PER_YEAR

@st.cache_data
def build_master_df(df_returns: pd.DataFrame,
                    df_loadings: pd.DataFrame) -> pd.DataFrame:
    """
    Computes systematic and idiosyncratic returns via dot product.
    """
    exp_cols = [f"exp_{f}" for f in FACTORS if f"exp_{f}" in df_loadings.columns]
    ret_cols = [f"ret_{f}" for f in FACTORS if f"ret_{f}" in df_returns.columns]

    # Align columns — use only factors present in both files
    common_factors = [f for f in FACTORS
                      if f"exp_{f}" in df_loadings.columns
                      and f"ret_{f}" in df_returns.columns]

    exp_cols = [f"exp_{f}" for f in common_factors]
    ret_cols = [f"ret_{f}" for f in common_factors]

    exposures = df_loadings[exp_cols].values
    fac_rets  = df_returns[ret_cols].values

    df = pd.DataFrame(index=df_returns.index)
    df["nvda_return"]        = df_returns["nvda_return"]
    df["systematic_return"]  = np.einsum("ij,ij->i", exposures, fac_rets)
    df["idio_return"]        = df["nvda_return"] - df["systematic_return"]

    return df


def compute_summary_stats(df: pd.DataFrame,
                          earnings_dates: list,
                          day_n: int = 1) -> pd.DataFrame:
    """
    Returns a styled summary DataFrame with 5 rows x 3 cols.
    Columns: Total, Systematic, Idiosyncratic
    """
    ann  = TRADING_DAYS_PER_YEAR
    cols = {
        "Total"         : "nvda_return",
        "Systematic"    : "systematic_return",
        "Idiosyncratic" : "idio_return"
    }

    results = {}
    for label, col in cols.items():
        r = df[col].dropna()

        # Equity curve (compounded)
        equity  = (1 + r).cumprod()
        n_years = len(r) / ann

        # CAGR
        cagr = (equity.iloc[-1] ** (1 / n_years) - 1) * 100

        # Avg daily return
        avg_ret = r.mean() * 100
        sum_ret = r.sum() * 100

        # Annualized volatility
        ann_vol = r.std() * np.sqrt(ann) * 100

        # Max drawdown
        roll_max = equity.cummax()
        drawdown = (equity - roll_max) / roll_max
        max_dd   = drawdown.min() * 100

        # Sum of Day+N returns around earnings
        day_n_sum = _sum_day_n_returns(df, col, earnings_dates, day_n)

        results[label] = {
            "CAGR (%)"                    : f"{cagr:.1f}%",
            "Ann. Volatility (%)"          : f"{ann_vol:.1f}%",
            "Max Drawdown (%)"             : f"{max_dd:.1f}%",
            "Sum of Daily Returns (%)"         : f"{sum_ret:.3f}%",
            "Sum of D+1 Returns (%)" : f"{day_n_sum:.2f}%",
        }

    summary_df = pd.DataFrame(results)
    summary_df = summary_df.dropna(how="all")
    #print(summary_df)
    #print(summary_df.index.tolist())
    return summary_df


def _sum_day_n_returns(df: pd.DataFrame,
                       col: str,
                       earnings_dates: list,
                       n: int) -> float:
    """
    For each earnings date, finds the Nth trading day after it
    and sums those returns across all events.
    """
    trading_days = df.index.tolist()
    total = 0.0

    for ed in earnings_dates:
        ed = pd.Timestamp(ed)
        # Find position of first trading day on or after earnings date
        future = [d for d in trading_days if d > ed]
        if len(future) >= n:
            target_date = future[n - 1]
            total += df.loc[target_date, col]

    return total * 100

# backend/compute.py — add this helper
def build_drilldown_data(df: pd.DataFrame) -> dict:
    """
    Returns a dict of year -> {total, systematic, idio} 
    and year -> quarter -> {total, systematic, idio}
    """
    result = {}
    for y in sorted(df.index.year.unique()):
        y_mask  = df.index.year == y
        y_slice = df[y_mask]
        result[y] = {
            "total" : round(y_slice["nvda_return"].sum() * 100, 1),
            "sys"   : round(y_slice["systematic_return"].sum() * 100, 1),
            "idio"  : round(y_slice["idio_return"].sum() * 100, 1),
            "quarters": {}
        }
        for q in [1, 2, 3, 4]:
            q_mask  = y_mask & (df.index.quarter == q)
            q_slice = df[q_mask]
            if q_slice.empty:
                continue
            result[y]["quarters"][f"Q{q}"] = {
                "total" : round(q_slice["nvda_return"].sum() * 100, 1),
                "sys"   : round(q_slice["systematic_return"].sum() * 100, 1),
                "idio"  : round(q_slice["idio_return"].sum() * 100, 1),
            }
    return result

def build_factor_contributions(
    df_returns: pd.DataFrame,
    df_loadings: pd.DataFrame,
) -> pd.DataFrame:
    """
    Returns a DataFrame of shape (n_days, 16):
    one column per factor (exposure × factor_return) + idio_return.
    """
    common_factors = [f for f in FACTORS
                      if f"exp_{f}" in df_loadings.columns
                      and f"ret_{f}" in df_returns.columns]

    contrib = pd.DataFrame(index=df_returns.index)
    for f in common_factors:
        contrib[f] = df_loadings[f"exp_{f}"] * df_returns[f"ret_{f}"]

    # Idiosyncratic = total - systematic
    systematic = contrib.sum(axis=1)
    contrib["Idiosyncratic"] = df_returns["nvda_return"] - systematic

    return contrib

SNAPSHOTS_PRE  = [-20, -10, -5, -3, -1, 0]
SNAPSHOTS_POST = [1, 3, 5, 10, 20]

def _quarter_label(dt: pd.Timestamp) -> str:
    q = (dt.month - 1) // 3 + 1
    return f"{dt.year} Q{q}"

@st.cache_data
def build_earnings_factor_decomp(
    df_returns: pd.DataFrame,
    df_loadings: pd.DataFrame,
    earnings_dates: list,
    pre_window: int = 20,
    post_window: int = 20,
) -> dict:
    """
    For each earnings event, computes cumulative factor contributions
    at snapshot points pre/post D0.

    Returns:
        per_event : {quarter_label: DataFrame(index=factors, columns=snap_labels)}
        average   : DataFrame(index=factors, columns=snap_labels)
        snap_labels: list of column label strings
    """
    common_factors = [f for f in FACTORS
                      if f"exp_{f}" in df_loadings.columns
                      and f"ret_{f}" in df_returns.columns]
    all_factors = common_factors + ["Idiosyncratic", "NVDA Total"]
    trading_days = df_returns.index

    # Filter snapshots to within requested window
    snaps_pre  = [d for d in SNAPSHOTS_PRE  if d >= -pre_window]
    snaps_post = [d for d in SNAPSHOTS_POST if d <=  post_window]
    all_snaps  = snaps_pre + snaps_post

    def _label(d):
        if d < 0:  return f"D{d}"
        if d == 0: return "D0"
        return f"D+{d}"

    snap_labels = [_label(d) for d in all_snaps]

    per_event = {}

    for ed in earnings_dates:
        ed_ts = pd.Timestamp(ed)
        if ed_ts not in trading_days:
            continue

        d0_idx = trading_days.get_loc(ed_ts)
        label  = _quarter_label(ed_ts)

        event_cols = {}

        for snap, slabel in zip(all_snaps, snap_labels):
            snap_idx = d0_idx + snap
        
            if snap_idx < 0 or snap_idx >= len(trading_days):
                event_cols[slabel] = pd.Series(0.0, index=all_factors)
                continue
        
            if snap < 0:
                # ── Pre-earnings: from snap → D0 ──────────────────
                slice_start = trading_days[snap_idx]
                slice_end   = trading_days[d0_idx]
        
            elif snap == 0:
                # ── D0 alone ──────────────────────────────────────
                slice_start = trading_days[d0_idx]
                slice_end   = trading_days[d0_idx]
        
            else:
                # ── Post-earnings: D+1 → snap (unchanged) ─────────
                post_start_idx = d0_idx + 1
                if post_start_idx >= len(trading_days):
                    event_cols[slabel] = pd.Series(0.0, index=all_factors)
                    continue
                slice_start = trading_days[post_start_idx]
                slice_end   = trading_days[snap_idx]
        
            mask = (df_returns.index >= slice_start) & (df_returns.index <= slice_end)
        
            row = {}
            for f in common_factors:
                row[f] = (
                    df_loadings.loc[mask, f"exp_{f}"] *
                    df_returns.loc[mask,  f"ret_{f}"]
                ).sum()
        
            systematic           = sum(row.values())
            nvda_total           = df_returns.loc[mask, "nvda_return"].sum()
            row["Idiosyncratic"] = nvda_total - systematic
            row["NVDA Total"]    = nvda_total
        
            event_cols[slabel] = pd.Series(row) * 100

        per_event[label] = pd.DataFrame(event_cols)    # (factors × snaps)

    # Average across all events
    if per_event:
        stacked = pd.concat(per_event.values(), keys=per_event.keys())
        average = stacked.groupby(level=1).mean().reindex(all_factors)
    else:
        average = pd.DataFrame(index=all_factors, columns=snap_labels)

    return {
        "per_event"  : per_event,
        "average"    : average,
        "snap_labels": snap_labels,
        "all_snaps"  : all_snaps,
    }

@st.cache_data
def build_car_heatmap(
    df_returns: pd.DataFrame,
    df_loadings: pd.DataFrame,
    earnings_dates: list,
    pre_window: int = 20,
    post_window: int = 20,
) -> dict:

    common_factors = [f for f in FACTORS
                      if f"exp_{f}" in df_loadings.columns
                      and f"ret_{f}" in df_returns.columns]
    trading_days = df_returns.index

    snaps_pre  = [d for d in SNAPSHOTS_PRE  if d >= -pre_window]
    snaps_post = [d for d in SNAPSHOTS_POST if d <=  post_window]
    all_snaps  = snaps_pre + snaps_post

    def _label(d):
        if d < 0:  return f"D{d}"
        if d == 0: return "D0"
        return f"D+{d}"

    snap_labels = [_label(d) for d in all_snaps]

    rows   = []
    z_data = []

    for ed in sorted(earnings_dates, reverse=True):
        ed_ts = pd.Timestamp(ed)
        if ed_ts not in trading_days:
            continue

        d0_idx = trading_days.get_loc(ed_ts)
        label  = _quarter_label(ed_ts)

        row_vals = []
        for snap in all_snaps:
            snap_idx = d0_idx + snap
            if snap_idx < 0 or snap_idx >= len(trading_days):
                row_vals.append(None)
                continue
        
            if snap < 0:
                # ── Pre-earnings: CAR from snap day → D0 ──────────
                slice_start = trading_days[snap_idx]      # e.g. D-5
                slice_end   = trading_days[d0_idx]        # always D0
        
            elif snap == 0:
                # ── D0 alone ──────────────────────────────────────
                slice_start = trading_days[d0_idx]
                slice_end   = trading_days[d0_idx]
        
            else:
                # ── Post-earnings: CAR from D+1 → snap ────────────
                post_start_idx = d0_idx + 1
                if post_start_idx >= len(trading_days):
                    row_vals.append(None)
                    continue
                slice_start = trading_days[post_start_idx]
                slice_end   = trading_days[snap_idx]
        
            mask = (
                (df_returns.index >= slice_start) &
                (df_returns.index <= slice_end)
            )
            systematic = sum(
                (df_loadings.loc[mask, f"exp_{f}"] *
                 df_returns.loc[mask,  f"ret_{f}"]).sum()
                for f in common_factors
            )
            car = df_returns.loc[mask, "nvda_return"].sum() - systematic
            row_vals.append(round(car * 100, 2))

        rows.append(label)
        z_data.append(row_vals)

    return {
        "rows"       : rows,
        "snap_labels": snap_labels,
        "z"          : z_data,
    }

def build_car_lines(
    df_returns: pd.DataFrame,
    df_loadings: pd.DataFrame,
    earnings_dates: list,
    pre_window: int = 20,
    post_window: int = 20,
) -> dict:
    """
    Continuous CAR from D-20 to D+20, anchored at D-20.
    CAR(d) = sum of daily abnormal returns from D-20 to d inclusive.
    """
    common_factors = [f for f in FACTORS
                      if f"exp_{f}" in df_loadings.columns
                      and f"ret_{f}" in df_returns.columns]
    trading_days = df_returns.index
    day_offsets  = list(range(-pre_window, post_window + 1))  # -20 to +20

    per_event = {}   # { quarter_label: list of CAR values, one per day offset }

    for ed in earnings_dates:
        ed_ts = pd.Timestamp(ed)
        if ed_ts not in trading_days:
            continue

        d0_idx = trading_days.get_loc(ed_ts)
        label  = _quarter_label(ed_ts)

        daily_ar = []
        for offset in day_offsets:
            day_idx = d0_idx + offset
            if day_idx < 0 or day_idx >= len(trading_days):
                daily_ar.append(np.nan)
                continue

            day_date = trading_days[day_idx]
            systematic = sum(
                df_loadings.loc[day_date, f"exp_{f}"] *
                df_returns.loc[day_date,  f"ret_{f}"]
                for f in common_factors
                if day_date in df_loadings.index and day_date in df_returns.index
            )
            ar = df_returns.loc[day_date, "nvda_return"] - systematic
            daily_ar.append(ar)

        # Cumulative sum from D-20
        car_series = np.nancumsum(daily_ar) * 100
        per_event[label] = car_series.tolist()

    # Average across all events (element-wise, ignoring nan)
    matrix  = np.array(list(per_event.values()), dtype=float)
    average = np.nanmean(matrix, axis=0).tolist()

    return {
        "per_event"  : per_event,    # { label: [car_d-20, ..., car_d+20] }
        "average"    : average,       # [avg_car_d-20, ..., avg_car_d+20]
        "day_offsets": day_offsets,   # [-20, -19, ..., +20]
    }

def build_factor_daily_series(
    df_returns:     pd.DataFrame,
    df_loadings:    pd.DataFrame,
    earnings_dates: list,
    factor:         str,
    snap:           str,
    selected_event: str,
    pre_window:     int = 20,
    post_window:    int = 20,
) -> dict:
    """
    Returns daily (non-cumulative) factor contribution for each
    trading day in the window defined by snap, for the selected event.
    """
    from backend.compute import FACTORS, _quarter_label   # adjust import path if needed

    common_factors = [f for f in FACTORS
                      if f"exp_{f}" in df_loadings.columns
                      and f"ret_{f}" in df_returns.columns]
    trading_days = df_returns.index

    # Find D0 for the selected event
    d0_ts = None
    for ed in earnings_dates:
        ed_ts = pd.Timestamp(ed)
        if ed_ts in trading_days and _quarter_label(ed_ts) == selected_event:
            d0_ts = ed_ts
            break

    if d0_ts is None:
        return {"labels": [], "values": []}

    d0_idx = trading_days.get_loc(d0_ts)

    def _label(d):
        if d < 0:  return f"D{d}"
        if d == 0: return "D0"
        return f"D+{d}"

    snap_to_offset = {_label(d): d for d in
                      list(range(-pre_window, 0)) + [0] +
                      list(range(1, post_window + 1))}

    if snap not in snap_to_offset:
        return {"labels": [], "values": []}

    snap_offset = snap_to_offset[snap]

    # Define day range
    if snap_offset <= 0:
        day_range = range(snap_offset, 1)    # e.g. D-10 → range(-10, 1) = D-10 to D0
    else:
        day_range = range(1, snap_offset + 1)              # D+1 to snap

    labels = []
    values = []

    for offset in day_range:
        day_idx = d0_idx + offset
        if day_idx < 0 or day_idx >= len(trading_days):
            continue

        day_date = trading_days[day_idx]

        if factor == "Idiosyncratic":
            # Daily idiosyncratic = nvda_return - sum(factor contributions)
            systematic = sum(
                df_loadings.loc[day_date, f"exp_{f}"] *
                df_returns.loc[day_date,  f"ret_{f}"]
                for f in common_factors
                if day_date in df_loadings.index and day_date in df_returns.index
            )
            val = (df_returns.loc[day_date, "nvda_return"] - systematic) * 100
        elif factor == "NVDA Total":
            val = df_returns.loc[day_date, "nvda_return"] * 100
        else:
            if day_date not in df_loadings.index or day_date not in df_returns.index:
                continue
            val = (
                df_loadings.loc[day_date, f"exp_{factor}"] *
                df_returns.loc[day_date,  f"ret_{factor}"]
            ) * 100

        labels.append(day_date.strftime("%m/%d"))   # e.g. "11/17"
        values.append(round(val, 2))

    return {"labels": labels, "values": values}

# ── Predictability constants ───────────────────────────────────────
SCATTER_CAR_OFFSETS = [-20,-10,-5,-3,-1,0,1,3,5,10,20]
SCATTER_VOL_OFFSETS = [-20,-10,-5,5,10,20]

def _metric_label(kind: str, offset: int) -> str:
    sign = f"+{offset}" if offset > 0 else str(offset)
    return f"{'CAR' if kind == 'car' else 'Vol'}: D{sign}"

def _parse_metric_label(label: str) -> tuple:
    """'CAR: D+1' → ('car', 1),  'Vol: D-5' → ('vol', -5)"""
    kind_str, day_str = label.split(": D")
    return ("car" if kind_str == "CAR" else "vol"), int(day_str.replace("+", ""))

@st.cache_data
def build_scatter_data(
    df_returns: pd.DataFrame,
    df_loadings: pd.DataFrame,
    earnings_dates: list,
) -> dict:
    """
    For each earnings event computes CAR and Vol at all window boundaries.
    Returns:
        { quarter_label: { "car": {offset: {"total":..,"idio":..}},
                           "vol": {offset: {"total":..,"idio":..}} } }
    """
    common_factors = [f for f in FACTORS
                      if f"exp_{f}" in df_loadings.columns
                      and f"ret_{f}" in df_returns.columns]
    trading_days = df_returns.index
    result = {}

    for ed in earnings_dates:
        ed_ts = pd.Timestamp(ed)
        if ed_ts not in trading_days:
            continue

        d0_idx = trading_days.get_loc(ed_ts)
        label  = _quarter_label(ed_ts)
        car_vals, vol_vals = {}, {}

        for kind, offsets in [("car", SCATTER_CAR_OFFSETS), ("vol", SCATTER_VOL_OFFSETS)]:
            for offset in offsets:
                boundary_idx = d0_idx + offset
                if boundary_idx < 0 or boundary_idx >= len(trading_days):
                    (car_vals if kind == "car" else vol_vals)[offset] = None
                    continue

                if offset < 0:
                    slice_start = trading_days[boundary_idx]
                    slice_end   = trading_days[d0_idx]
                elif offset == 0:
                    slice_start = slice_end = trading_days[d0_idx]
                else:
                    post_start = d0_idx + 1
                    if post_start >= len(trading_days):
                        (car_vals if kind == "car" else vol_vals)[offset] = None
                        continue
                    slice_start = trading_days[post_start]
                    slice_end   = trading_days[boundary_idx]

                mask = (trading_days >= slice_start) & (trading_days <= slice_end)
                exp  = df_loadings.loc[mask, [f"exp_{f}" for f in common_factors]].values
                ret  = df_returns.loc[mask,  [f"ret_{f}" for f in common_factors]].values
                systematic_daily = (exp * ret).sum(axis=1)
                nvda_daily       = df_returns.loc[mask, "nvda_return"].values
                idio_daily       = nvda_daily - systematic_daily

                if kind == "car":
                    car_vals[offset] = {
                        "total": round(nvda_daily.sum()  * 100, 3),
                        "idio":  round(idio_daily.sum()  * 100, 3),
                    }
                else:
                    vol_vals[offset] = {
                        "total": round(nvda_daily.std()  * 100, 3),
                        "idio":  round(idio_daily.std()  * 100, 3),
                    }

        result[label] = {"car": car_vals, "vol": vol_vals}

    return result


def build_correlation_matrix(scatter_data: dict, series: str = "idio") -> dict:
    """
    Computes pairwise Pearson correlations between all 17 metrics
    across the 12 earnings events. Returns upper-triangular matrix.
    """
    metrics = (
        [("car", o) for o in SCATTER_CAR_OFFSETS] +
        [("vol", o) for o in SCATTER_VOL_OFFSETS]
    )
    labels = [_metric_label(k, o) for k, o in metrics]
    n      = len(metrics)

    # Build value vectors (12 values per metric)
    vectors = {}
    for kind, offset in metrics:
        lbl = _metric_label(kind, offset)
        vals = []
        for ev in scatter_data.values():
            src = ev[kind].get(offset)
            vals.append(src[series] if src is not None else np.nan)
        vectors[lbl] = np.array(vals, dtype=float)

    # Pearson correlation — upper triangle only
    z = np.full((n, n), np.nan)
    for i in range(n):
        for j in range(i, n):
            xi, xj = vectors[labels[i]], vectors[labels[j]]
            mask = ~(np.isnan(xi) | np.isnan(xj))
            if mask.sum() < 3:
                continue
            z[i, j] = 1.0 if i == j else round(np.corrcoef(xi[mask], xj[mask])[0, 1], 2)

    return {"z": z, "labels": labels, "metrics": metrics}

@st.cache_data
def build_rolling_vol(
    df_returns: pd.DataFrame,
    df_loadings: pd.DataFrame,
    earnings_dates: list,
    window: int = 20,
    series: str = "idio",   # "idio" or "total"
) -> dict:
    """
    Rolling annualised volatility + daily returns for dual-axis chart.
    Returns full period series.
    """
    from config import TRADING_DAYS_PER_YEAR
    common_factors = [f for f in FACTORS
                      if f"exp_{f}" in df_loadings.columns
                      and f"ret_{f}" in df_returns.columns]

    if series == "idio":
        exp = df_loadings[[f"exp_{f}" for f in common_factors]].values
        ret = df_returns[[f"ret_{f}" for f in common_factors]].values
        systematic  = pd.Series((exp * ret).sum(axis=1), index=df_returns.index)
        daily       = df_returns["nvda_return"] - systematic
    else:
        daily = df_returns["nvda_return"]

    rolling_vol = (
        daily.rolling(window).std() * np.sqrt(TRADING_DAYS_PER_YEAR) * 100
    )

    return {
        "dates"      : df_returns.index.tolist(),
        "daily"      : (daily * 100).tolist(),
        "rolling_vol": rolling_vol.tolist(),
        "earnings"   : [pd.Timestamp(e) for e in earnings_dates],
    }

def build_acf_pacf(
    df_returns: pd.DataFrame,
    df_loadings: pd.DataFrame,
    series: str = "idio",   # "idio" or "total"
    nlags: int = 20,
) -> dict:
    """
    Computes ACF and PACF of daily returns over full period.
    Returns values + confidence bands.
    """
    common_factors = [f for f in FACTORS
                      if f"exp_{f}" in df_loadings.columns
                      and f"ret_{f}" in df_returns.columns]

    if series == "idio":
        exp        = df_loadings[[f"exp_{f}" for f in common_factors]].values
        ret        = df_returns[[f"ret_{f}" for f in common_factors]].values
        systematic = pd.Series((exp * ret).sum(axis=1), index=df_returns.index)
        daily      = (df_returns["nvda_return"] - systematic).dropna()
    else:
        daily = df_returns["nvda_return"].dropna()

    n        = len(daily)
    conf     = 1.96 / np.sqrt(n)   # ±95% significance band

    acf_vals  = acf(daily,  nlags=nlags, fft=True,  alpha=None)
    pacf_vals = pacf(daily, nlags=nlags, method="ywm", alpha=None)

    lags = list(range(0, nlags + 1))

    return {
        "lags"     : lags,
        "acf"      : acf_vals.tolist(),
        "pacf"     : pacf_vals.tolist(),
        "conf"     : conf,
        "n"        : n,
        "series"   : series,
    }

@st.cache_data
def build_data_explorer(
    df_returns: pd.DataFrame,
    df_loadings: pd.DataFrame,
) -> dict:
    """
    Builds summary stats tables and raw series for data explorer tab.
    """
    def _stats(series: pd.Series, scale: float = 100) -> dict:
        s = series * scale
        return {
            "Mean"        : round(s.mean(), 2),
            "Median"      : round(s.median(), 2),
            "Min"         : round(s.min(), 2),
            "Max"         : round(s.max(), 2),
            "Range"       : round(s.max() - s.min(), 2),
            "StdDev"      : round(s.std(), 2),
            "StdDev/Mean" : abs(round(s.std()/s.mean(), 2)) if s.std() != 0 else None,
        }

    # ── Factor Returns table ───────────────────────────────────────
    ret_rows = {}
    ret_rows["NVDA Return"] = _stats(df_returns["nvda_return"])
    for f in FACTORS:
        col = f"ret_{f}"
        if col in df_returns.columns:
            ret_rows[f] = _stats(df_returns[col])
    returns_df = pd.DataFrame(ret_rows).T
    returns_df.index.name = "Factor"

    # ── Factor Exposures table ─────────────────────────────────────
    exp_rows = {}
    for f in FACTORS:
        col = f"exp_{f}"
        if col in df_loadings.columns:
            exp_rows[f] = _stats(df_loadings[col], scale=1)
    exposures_df = pd.DataFrame(exp_rows).T
    exposures_df.index.name = "Factor"

    # ── Raw series lookup ──────────────────────────────────────────
    # { display_name: pd.Series }
    raw = {"NVDA Return": df_returns["nvda_return"] * 100}
    for f in FACTORS:
        if f"ret_{f}" in df_returns.columns:
            raw[f"ret_{f}"] = df_returns[f"ret_{f}"] * 100
        if f"exp_{f}" in df_loadings.columns:
            raw[f"exp_{f}"] = df_loadings[f"exp_{f}"]

    return {
        "returns_df" : returns_df,
        "exposures_df": exposures_df,
        "raw"        : raw,
        "dates"      : df_returns.index.tolist(),
    }


