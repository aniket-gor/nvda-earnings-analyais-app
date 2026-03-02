# tabs/tab_fullperiod.py

import streamlit as st
import pandas as pd
from backend.loader  import load_all
from backend.compute import (
    build_master_df, compute_summary_stats,
    build_drilldown_data, build_factor_contributions,
)
from components.charts import (
    plot_returns_and_equity, plot_drawdown, plot_factor_heatmap,
)
from components.ui import card, card_title, divider, selected_row_label, empty_state, render_summary_table



@st.cache_data(show_spinner="Loading data...")
def get_data():
    return load_all()


def get_date_range(df: pd.DataFrame) -> tuple:
    year = st.session_state.get("fp_selected_year")
    qtr  = st.session_state.get("fp_selected_quarter")

    if year is None:
        return df.index.min(), df.index.max()

    if qtr is None:
        start = pd.Timestamp(f"{year}-01-01")
        end   = pd.Timestamp(f"{year}-12-31")
    else:
        qtr_map = {"Q1": (1,3), "Q2": (4,6), "Q3": (7,9), "Q4": (10,12)}
        m_start, m_end = qtr_map[qtr]
        start = pd.Timestamp(f"{year}-{m_start:02d}-01")
        end   = pd.Timestamp(f"{year}-{m_end:02d}-01") + pd.offsets.MonthEnd(1)

    return max(start, df.index.min()), min(end, df.index.max())


def render():
    df_returns, df_loadings, earnings_dates = get_data()
    df = build_master_df(df_returns, df_loadings)

    if "fp_selected_year"    not in st.session_state:
        st.session_state["fp_selected_year"]    = None
    if "fp_selected_quarter" not in st.session_state:
        st.session_state["fp_selected_quarter"] = None
    if "fp_table_view"       not in st.session_state:
        st.session_state["fp_table_view"]        = "years"

    start, end      = get_date_range(df)
    df_filtered     = df[(df.index >= start) & (df.index <= end)]
    earnings_filtered = [e for e in earnings_dates
                         if start <= pd.Timestamp(e) <= end]

    # ── Navigation guide (collapsed by default) ───────────────────
    with st.expander("ℹ️  About Full Period Analysis", expanded=False):      
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
        This tab provides a comprehensive performance snapshot of the portfolio over its entire history. It is designed to bridge the gap between high-level **CAGR/Returns** and daily **Factor Attribution**, allowing you to identify the drivers of significant return events whether they occur during earnings windows or during standard market regimes.
        """)
        
        st.divider()
    
        # 2. Columnar Guide
        col1, col2, col3, col4 = st.columns(4)
    
        with col1:
            st.markdown("##### Returns Drilldown")
            st.markdown("""
            - **Temporal Filter:** Click a **Year** or **Quarter** to filter all charts.
            - **Navigation:** Use **↺ Back** to reset the view to the full history.
            """)

        with col2:
            st.markdown("##### Returns & CAGR")
            st.markdown("""
            - **Daily Returns:** The top bar chart shows raw daily returns.
            - **Equity Curve:** The bottom area chart shows cumulative CAGR growth.
            - **Amber Lines:** Vertical markers indicate earnings announcement dates.
            - **Toggle:** Switch between *Total*, *Systematic*, and *Idiosyncratic* views.
            """)
    
        with col3:
            st.markdown("##### Drawdown")
            st.markdown("""
            - **Risk Toggle:** Switch between *Total*, *Systematic*, and *Idiosyncratic* risk views.
            - **Recovery:** Visualize the depth and duration of peak-to-trough declines.
            - **Zoom in:** Drag the cursor across the chart to look at specific periods. Double click to reset zoom.
            """)
    
        with col4:
            st.markdown("##### Factor Attribution")
            st.markdown("""
            - **Factor Heatmap:** See which specific Barra factors drove returns on any date.
            - **Zoom in:** Drag the cursor across the chart to look at specific periods. Double click to reset zoom.
            """)
    
        st.caption("Note: All charts and summary statistics synchronize automatically to the date range selected in the Drilldown table.")

    # ═══════════════════════════════════════════════════════════════
    # ROW 1 — Summary stats | Drilldown table | Drawdown chart
    # ═══════════════════════════════════════════════════════════════      
    col_stats, col_drill, col_draw = st.columns([1.5, 1.3, 1.7])

    # ── Summary stats ──────────────────────────────────────────────
    with col_stats:
        with card():
            card_title("Summary Statistics")
            summary = compute_summary_stats(df, earnings_dates, day_n=1)
            render_summary_table(summary)
            #summary     = compute_summary_stats(df, earnings_dates, day_n=1)
            #auto_height = (len(summary) * 35) + 35
            #st.dataframe(summary, use_container_width=True, height=auto_height)

    # ── Drilldown table ────────────────────────────────────────────
    with col_drill:
        with card():
            year       = st.session_state.get("fp_selected_year")
            qtr        = st.session_state.get("fp_selected_quarter")
            dd_data    = build_drilldown_data(df)
            table_view = st.session_state.get("fp_table_view", "years")

            # Title row + back button
            title_c, back_c = st.columns([6, 1])
            with title_c:
                if year is not None:
                    breadcrumb = f"{year} → {qtr}" if qtr else str(year)
                    card_title("Returns Drilldown", subtitle=breadcrumb)
                else:
                    card_title("Returns Drilldown")
            with back_c:
                if year is not None:
                    if st.button("↺ Back", key="fp_back"):
                        if qtr is not None:
                            st.session_state["fp_selected_quarter"] = None
                            st.session_state["fp_table_view"]       = "years"
                        else:
                            st.session_state["fp_selected_year"]    = None
                            st.session_state["fp_table_view"]       = "years"
                        st.rerun()

            from config import THEME
            h_style = (
                f"font-size:{THEME['font_size_body']}px;"
                f"font-weight:700;color:{THEME['text_muted']};"
                f"background:{THEME['bg_panel_alt']};"
                f"padding:3px 4px;display:block;text-align:center;"
            )
            c_style = (
                f"font-size:{THEME['font_size_cell']}px;"
                f"color:{THEME['text_primary']};"
                f"padding:3px 4px;display:block;text-align:center;"
            )

            # Column headers
            h1, h2, h3, h4 = st.columns([1.2, 0.9, 0.9, 0.9])
            h1.markdown(f"<span style='{h_style}'>Period</span>",       unsafe_allow_html=True)
            h2.markdown(f"<span style='{h_style}'>Total</span>",        unsafe_allow_html=True)
            h3.markdown(f"<span style='{h_style}'>Systematic</span>",   unsafe_allow_html=True)
            h4.markdown(f"<span style='{h_style}'>Idiosyncratic</span>",unsafe_allow_html=True)

            rows = (
                dd_data.items()
                if table_view == "years"
                else dd_data[year]["quarters"].items()
            )

            for i, (period, data) in enumerate(rows):
                #bg   = f"background:{THEME['bg_panel_alt']};" if i % 2 else ""
                bg   = f"background:{THEME['bg_panel']};"
                is_selected = (
                    (table_view == "years"    and period == st.session_state.get("fp_selected_year")) or
                    (table_view == "quarters" and period == st.session_state.get("fp_selected_quarter"))
                )
                btn_key = f"dd_yr_{period}" if table_view == "years" else f"dd_q_{year}_{period}"

                r1, r2, r3, r4 = st.columns([1.2, 0.9, 0.9, 0.9])
                with r1:
                    if is_selected:
                        selected_row_label(str(period))
                    else:
                        if st.button(str(period), key=btn_key,
                                     use_container_width=True):
                            if table_view == "years":
                                st.session_state["fp_selected_year"]    = period
                                st.session_state["fp_selected_quarter"] = None
                                st.session_state["fp_table_view"]       = "quarters"
                            else:
                                st.session_state["fp_selected_quarter"] = period
                            st.rerun()

                r2.markdown(f"<span style='{c_style}{bg}'>{data['total']}%</span>",  unsafe_allow_html=True)
                r3.markdown(f"<span style='{c_style}{bg}'>{data['sys']}%</span>",    unsafe_allow_html=True)
                r4.markdown(f"<span style='{c_style}{bg}'>{data['idio']}%</span>",   unsafe_allow_html=True)

    # ── Drawdown chart ─────────────────────────────────────────────
    with col_draw:
        with card():
            fig_dd = plot_drawdown(df_filtered, earnings_filtered)
            st.plotly_chart(
                fig_dd,
                use_container_width=True,
                config={"displayModeBar": False, "staticPlot": False},
            )

    # ═══════════════════════════════════════════════════════════════
    # ROW 2 — Returns + equity | Factor heatmap
    # ═══════════════════════════════════════════════════════════════
    col_eq, col_heat = st.columns([1, 1])

    with col_eq:
        with card():
            df_ret_f = df_returns[
                (df_returns.index >= start) & (df_returns.index <= end)
            ]
            fig_combined = plot_returns_and_equity(
                df                 = df_filtered,
                earnings_dates     = earnings_filtered,
                factor_overlays    = st.session_state.get("eq_factor_overlays", []),
                df_returns         = df_ret_f,
                show_earnings_line = True,
                show_earnings_band = False,
            )
            st.plotly_chart(
                fig_combined,
                use_container_width=True,
                config={"displayModeBar": False},
            )

    with col_heat:
        with card():
            df_load_f = df_loadings[
                (df_loadings.index >= start) & (df_loadings.index <= end)
            ]
            df_ret_f  = df_returns[
                (df_returns.index >= start) & (df_returns.index <= end)
            ]
            contrib   = build_factor_contributions(df_ret_f, df_load_f)
            fig_heat  = plot_factor_heatmap(contrib)
            st.plotly_chart(
                fig_heat,
                use_container_width=True,
                config={"displayModeBar": False, "scrollZoom": False},
            )
