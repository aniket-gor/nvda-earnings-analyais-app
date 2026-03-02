# -*- coding: utf-8 -*-
"""
Created on Fri Feb 27 22:00:24 2026
@author: anike
"""

import streamlit as st
from config import THEME
from tabs.tab_fullperiod    import render as render_fullperiod
from tabs.tab_earnings      import render as render_earnings
from tabs.tab_predictability import render as render_predictability
from tabs.tab_dataexplorer  import render as render_dataexplorer

st.set_page_config(
    page_title="NVDA Earnings Dashboard",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Shorthand references ───────────────────────────────────────────────────
_bg_page       = THEME["bg_page"]
_bg_panel      = THEME["bg_panel"]
_primary       = THEME["primary"]
_neutral       = THEME["neutral"]
_text_primary  = THEME["text_primary"]
_text_muted    = THEME["text_muted"]
_border        = THEME["border_subtle"]
_grid          = THEME["grid"]
_shadow        = THEME["card_shadow"]
_radius        = THEME["border_radius"]
_font          = THEME["font_family"]
_sz_body       = THEME["font_size_body"]
_sz_caption    = THEME["font_size_caption"]
_space_xs      = THEME["space_xs"]
_space_sm      = THEME["space_sm"]
_space_md      = THEME["space_md"]
_selected_bg   = THEME["selected_bg"]
_selected_bdr  = THEME["selected_border"]

st.markdown(f"""
<style>

/* ── Page shell ──────────────────────────────────────────────────────────── */
[data-testid="collapsedControl"] {{ display: none; }}
[data-testid="stToolbar"]        {{ display: none; }}
[data-testid="stHeader"]         {{ display: none; }}
footer                           {{ visibility: hidden; }}
#MainMenu                        {{ visibility: hidden; }}

html, body, [data-testid="stAppViewContainer"] {{
    background-color: {_bg_page};
    font-family: {_font}, sans-serif;
    font-size: {_sz_body}px;
    color: {_text_primary};
}}

.block-container {{
    padding-top    : 0.75rem;
    padding-bottom : 0rem;
    padding-left   : {_space_md}px;
    padding-right  : {_space_md}px;
    max-width      : 100%;
}}

/* ── Tab bar ─────────────────────────────────────────────────────────────── */
.stTabs {{
    margin-top: -0.5rem;
}}
.stTabs [data-baseweb="tab-panel"] {{
    padding-top    : 0.5rem !important;
    padding-bottom : 0rem   !important;
}}
.stTabs [data-baseweb="tab"] {{
    font-family : {_font}, sans-serif;
    font-size   : {_sz_body}px;
    font-weight : 600;
    color       : {_text_muted};
    padding     : 6px 16px;
}}
.stTabs [aria-selected="true"] {{
    color              : {_primary}  !important;
    border-bottom-color: {_primary}  !important;
}}

/* ── Card — targets st.container(border=True) ────────────────────────────── */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    background    : {_bg_panel}  !important;
    border-radius : {_radius}px  !important;
    border        : 1px solid {_border} !important;
    box-shadow    : {_shadow}    !important;
    padding       : {_space_sm}px {_space_md}px !important;
    margin-bottom : {_space_sm}px !important;
}}

/* ── Expander (nav guide) ────────────────────────────────────────────────── */
div[data-testid="stExpander"] {{
    background    : {_bg_panel};
    border-radius : {_radius}px;
    border        : 1px solid {_border} !important;
    box-shadow    : none;
    margin-bottom : {_space_sm}px;
}}
div[data-testid="stExpander"] summary {{
    font-size   : {_sz_body}px;
    font-weight : 600;
    color       : {_text_primary};
    font-family : {_font}, sans-serif;
}}

/* ── Buttons (all tabs) ──────────────────────────────────────────────────── */
div[data-testid="stButton"] > button {{
    height        : 26px          !important;
    padding       : 0 {_space_sm}px !important;
    font-size     : {_sz_body}px  !important;
    font-weight   : 400           !important;
    font-family   : {_font}, sans-serif !important;
    line-height   : 1             !important;
    margin        : 0             !important;
    width         : 100%          !important;
    border-radius : {_radius}px   !important;
    color         : {_text_primary} !important;
    background    : {_bg_panel}   !important;
    border        : 1px solid {_border} !important;
    box-shadow    : none          !important;
    text-align    : center        !important;
    transition    : background 0.15s, color 0.15s;
}}


div[data-testid="stButton"] > button:hover {{
    background : {_selected_bg}  !important;
    color      : {_primary}      !important;
    border     : 1px solid {_selected_bdr} !important;
}}
div[data-testid="stButton"] {{ margin: 0 !important; }}

/* ── Drilldown table — borderless button variant ─────────────────────────── */
div[data-testid="stButton"].dd-btn > button {{
    border        : none !important;
    border-radius : 0    !important;
    background    : transparent !important;
    font-weight   : 400  !important;
    font-size     : {_sz_body}px !important;
}}
div[data-testid="stButton"].dd-btn > button:hover {{
    background : {_selected_bg} !important;
    color      : {_primary}     !important;
    border     : none           !important;
}}

/* ── Selectbox ───────────────────────────────────────────────────────────── */
div[data-testid="stSelectbox"] > div {{
    min-height  : 32px !important;
    font-size   : {_sz_body}px !important;
    font-family : {_font}, sans-serif !important;
}}

/* ── Radio ───────────────────────────────────────────────────────────────── */
div[data-testid="stRadio"] label {{
    font-size   : {_sz_body}px !important;
    font-family : {_font}, sans-serif !important;
    color       : {_text_primary} !important;
}}

/* ── Dataframe ───────────────────────────────────────────────────────────── */
div[data-testid="stDataFrame"] {{
    font-size   : {_sz_body}px !important;
    font-family : {_font}, sans-serif !important;
}}

/* ── Layout helpers ──────────────────────────────────────────────────────── */
div[data-testid="stHorizontalBlock"] {{
    align-items: flex-start !important;
}}
div[data-testid="stVerticalBlock"] > div {{
    gap: 0rem !important;
}}

/* ── Plotly containers ───────────────────────────────────────────────────── */
div[data-testid="stPlotlyChart"]       {{ height: 100% !important; }}
div[data-testid="stPlotlyChart"] > div {{ height: 100% !important; }}

/* ── Plotly cursor ───────────────────────────────────────────────────────── */
.js-plotly-plot .plotly .cursor-crosshair {{ cursor: crosshair !important; }}
.js-plotly-plot .plotly .drag            {{ cursor: crosshair !important; }}

</style>
""", unsafe_allow_html=True)


# ── Tab shell ──────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "Full Period Analysis",
    "Earnings Events",
    "Predictability",
    "Data Explorer"
])

with tab1: render_fullperiod()
with tab2: render_earnings()
with tab3: render_predictability()
with tab4: render_dataexplorer()
