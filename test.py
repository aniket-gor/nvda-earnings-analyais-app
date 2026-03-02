# -*- coding: utf-8 -*-
"""
Created on Sat Feb 28 00:44:09 2026

@author: anike
"""

from backend.loader  import load_all
from backend.compute import build_master_df, compute_summary_stats

# ── Load data ─────────────────────────────────────────────────────────
df_returns, df_loadings, earnings_dates = load_all()
df = build_master_df(df_returns, df_loadings)

# Compute and render table
summary_df = compute_summary_stats(
    df, earnings_dates,
    day_n=1
)