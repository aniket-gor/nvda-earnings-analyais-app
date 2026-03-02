# tabs/tab_earnings.py

import streamlit as st
import pandas as pd
from backend.loader  import load_all
from backend.compute import (
    build_earnings_factor_decomp, build_car_heatmap,
    build_car_lines, build_factor_daily_series,
)
from components.charts import (
    plot_earnings_factor_heatmap, plot_car_heatmap,
    plot_car_line_chart, plot_factor_detail_bar_multi,
)
from components.ui import (
    card, card_title, divider, empty_state, selected_row_label,
)
from config import THEME, CELL_COLORS, CELL_TEXT_COLORS


@st.cache_data(show_spinner="Loading data...")
def get_data():
    return load_all()


def _cell_color(val: float) -> str:
    if val is None:  return CELL_COLORS["neutral"]
    if val >= 10:    return CELL_COLORS["pos_strong"]
    if val >= 5:     return CELL_COLORS["pos_medium"]
    if val >= 2:     return CELL_COLORS["pos_mild"]
    if val >= 0:     return CELL_COLORS["pos_faint"]
    if val >= -2:    return CELL_COLORS["neg_faint"]
    if val >= -5:    return CELL_COLORS["neg_mild"]
    if val >= -10:   return CELL_COLORS["neg_medium"]
    return                  CELL_COLORS["neg_strong"]


def _text_color(val: float) -> str:
    if val is None:  return CELL_TEXT_COLORS["neutral"]
    if val >= 5:     return CELL_TEXT_COLORS["pos_strong"]
    if val >= 0:     return CELL_TEXT_COLORS["positive"]
    if val >= -5:    return CELL_TEXT_COLORS["negative"]
    return                  CELL_TEXT_COLORS["neg_strong"]


def render():
    df_returns, df_loadings, earnings_dates = get_data()

    # ── Session state ──────────────────────────────────────────────
    if "ee_selected_event" not in st.session_state:
        st.session_state["ee_selected_event"] = None
    if "ee_pre_window"  not in st.session_state:
        st.session_state["ee_pre_window"]  = 20
    if "ee_post_window" not in st.session_state:
        st.session_state["ee_post_window"] = 20
    if "ee_factor_row"  not in st.session_state:
        st.session_state["ee_factor_row"]  = ["Idiosyncratic", "NVDA Total", "Market"]
    if "ee_factor_snap" not in st.session_state:
        st.session_state["ee_factor_snap"] = "D+20"

    pre_window  = st.session_state["ee_pre_window"]
    post_window = st.session_state["ee_post_window"]

    decomp = build_earnings_factor_decomp(
        df_returns, df_loadings, earnings_dates,
        pre_window=pre_window, post_window=post_window,
    )
    car_data  = build_car_heatmap(
        df_returns, df_loadings, earnings_dates,
        pre_window=pre_window, post_window=post_window,
    )
    car_lines = build_car_lines(df_returns, df_loadings, earnings_dates)

    selected    = st.session_state.get("ee_selected_event")
    all_factors = list(decomp["average"].index)
    snap_labels = decomp["snap_labels"]
    rows        = car_data["rows"]
    car_snaps   = car_data["snap_labels"]
    z           = car_data["z"]

    event_date_map = {
        label: pd.Timestamp(ed)
        for label, ed in zip(rows, reversed(earnings_dates))
    }
    d0_date = event_date_map.get(selected) if selected else None

    # Identify D0 column index for vertical divider
    d0_col_idx = car_snaps.index("D0") if "D0" in car_snaps else None
    
    with st.expander("ℹ️  About Earnings Events Analysis", expanded=False):
        # CSS to tighten vertical spacing and match your clean UI
        st.markdown("""
        <style>
            [data-testid="stExpander"] .stMarkdown { margin-bottom: -15px; }
            [data-testid="stExpander"] hr { margin-top: 5px; margin-bottom: 5px; }
            [data-testid="stExpander"] h5 { margin-top: 0px; margin-bottom: 5px; }
        </style>
        """, unsafe_allow_html=True)
        # 1. Purpose Statement
        st.markdown("""
        This tab isolates price action around earnings announcements to analyze **Post-Earnings Announcement Drift (PEAD)**. By centering all data on **D0** (the event date), you can evaluate if specific quarters exhibit consistent alpha persistence or if returns are driven by broader factor exposures (Market, Beta, etc.) during the volatility window.
        """)
        
        st.divider()
    
        # 2. Columnar Guide (3 columns for the specialized layout)
        col1, col2, col3 = st.columns(3)
    
        with col1:
            st.markdown("##### Event Selection")
            st.markdown("""
            - **CAR Heatmap:** Click an **Earnings Quarter** (e.g., Q3 '25) to anchor the entire page to that specific event date.
            - **D0 Alignment:** Values are shown as Cumulative Abnormal Returns (%) relative to the day of the announcement.
            """)
    
        with col2:
            st.markdown("##### Drift & Persistence")
            st.markdown("""
            - **PEAD Line Chart:** Compare the *Average* drift across all 12 quarters against your *Selected* quarter.
            - **Pre/Post Windows:** Observe how the stock behaves leading into the earnings announcement vs. the subsequent 20-day drift.
            """)
    
        with col3:
            st.markdown("##### Factor Decomp")
            st.markdown("""
            - **Decomposition:** See exactly how much of the D0 move was 'Stock Specific' vs. 'Systematic' (Factor-driven).
            - **Daily Detail:** Select up to 3 factors (e.g., Value, Momentum) to see their day-by-day impact during the drift window.
            """)
    
        st.caption("Note: Use the **↺ Reset** button to clear your selection and return to the 12-quarter average view.")
    
    left_col, right_col = st.columns([9, 11])

    # ════════════════════════════════════════════════════════════════
    # LEFT — CAR table + CAR line chart
    # ════════════════════════════════════════════════════════════════
    with left_col:
        with card():

            # ── Title row + reset pushed right ────────────────────
            title_c, spacer_c, reset_c = st.columns([9.5, 1, 1])
            with title_c:
                subtitle = (d0_date.strftime("%m-%d-%Y")
                            if d0_date else "select an earnings event →")
                card_title("Cumulative Abnormal Returns (%)", subtitle=subtitle)
            with reset_c:
                if st.button("↺ Reset", key="ee_reset"):
                    st.session_state["ee_selected_event"] = None
                    st.rerun()

            # ── Column headers ─────────────────────────────────────
            # D0 gets bg highlight; D0 column gets right border as divider
            cols = st.columns([1.2] + [1] * len(car_snaps))
            cols[0].markdown(
                f"<div style='"
                f"font-size:{THEME['font_size_body']}px;"
                f"font-weight:700;color:{THEME['text_muted']};"
                f"text-align:center;"
                f"border-bottom:2px solid {THEME['border_subtle']};"
                f"padding:2px 0;'>Period</div>",
                unsafe_allow_html=True,
            )
            for i, label in enumerate(car_snaps):
                is_d0      = label == "D0"
                bg         = f"background:{THEME['bg_panel_alt']};" if is_d0 else ""
                
                cols[i+1].markdown(
                    f"<div style='"
                    f"font-size:{THEME['font_size_body']}px;"
                    f"font-weight:700;color:{THEME['text_muted']};"
                    f"text-align:center;"
                    f"border-bottom:2px solid {THEME['border_subtle']};"
                    f"padding:2px 0;{bg}'>{label}</div>",
                    unsafe_allow_html=True,
                )

            # ── Data rows — tightened ──────────────────────────────
            cell_base = (
            f"font-size:{THEME['font_size_body']}px;"
            f"font-weight:600;text-align:center;"
            f"height:30px;line-height:28px;"
            f"border-radius:{THEME['border_radius']}px;"
            f"border:1px solid rgba(0,0,0,0.04);"
            )
            for event_label, row_vals in zip(rows, z):
                r_cols = st.columns([1.2] + [1] * len(car_snaps))
                with r_cols[0]:
                    if event_label == selected:
                        selected_row_label(event_label)
                    else:
                        if st.button(event_label,
                                     key=f"ee_row_{event_label}",
                                     use_container_width=True):
                            st.session_state["ee_selected_event"] = event_label
                            st.rerun()

                for i, val in enumerate(row_vals):
                    val_str   = f"{val:+.1f}" if val is not None else "—"
                    is_d0_col = (i == d0_col_idx)
                    
                    r_cols[i+1].markdown(
                    f"<div style='{cell_base}"
                    f"background:{_cell_color(val)};"
                    f"color:{_text_color(val)};'>{val_str}</div>",
                    unsafe_allow_html=True,
                    )

            divider()

            # ── CAR line chart ─────────────────────────────────────
            fig_line = plot_car_line_chart(car_lines, selected_event=selected)
            fig_line.update_layout(height=300)
            st.plotly_chart(
                fig_line,
                use_container_width=True,
                config={"displayModeBar": False},
            )

    # ════════════════════════════════════════════════════════════════
    # RIGHT — Factor decomp heatmap + detail bar
    # ════════════════════════════════════════════════════════════════
    with right_col:
        with card():
            fig_decomp = plot_earnings_factor_heatmap(
                decomp, selected_event=selected,
            )
            st.plotly_chart(
                fig_decomp,
                use_container_width=True,
                config={"displayModeBar": False},
            )

            divider()

            ctrl_l, ctrl_r = st.columns([1.3, 1])
            with ctrl_l:
                # ── Multiselect fix: rely on key only, no default ──
                # Guard ensures valid list type but never resets content
                if not isinstance(st.session_state.get("ee_factor_row"), list):
                    st.session_state["ee_factor_row"] = ["Idiosyncratic"]

                factors_selected = st.multiselect(
                    "Factor (max 3)",
                    all_factors,
                    max_selections=3,
                    key="ee_factor_row",   # ← no default= param
                )

            with ctrl_r:
                if st.session_state["ee_factor_snap"] not in snap_labels:
                    st.session_state["ee_factor_snap"] = snap_labels[0]
                snap = st.selectbox(
                    "Snapshot",
                    snap_labels,
                    #index=snap_labels.index(st.session_state["ee_factor_snap"]),
                    key="ee_factor_snap",
                )

            if not factors_selected:
                empty_state("Select at least one factor.")
            elif not selected:
                empty_state("Select an earnings event to view factor detail.")
            else:
                all_details = {
                    f: build_factor_daily_series(
                        df_returns, df_loadings, earnings_dates,
                        factor         = f,
                        snap           = snap,
                        selected_event = selected,
                        pre_window     = pre_window,
                        post_window    = post_window,
                    )
                    for f in factors_selected
                }
                title = (f"{', '.join(factors_selected)} — "
                         f"{selected} daily returns to {snap}")
                fig_detail = plot_factor_detail_bar_multi(all_details)
                fig_detail.update_layout(
                    title=dict(
                        text    = title,
                        x       = 0.0,
                        xanchor = "left",
                        font    = dict(
                            size   = THEME["font_size_body"],
                            color  = THEME["text_primary"],
                            family = THEME["font_family"],
                        ),
                    ),
                    height=240,
                )
                st.plotly_chart(
                    fig_detail,
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
