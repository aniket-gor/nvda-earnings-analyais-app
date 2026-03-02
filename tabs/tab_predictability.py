# tabs/tab_predictability.py

import streamlit as st
import pandas as pd
from backend.loader  import load_all
from backend.compute import (
    build_scatter_data, build_correlation_matrix,
    build_rolling_vol, build_acf_pacf,
    _parse_metric_label, _quarter_label,
    SCATTER_CAR_OFFSETS, SCATTER_VOL_OFFSETS,
)
from components.charts import (
    plot_correlation_heatmap, plot_predictability_scatter,
    plot_rolling_vol, plot_acf_pacf,
)
from components.ui import card, card_title, empty_state


@st.cache_data(show_spinner="Loading data...")
def get_data():
    return load_all()


def _build_axis_options() -> list:
    options = []
    for o in SCATTER_CAR_OFFSETS:
        sign = f"+{o}" if o > 0 else str(o)
        options.append({"label": f"CAR: D{sign}", "type": "car", "offset": o})
    for o in SCATTER_VOL_OFFSETS:
        sign = f"+{o}" if o > 0 else str(o)
        options.append({"label": f"Vol: D{sign}", "type": "vol", "offset": o})
    return options


def render():
    df_returns, df_loadings, earnings_dates = get_data()

    # ── Session state ──────────────────────────────────────────────
    for key, default in [
        ("pred_series",     "Idiosyncratic"),
        ("pred_x",          "CAR: D+1"),
        ("pred_y",          "CAR: D+20"),
        ("pred_vol_window", 20),
        ("pred_vol_series", "Idiosyncratic"),
        ("pred_vol_zoom",   "Full Period"),
        ("pred_acf_series", "Idiosyncratic"),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    scatter_data = build_scatter_data(df_returns, df_loadings, earnings_dates)
    axis_options = _build_axis_options()
    axis_labels  = [o["label"] for o in axis_options]
    axis_map     = {o["label"]: o for o in axis_options}
    
    with st.expander("ℹ️  About Predictability Analysis", expanded=False):      
        # CSS to tighten vertical spacing and match your clean UI
        st.markdown("""
        <style>
            [data-testid="stExpander"] .stMarkdown { margin-bottom: -15px; }
            [data-testid="stExpander"] hr { margin-top: 5px; margin-bottom: 5px; }
            [data-testid="stExpander"] h5 { margin-top: 0px; margin-bottom: 5px; }
        </style>
        """, unsafe_allow_html=True)
        
        # 1. Purpose Statement (Full Width)
        st.markdown("""
        This tab evaluates whether pre and post earnings metrics (return/vol) show any relationships. Users can also analyze the rolling volatility. 
        """)

        st.divider()
    
        # 2. Columnar Guide (One column per major section)
        col1, col2, col3 = st.columns(3)
    
        with col1:
            st.markdown("### Correlation & Scatter")
            st.markdown("""
            - **Internal Toggle:** Switch between *Idiosyncratic* and *Total* returns directly inside the Heatmap.
            - **Offsets:** Select different **D+n** windows to see how early returns (X) predict later ones (Y).
            """)
    
        with col2:
            st.markdown("### Risk & Volatility")
            st.markdown("""
            - **Rolling Window:** Change the window (5d, 20d, 60d) to see short-term spikes vs. long-term regime changes.
            - **Event Zoom:** Isolate the chart to a specific earnings quarter to see how risk expanded or contracted.
            - **Drag to Zoom:** Drag the cursor to analyze specific periods.
            """)
    
        with col3:
            st.markdown("### Persistence (ACF)")
            st.markdown("""
            - **Lags:** Check if yesterday's return informs today's (Lag 1) or if there are weekly patterns (Lag 5).
            """)
    
        st.caption("Note: Dotted **amber** lines in time-series charts represent specific earnings announcement dates.")
    
    left_col, right_col = st.columns([9, 11])

    # ════════════════════════════════════════════════════════════════
    # LEFT — Correlation heatmap + Scatter
    # ════════════════════════════════════════════════════════════════
    with left_col:

        # ── Card 1: Correlation heatmap ────────────────────────────
        with card():
            tc, rc = st.columns([7, 2])
            with tc:
                card_title("Metric Correlation Matrix")
            with rc:
                series_ui = st.radio(
                    "Series", ["Idiosyncratic", "Total"],
                    horizontal=True,
                    key="pred_series",
                    label_visibility="collapsed",
                )
            series    = "idio" if series_ui == "Idiosyncratic" else "total"
            corr_data = build_correlation_matrix(scatter_data, series=series)
            fig_corr  = plot_correlation_heatmap(corr_data)
            st.plotly_chart(
                fig_corr,
                use_container_width=True,
                config={"displayModeBar": False},
            )

        # ── Card 2: Scatter ────────────────────────────────────────
        with card():
            c1, c2 = st.columns(2)
            with c1:
                x_label = st.selectbox(
                    "X Axis", axis_labels,
                    index=axis_labels.index(st.session_state["pred_x"]),
                    key="pred_x",
                )
            with c2:
                y_label = st.selectbox(
                    "Y Axis", axis_labels,
                    index=axis_labels.index(st.session_state["pred_y"]),
                    key="pred_y",
                )

            x_opt = axis_map[x_label]
            y_opt = axis_map[y_label]
            fig_scatter = plot_predictability_scatter(
                scatter_data,
                x_type=x_opt["type"], x_offset=x_opt["offset"],
                y_type=y_opt["type"], y_offset=y_opt["offset"],
                series=series,
            )
            st.plotly_chart(
                fig_scatter,
                use_container_width=True,
                config={"displayModeBar": False},
            )

    # ════════════════════════════════════════════════════════════════
    # RIGHT — Rolling vol + ACF/PACF
    # ════════════════════════════════════════════════════════════════
    with right_col:

        # ── Card 1: Rolling volatility ─────────────────────────────
        with card():
            card_title("Rolling Volatility")
            c1, c2, c3 = st.columns([1, 1, 2])
            with c1:
                window = st.selectbox(
                    "Window", [5, 20, 60],
                    index=[5, 20, 60].index(st.session_state["pred_vol_window"]),
                    key="pred_vol_window",
                )
            with c2:
                vol_series_ui = st.selectbox(
                    "Series", ["Idiosyncratic", "Total"],
                    index=["Idiosyncratic", "Total"].index(
                        st.session_state["pred_vol_series"]),
                    key="pred_vol_series",
                )
            with c3:
                quarter_labels = [
                    _quarter_label(pd.Timestamp(e)) for e in earnings_dates
                ]
                zoom_options = ["Full Period"] + list(reversed(quarter_labels))
                if st.session_state["pred_vol_zoom"] not in zoom_options:
                    st.session_state["pred_vol_zoom"] = "Full Period"
                zoom = st.selectbox(
                    "Zoom to Event", zoom_options,
                    index=zoom_options.index(st.session_state["pred_vol_zoom"]),
                    key="pred_vol_zoom",
                )

            vol_series = "idio" if vol_series_ui == "Idiosyncratic" else "total"
            zoom_event = None if zoom == "Full Period" else zoom
            vol_data   = build_rolling_vol(
                df_returns, df_loadings, earnings_dates,
                window=window, series=vol_series,
            )
            fig_vol = plot_rolling_vol(
                vol_data, window=window,
                series=vol_series, zoom_event=zoom_event,
            )
            st.plotly_chart(
                fig_vol,
                use_container_width=True,
                config={"displayModeBar": False},
            )

        # ── Card 2: ACF / PACF ─────────────────────────────────────
        with card():
            ac, rc = st.columns([7, 2])
            # with rc:
            #     acf_series_ui = st.radio(
            #         "ACF Series", ["Idiosyncratic", "Total"],
            #         horizontal=True,
            #         key="pred_acf_series",
            #         label_visibility="collapsed",
            #     )
            with ac:
                card_title("Idiosyncratic Returns Autocorrelation" if series_ui =="Idiosyncratic" else "Total Returns Autocorrelation")
            acf_series = "idio" if series_ui == "Idiosyncratic" else "total"
            acf_data   = build_acf_pacf(
                df_returns, df_loadings,
                series=acf_series, nlags=20,
            )
            fig_acf = plot_acf_pacf(acf_data)
            st.plotly_chart(
                fig_acf,
                use_container_width=True,
                config={"displayModeBar": False},
            )
