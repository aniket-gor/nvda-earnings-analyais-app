# -*- coding: utf-8 -*-
"""
Created on Mon Mar  2 04:19:04 2026

@author: anike
"""

# components/ui.py
"""
Shared UI helpers for consistent card layout and typography across all tabs.
All tabs import from here instead of writing inline HTML.
"""

import streamlit as st
import pandas as pd
from config import THEME


def card():
    """
    Returns a styled st.container(border=True).
    Use as a context manager:

        with card():
            st.plotly_chart(fig)

    CSS for the border wrapper is defined globally in app.py.
    """
    return st.container(border=True)


def card_title(title: str, subtitle: str = None):
    """
    Renders a consistent card title inside a card container.
    Optional subtitle renders inline to the right of the title.

    Usage:
        with card():
            card_title("Cumulative Abnormal Returns", subtitle="2024-11-20")
            st.plotly_chart(fig)
    """
    title_color    = THEME["text_primary"]
    subtitle_color = THEME["text_muted"]
    title_size     = THEME["font_size_title"]
    subtitle_size  = THEME["font_size_body"]
    font           = THEME["font_family"]

    if subtitle:
        st.markdown(
            f"<div style='margin-bottom:6px;line-height:1.2;'>"
            f"<span style='font-size:{title_size}px;font-weight:700;"
            f"color:{title_color};font-family:{font};'>{title}</span>"
            f"<span style='font-size:{subtitle_size}px;font-weight:400;"
            f"color:{subtitle_color};font-family:{font};"
            f"margin-left:10px;'>{subtitle}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div style='margin-bottom:6px;line-height:1.2;'>"
            f"<span style='font-size:{title_size}px;font-weight:700;"
            f"color:{title_color};font-family:{font};'>{title}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )


def section_label(text: str):
    """
    Smaller label for control groups or table headers inside cards.
    e.g. "Factor Exposures", "Factor Returns (%)"
    """
    st.markdown(
        f"<div style='font-size:{THEME['font_size_body']}px;"
        f"font-weight:700;color:{THEME['text_muted']};"
        f"font-family:{THEME['font_family']};"
        f"margin:0 0 4px;'>{text}</div>",
        unsafe_allow_html=True,
    )


def empty_state(message: str):
    """
    Consistent empty/hint state message.
    e.g. "Select an event to view factor detail."
    """
    st.markdown(
        f"<div style='font-size:{THEME['font_size_body']}px;"
        f"color:{THEME['text_hint']};"
        f"font-family:{THEME['font_family']};"
        f"margin-top:4px;'>{message}</div>",
        unsafe_allow_html=True,
    )


def divider():
    """Thin horizontal rule between sections inside a card."""
    st.markdown(
        f"<div style='border-top:1px solid {THEME['border_subtle']};"
        f"margin:{THEME['space_sm']}px 0;'></div>",
        unsafe_allow_html=True,
    )


def selected_row_label(text: str):
    """
    Highlighted label for the selected row in custom HTML tables.
    Used in tab_earnings CAR table and tab_fullperiod drilldown.
    """
    st.markdown(
        f"<span style='font-size:{THEME['font_size_cell']}px;"
        f"font-weight:700;"
        f"color:{THEME['primary']};"
        f"background:{THEME['selected_bg']};"
        f"padding:0 6px;"
        f"display:block;text-align:center;"
        f"height:26px;line-height:26px;"
        f"border-radius:{THEME['border_radius']}px;"
        f"border:1px solid {THEME['selected_border']};'>"
        f"{text}</span>",
        unsafe_allow_html=True,
    )

def render_summary_table(df: pd.DataFrame):
    """
    Static summary stats table using col_drilldown pattern.
    """
    from config import THEME

    cols = list(df.columns)
    rows = list(df.index)

    # ── Column headers ────────────────────────────────────────────
    h_cols = st.columns([1.8, 1, 1, 1])  # ← wider first column
    h_style = (
        f"font-size:{THEME['font_size_body']}px;font-weight:700;"
        f"color:{THEME['text_primary']};"      # ← black instead of muted
        f"background:{THEME['bg_panel_alt']};" # ← header stays highlighted
        f"padding:4px 8px;display:block;text-align:center;"
    )
    h_cols[0].markdown(f"<span style='{h_style}'>Metric</span>", unsafe_allow_html=True)
    for i, col in enumerate(cols):
        h_cols[i+1].markdown(f"<span style='{h_style}'>{col}</span>", unsafe_allow_html=True)

    # ── Data rows ─────────────────────────────────────────────────
    c_style = (
        f"font-size:{THEME['font_size_cell']}px;font-weight:600;"
        f"color:{THEME['text_primary']};"       # ← all black
        f"padding:4px 8px;display:block;text-align:center;"
    )
    for i, row_label in enumerate(rows):
        # ← No alternating bg — all use bg_panel (white)
        bg = f"background:{THEME['bg_panel']};"
        r_cols = st.columns([1.8, 1, 1, 1])  # ← consistent widths

        # Row label — wider first column
        r_cols[0].markdown(
            f"<span style='{c_style}"
            f"text-align:left;font-weight:700;{bg}'>"
            f"{row_label}</span>",
            unsafe_allow_html=True,
        )

        # Value cells — even distribution, all black
        for j, col in enumerate(cols):
            val_str = str(df.loc[row_label, col])
            r_cols[j+1].markdown(
                f"<span style='{c_style}{bg}'>"
                f"{val_str}</span>",
                unsafe_allow_html=True,
            )
