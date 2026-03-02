# -*- coding: utf-8 -*-
"""
Created on Fri Feb 27 23:43:44 2026

@author: anike
"""

import streamlit as st

st.set_page_config(layout="wide")

themes = {
    "Option A — MSCI Institutional": {
        "bg": "#F7F9FC", "primary": "#005EB8",
        "secondary": "#00A3E0", "accent": "#00B08B", "earnings": "#F4A100"
    },
    "Option B — Spotfire Modern": {
        "bg": "#F4F5F7", "primary": "#3F51B5",
        "secondary": "#FF9800", "accent": "#26A69A", "earnings": "#AB47BC"
    },
    "Option C — Factset Minimal": {
        "bg": "#FFFFFF", "primary": "#1A237E",
        "secondary": "#5C6BC0", "accent": "#00897B", "earnings": "#FF6F00"
    },
}

cols = st.columns(3)
for col, (name, t) in zip(cols, themes.items()):
    with col:
        st.markdown(f"**{name}**")
        st.markdown(f"""
        <div style='background:{t["bg"]};padding:16px;border-radius:6px;
                    border:1px solid #ddd;font-family:Arial;font-size:13px;'>
            <div style='color:{t["primary"]};font-weight:bold;
                        margin-bottom:6px;'>Total Return</div>
            <div style='color:{t["secondary"]};
                        margin-bottom:6px;'>Systematic Return</div>
            <div style='color:{t["accent"]};
                        margin-bottom:6px;'>Idiosyncratic Return</div>
            <div style='color:{t["earnings"]};
                        margin-bottom:6px;'>Earnings Date Marker</div>
            <hr style='border-color:#ddd;'>
            <div style='color:#333;'>CAGR: 94.2%</div>
            <div style='color:#333;'>Sharpe: 1.84</div>
            <div style='color:#333;'>Max DD: -35.1%</div>
        </div>
        """, unsafe_allow_html=True)
