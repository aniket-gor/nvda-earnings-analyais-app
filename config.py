# -*- coding: utf-8 -*-
"""
Created on Fri Feb 27 22:00:03 2026
@author: anike
"""

import os

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

RETURNS_FILE  = os.path.join(DATA_DIR, "01_case_study_returns.csv")
LOADINGS_FILE = os.path.join(DATA_DIR, "02_case_study_factor_loadings.csv")
EARNINGS_FILE = os.path.join(DATA_DIR, "03_case_study_earnings_dates.csv")

# ── Barra Factor List ──────────────────────────────────────────────────────
FACTORS = [
    "Beta", "Dividend Yield", "Earnings Yield", "Excess Beta",
    "Growth", "Leverage", "Liquidity", "Market", "Mid Cap",
    "Momentum", "Quality", "Semiconductors", "Size", "Value", "Volatility"
]

# ── Event Window ───────────────────────────────────────────────────────────
EVENT_WINDOW_PRE  = 10
EVENT_WINDOW_POST = 30

# ── Statistical Parameters ─────────────────────────────────────────────────
SIGNIFICANCE_LEVEL    = 0.05
TRADING_DAYS_PER_YEAR = 252
ROLLING_WINDOW_LONG   = 90
ROLLING_WINDOW_SHORT  = 30
ROLLING_WINDOW_MICRO  = 5

# ── CAR Convention ─────────────────────────────────────────────────────────
DEFAULT_CAR_METHOD = "additive"

# ── Theme ──────────────────────────────────────────────────────────────────
THEME = {

    # ── Core palette (MSCI institutional) ──────────────────────────────────
    "bg_page"      : "#FFFFFF",       # page / app background F7F9FC
    "bg_panel"     : "#FAFBFC",       # card / panel surface
    "bg_panel_alt" : "#F3F4F6",       # alternating table row / secondary surface
    "primary"      : "#005EB8",       # MSCI navy  — Total series, primary actions
    "secondary"    : "#00A3E0",       # MSCI sky blue — Systematic series
    "accent"       : "#00B08B",       # teal — Idiosyncratic series
    "positive"     : "#2E7D32",       # dark green — positive values
    "negative"     : "#C62828",       # dark red   — negative values
    "neutral"      : "#616161",       # axes / secondary labels
    "grid"         : "#E8EDF2",       # chart gridlines
    "earnings_line": "#F4A100",       # amber — earnings date markers

    # ── Text hierarchy ──────────────────────────────────────────────────────
    "text_primary"       : "#31333F",       # main headings, chart titles
    "text_muted"         : "#6b7280",       # secondary labels, column headers
    "text_muted_further" : "#9ca3af",       # secondary labels, column headers
    "text_hint"          : "#9ca3af",       # placeholder / empty-state text

    # ── Typography scale ────────────────────────────────────────────────────
    "font_family"      : "Arial",
    "font_size_base"   : 13,          # kept for backward compat in charts.py
    "font_size_title"  : 16,          # chart/section main titles
    "font_size_heading": 14,          # card sub-headers, annotation labels
    "font_size_body"   : 13,          # body text, table headers
    "font_size_cell"   : 14,          # table cell values
    "font_size_caption": 11,          # axis ticks, legends, captions

    # ── Spacing scale (integers — use as f"{THEME['space_md']}px") ─────────
    "space_xs" : 4,
    "space_sm" : 8,
    "space_md" : 16,
    "space_lg" : 24,

    # ── Shape & elevation ───────────────────────────────────────────────────
    "border_radius": 6,
    "border_subtle": "#DDE1E7",          # lighter — less contrast against bg_page DDE1E7
    "card_shadow"  : "0 2px 12px rgba(0,0,0,0.10), 0 1px 3px rgba(0,0,0,0.06)",

    # ── Selection state (row highlights in custom HTML tables) ─────────────
    "selected_bg"    : "#E8F0FE",     # light navy tint
    "selected_border": "#93c5fd",     # mid-blue border
    # selected text → use "primary" (#005EB8)

    # ── Chart-specific aliases ──────────────────────────────────────────────
    "chart_bg"  : "#FFFFFF",          # == bg_panel
    "chart_grid": "#E8EDF2",          # == grid
}

# ── Return series colors (canonical mapping used across all charts) ─────────
RETURN_COLORS = {
    "Total"         : THEME["primary"],    # #005EB8 MSCI navy
    "Systematic"    : THEME["secondary"],  # #00A3E0 MSCI sky blue
    "Idiosyncratic" : THEME["accent"],     # #00B08B teal
}

# ── Factor overlay colors (used in plot_returns_and_equity overlays) ────────
FACTOR_OVERLAY_COLORS = [
    "#9C27B0",   # purple
    "#FF5722",   # deep orange
    "#795548",   # brown
    "#607D8B",   # blue-grey
    "#E91E63",   # pink
    "#009688",   # teal variant
]

# ── Cell background tints for P&L HTML tables (tab_earnings CAR table) ──────
CELL_COLORS = {
    "pos_strong" : "#86efac",   # val >= +10%
    "pos_medium" : "#bbf7d0",   # val >= +5%
    "pos_mild"   : "#dcfce7",   # val >= +2%
    "pos_faint"  : "#f0fdf4",   # val >= 0%
    "neutral"    : "#f9fafb",   # None
    "neg_faint"  : "#fff1f2",   # val >= -2%
    "neg_mild"   : "#ffe4e6",   # val >= -5%
    "neg_medium" : "#fecdd3",   # val >= -10%
    "neg_strong" : "#fda4af",   # val < -10%
}

# ── Cell text colors for P&L HTML tables ────────────────────────────────────
CELL_TEXT_COLORS = {
    "pos_strong" : "#14532d",   # val >= +5%
    "positive"   : "#166534",   # val >= 0%
    "negative"   : "#9f1239",   # val >= -5%
    "neg_strong" : "#881337",   # val < -5%
    "neutral"    : "#9ca3af",   # None
}
