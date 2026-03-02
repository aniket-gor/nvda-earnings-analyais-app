# -*- coding: utf-8 -*-
"""
Created on Fri Feb 27 22:00:33 2026

@author: anike
"""

# backend/loader.py

import pandas as pd
import streamlit as st
from config import RETURNS_FILE, LOADINGS_FILE, EARNINGS_FILE, FACTORS


#@st.cache_data(show_spinner="Loading data...")
def load_all():
    df_returns     = _load_returns()
    df_loadings    = _load_loadings()
    earnings_dates = _load_earnings()

    # Align on common dates
    common_idx  = df_returns.index.intersection(df_loadings.index)
    df_returns  = df_returns.loc[common_idx].sort_index()
    df_loadings = df_loadings.loc[common_idx].sort_index()

    return df_returns, df_loadings, earnings_dates


def _parse_dates(series: pd.Series) -> pd.Series:
    """
    Handles mixed date formats: MM/DD/YY, MM/DD/YYYY, MM-DD-YYYY
    """
    return pd.to_datetime(series, infer_datetime_format=True, dayfirst=False)


def _load_returns():
    df = pd.read_csv(
        RETURNS_FILE,
        header=2,          # row 3 = index 2
        index_col=None
    )
    df.columns = df.columns.str.strip()
    df["Date"]  = _parse_dates(df["Date"])
    df          = df.set_index("Date").sort_index()

    # Rename NVDA column
    df.rename(columns={"NVDA": "nvda_return"}, inplace=True)

    # Rename factor return columns
    factor_rename = {f: f"ret_{f}" for f in FACTORS if f in df.columns}
    df.rename(columns=factor_rename, inplace=True)

    # Coerce all to numeric, drop fully empty rows
    df = df.apply(pd.to_numeric, errors="coerce").dropna(how="all")
    return df


def _load_loadings():
    df = pd.read_csv(
        LOADINGS_FILE,
        header=2,
        index_col=None
    )
    df.columns = df.columns.str.strip()
    df["Date"]  = _parse_dates(df["Date"])
    df          = df.set_index("Date").sort_index()

    # Rename factor exposure columns
    factor_rename = {f: f"exp_{f}" for f in FACTORS if f in df.columns}
    df.rename(columns=factor_rename, inplace=True)

    df = df.apply(pd.to_numeric, errors="coerce").dropna(how="all")
    return df


def _load_earnings():
    df = pd.read_csv(EARNINGS_FILE, header=1)
    df.columns = df.columns.str.strip()

    # Find the earnings date column regardless of exact spacing
    date_col = [c for c in df.columns
                if "earnings" in c.lower() or "date" in c.lower()][0]

    dates = _parse_dates(df[date_col]).dropna().sort_values().tolist()
    return dates
