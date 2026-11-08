"""SIP Explainer - AI-Native Mobile Application (Streamlit MVP).

Explains in plain English why a user's SIP value can sit below their invested
amount even when the fund itself is only slightly down.
"""

import json
from pathlib import Path
import time
import streamlit as st
import plotly.graph_objects as go

from core.compute import compute_sip, format_inr, format_pct
from core.static_data import (
    PARAG_PARIKH_DATA,
    AXIS_BLUECHIP_METADATA,
    FUND_HISTORY_HORIZONS,
    FUND_HISTORY_QUIZ,
    LEARN_GRAPH_ITEMS,
    FUND_HISTORY_TAKEAWAYS,
)
from core.gate import (
    generate_smart_digest_pipeline,
    process_question_pipeline,
    get_standard_digest_template,
)

# -----------------------------------------------------------------------------
# Streamlit Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SIP Explainer",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# -----------------------------------------------------------------------------
# Data Loader
# -----------------------------------------------------------------------------
@st.cache_data
def load_golden_set():
    path = Path(__file__).resolve().parent / "Evidence_Log" / "golden_set.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)

GOLDEN_SET = load_golden_set()
SCENARIOS = GOLDEN_SET["scenarios"]

# Default Base Scenario Calculation
BASE_AXIS_COMPUTE = compute_sip(
    SCENARIOS["base"]["monthly"],
    SCENARIOS["base"]["navs"],
    scenario_name="base"
)

# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------
if "screen" not in st.session_state:
    st.session_state["screen"] = "home"

if "history_stack" not in st.session_state:
    st.session_state["history_stack"] = ["home"]

if "selected_scenario" not in st.session_state:
    st.session_state["selected_scenario"] = "base"

if "quiz_selection" not in st.session_state:
    st.session_state["quiz_selection"] = None

if "history_horizon" not in st.session_state:
    st.session_state["history_horizon"] = "Since you started (7M)"

if "ai_vs_standard" not in st.session_state:
    st.session_state["ai_vs_standard"] = "AI"

if "smart_digest_cache" not in st.session_state:
    st.session_state["smart_digest_cache"] = {}

# -----------------------------------------------------------------------------
# Navigation Helpers
# -----------------------------------------------------------------------------
def navigate_to(screen_name: str):
    if st.session_state.get("screen") != screen_name:
        st.session_state["history_stack"].append(screen_name)
        st.session_state["screen"] = screen_name
        st.rerun()

def go_back(fallback: str = "home"):
    if len(st.session_state["history_stack"]) > 1:
        st.session_state["history_stack"].pop()
        st.session_state["screen"] = st.session_state["history_stack"][-1]
    else:
        st.session_state["screen"] = fallback
    st.rerun()

# -----------------------------------------------------------------------------
# Custom CSS for Mobile Fidelity & Chrome Removal
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* Hide Streamlit default UI elements */
    #MainMenu { display: none !important; }
    header[data-testid="stHeader"] { display: none !important; }
    footer { display: none !important; }
    div[data-testid="stDecoration"] { display: none !important; }
    div[data-testid="stToolbar"] { display: none !important; }
    .stDeployButton { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }

    /* Base page styling */
    .stApp {
        background-color: #F5F7FA;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Constrain app to mobile width ~420px */
    .block-container {
        max-width: 440px !important;
        padding-top: 1rem !important;
        padding-bottom: 5.5rem !important;
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
        margin: 0 auto !important;
    }

    /* Cards */
    .mobile-card {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 16px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
        margin-bottom: 14px;
    }

    .mint-card {
        background: #E6F8F3;
        border: 1px solid #A7F3D0;
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 14px;
    }

    .yellow-card {
        background: #FFF8E1;
        border: 1px solid #FDE68A;
        border-radius: 14px;
        padding: 14px;
        margin-bottom: 14px;
    }

    .navy-quiz-card {
        background: #1E1B4B;
        border-radius: 16px;
        padding: 18px;
        color: #FFFFFF;
        margin-bottom: 14px;
    }

    /* Gradient Portfolio Card */
    .portfolio-hero {
        background: linear-gradient(135deg, #064E3B 0%, #022C22 100%);
        border-radius: 20px;
        padding: 20px 18px;
        color: #FFFFFF;
        margin-bottom: 18px;
        position: relative;
        overflow: hidden;
    }

    .portfolio-hero::after {
        content: "";
        position: absolute;
        top: -40px;
        right: -40px;
        width: 160px;
        height: 160px;
        border-radius: 50%;
        border: 1px solid rgba(255, 255, 255, 0.1);
        pointer-events: none;
    }

    /* Pills & Badges */
    .pill-green {
        background-color: #DCFCE7;
        color: #00B386;
        font-size: 11px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 20px;
        display: inline-block;
    }

    .pill-red {
        background-color: #FEE2E2;
        color: #E5484D;
        font-size: 11px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 20px;
        display: inline-block;
    }

    .pill-neutral {
        background-color: #F1F5F9;
        color: #64748B;
        font-size: 11px;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 20px;
        display: inline-block;
    }

    .pill-indigo {
        background-color: #EEF2FF;
        color: #4F46E5;
        font-size: 11px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 20px;
        display: inline-block;
    }

    .pill-hero-gain {
        background: rgba(167, 243, 208, 0.2);
        color: #A7F3D0;
        border: 1px solid rgba(167, 243, 208, 0.3);
        font-size: 11px;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 20px;
        display: inline-block;
    }

    /* Red loss text rule */
    .loss-red {
        color: #E5484D !important;
        font-weight: 700;
    }
    .gain-green {
        color: #00B386 !important;
        font-weight: 700;
    }

    /* Top bar */
    .top-bar-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 14px;
        padding-top: 4px;
    }

    .avatar-circle {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        background-color: #00796B;
        color: #FFFFFF;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 13px;
    }

    /* Fixed Bottom Navigation */
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 100%;
        max-width: 440px;
        background: #FFFFFF;
        border-top: 1px solid #E2E8F0;
        display: flex;
        justify-content: space-around;
        padding: 8px 0 10px 0;
        z-index: 9999;
    }

    /* Streamlit button custom styling inside app */
    div.stButton > button {
        border-radius: 12px;
        font-weight: 600;
        border: 1px solid #E2E8F0;
        transition: all 0.15s ease-in-out;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# UI Header Components
# -----------------------------------------------------------------------------
def render_top_header(title: str, subtitle: str = "", show_back: bool = True, fallback_back: str = "home"):
    col_left, col_right = st.columns([0.82, 0.18])
    with col_left:
        sub_html = f"<div style='font-size: 12px; color: #64748B;'>{subtitle}</div>" if subtitle else ""
        if show_back:
            back_col, title_col = st.columns([0.15, 0.85])
            with back_col:
                if st.button("←", key=f"back_btn_{title}_{subtitle}", help="Go back"):
                    go_back(fallback_back)
            with title_col:
                st.markdown(f"<div style='font-size: 18px; font-weight: 700; color: #0F172A; line-height: 1.2;'>{title}</div>{sub_html}", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='font-size: 22px; font-weight: 800; color: #0F172A; line-height: 1.2;'>{title}</div>{sub_html}", unsafe_allow_html=True)
    with col_right:
        st.markdown("""
        <div style="display: flex; align-items: center; justify-content: flex-end; gap: 8px;">
            <span style="font-size: 18px; color: #64748B; cursor: pointer;">ⓘ</span>
            <div class="avatar-circle">RS</div>
        </div>
        """, unsafe_allow_html=True)

def render_segmented_toggle(active_tab: str):
    """Segmented toggle switch for My Investment | Fund History."""
    col1, col2 = st.columns(2)
    with col1:
        is_my_inv = (active_tab == "my_investment")
        if st.button("👤 My Investment", key="toggle_my_investment", use_container_width=True, type="primary" if is_my_inv else "secondary"):
            navigate_to("my_investment")
    with col2:
        is_hist = (active_tab == "fund_history")
        if st.button("📈 Fund History", key="toggle_fund_history", use_container_width=True, type="primary" if is_hist else "secondary"):
            navigate_to("fund_history")
    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

def render_bottom_navigation():
    """Persistent mobile bottom navigation bar."""
    curr = st.session_state.get("screen", "home")
    is_home_active = (curr == "home")
    is_sips_active = not is_home_active

    st.markdown("<div style='height: 35px;'></div>", unsafe_allow_html=True)
    nav_c1, nav_c2 = st.columns(2)
    with nav_c1:
        if st.button("🏠 Home", key="bnav_home", use_container_width=True, type="primary" if is_home_active else "secondary"):
            navigate_to("home")
    with nav_c2:
        if st.button("📊 My SIPs", key="bnav_sips", use_container_width=True, type="primary" if is_sips_active else "secondary"):
            navigate_to("my_sips")

def render_footer_disclaimer():
    st.markdown("""
    <div style="font-size: 11px; color: #94A3B8; text-align: center; margin-top: 18px; margin-bottom: 10px; line-height: 1.4;">
        Educational explanation, not investment advice. Mutual fund investments are subject to market risks. Read all scheme related documents carefully.
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# SCREEN 1: HOME
# =============================================================================
def render_screen_home():
    render_top_header("Hello!", "Here's how your SIPs are doing", show_back=False)

    # Home Portfolio Calculations
    tot_invested = BASE_AXIS_COMPUTE["invested"] + PARAG_PARIKH_DATA["invested"] # 35,000
    tot_value = BASE_AXIS_COMPUTE["value"] + PARAG_PARIKH_DATA["value"]         # 35,400
    tot_diff = tot_value - tot_invested                                          # +400
    tot_ret = round((tot_diff / tot_invested) * 100, 2)                          # +1.14%
    monthly_sip_tot = BASE_AXIS_COMPUTE["monthly"] + PARAG_PARIKH_DATA["monthly_amount"] # 5,000

    # Gradient Portfolio Card
    st.markdown(f"""
    <div class="portfolio-hero">
        <div style="font-size: 11px; font-weight: 700; letter-spacing: 0.5px; color: #A7F3D0; text-transform: uppercase;">
            TOTAL PORTFOLIO VALUE
        </div>
        <div style="display: flex; align-items: baseline; gap: 10px; margin-top: 4px; margin-bottom: 14px;">
            <span style="font-size: 32px; font-weight: 800; letter-spacing: -0.5px;">{format_inr(tot_value)}</span>
            <span class="pill-hero-gain">+{format_inr(tot_diff)} (+{tot_ret:.2f}%) overall</span>
        </div>
        <div style="border-top: 1px solid rgba(255, 255, 255, 0.15); margin-bottom: 14px;"></div>
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px;">
            <div>
                <div style="font-size: 11px; color: #A7F3D0;">Invested</div>
                <div style="font-size: 15px; font-weight: 700; color: #FFFFFF; margin-top: 2px;">{format_inr(tot_invested)}</div>
            </div>
            <div>
                <div style="font-size: 11px; color: #A7F3D0;">Active SIPs</div>
                <div style="font-size: 15px; font-weight: 700; color: #FFFFFF; margin-top: 2px;">2</div>
            </div>
            <div>
                <div style="font-size: 11px; color: #A7F3D0;">Monthly SIP</div>
                <div style="font-size: 15px; font-weight: 700; color: #FFFFFF; margin-top: 2px;">{format_inr(int(monthly_sip_tot))}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # THIS MONTH Section
    tm_col1, tm_col2 = st.columns([0.7, 0.3])
    with tm_col1:
        st.markdown("<div style='font-size: 12px; font-weight: 700; color: #0F172A; margin-bottom: 6px;'>● THIS MONTH</div>", unsafe_allow_html=True)
    with tm_col2:
        if st.button("View SIPs >", key="home_view_sips_link"):
            navigate_to("my_sips")

    st.markdown(f"""
    <div class="mobile-card" style="padding: 14px; display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="background-color: #E6F8F3; width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px;">
                📅
            </div>
            <div>
                <div style="font-size: 11px; color: #64748B;">Next investment</div>
                <div style="font-size: 15px; font-weight: 700; color: #0F172A;">{format_inr(int(monthly_sip_tot))} on 5 Dec</div>
                <div style="font-size: 11px; color: #64748B;">Across 2 active SIPs</div>
            </div>
        </div>
        <div style="color: #94A3B8; font-size: 18px; font-weight: bold;">›</div>
    </div>
    """, unsafe_allow_html=True)

    # YOUR FUNDS Section
    st.markdown("<div style='font-size: 12px; font-weight: 700; color: #0F172A; margin-top: 14px; margin-bottom: 6px;'>● YOUR FUNDS</div>", unsafe_allow_html=True)

    # Axis Bluechip Row
    ab_c1, ab_c2 = st.columns([0.75, 0.25])
    with ab_c1:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px; padding: 6px 0;">
            <div style="background-color: #FEE2E2; color: #E5484D; font-weight: 700; font-size: 13px; width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center;">
                AB
            </div>
            <div>
                <div style="font-size: 14px; font-weight: 700; color: #0F172A;">Axis Bluechip Fund</div>
                <div style="font-size: 12px; color: #64748B;">{format_inr(int(BASE_AXIS_COMPUTE['monthly']))} / month</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with ab_c2:
        st.markdown(f"""
        <div style="text-align: right; padding-top: 6px;">
            <div style="font-size: 14px; font-weight: 700; color: #0F172A;">{format_inr(BASE_AXIS_COMPUTE['value'])}</div>
            <div class="loss-red" style="font-size: 12px;">{BASE_AXIS_COMPUTE['return_pct']:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

    if st.button("Explore Axis Bluechip SIP →", key="btn_home_ab", use_container_width=True):
        navigate_to("sip_overview")

    st.markdown("<div style='border-top: 1px solid #E2E8F0; margin: 8px 0;'></div>", unsafe_allow_html=True)

    # Parag Parikh Row
    pp_c1, pp_c2 = st.columns([0.75, 0.25])
    with pp_c1:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px; padding: 6px 0;">
            <div style="background-color: #DCFCE7; color: #00B386; font-weight: 700; font-size: 13px; width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center;">
                PP
            </div>
            <div>
                <div style="font-size: 14px; font-weight: 700; color: #0F172A;">{PARAG_PARIKH_DATA['name']}</div>
                <div style="font-size: 12px; color: #64748B;">{format_inr(PARAG_PARIKH_DATA['monthly_amount'])} / month</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with pp_c2:
        st.markdown(f"""
        <div style="text-align: right; padding-top: 6px;">
            <div style="font-size: 14px; font-weight: 700; color: #0F172A;">{format_inr(PARAG_PARIKH_DATA['value'])}</div>
            <div class="gain-green" style="font-size: 12px;">+{PARAG_PARIKH_DATA['return_pct']:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

    if st.button("Explore Parag Parikh SIP →", key="btn_home_pp", use_container_width=True):
        navigate_to("my_sips")


# =============================================================================
# SCREEN 2: MY SIPs
# =============================================================================
def render_screen_my_sips():
    render_top_header("My SIPs", show_back=True, fallback_back="home")

    # Mint Explainer Card
    st.markdown("""
    <div class="mint-card">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
            <span style="font-size: 18px;">💡</span>
            <span style="font-size: 14px; font-weight: 700; color: #064E3B;">Fund Performance Explainer</span>
        </div>
        <div style="font-size: 12px; color: #064E3B; line-height: 1.45;">
            Confused by red or green numbers? Tap any SIP below to see plain-English explanations of your returns vs fund history.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Section Header
    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
        <span style="font-size: 12px; font-weight: 700; color: #64748B;">ACTIVE SIP INVESTMENTS (2)</span>
        <span class="pill-neutral">Tap to explore</span>
    </div>
    """, unsafe_allow_html=True)

    # 1. Axis Bluechip Fund Card
    st.markdown(f"""
    <div class="mobile-card" style="margin-bottom: 8px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div style="display: flex; gap: 10px;">
                <div style="background-color: #FEE2E2; color: #E5484D; font-weight: 700; font-size: 13px; width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center;">
                    AB
                </div>
                <div>
                    <div style="font-size: 15px; font-weight: 700; color: #0F172A;">Axis Bluechip Fund</div>
                    <div style="font-size: 12px; color: #64748B;">₹2,000 / month • <span style="color: #00B386; font-weight: 600;">Active SIP</span></div>
                    <div style="font-size: 11px; color: #94A3B8; margin-top: 2px;">Last instalment 5 Nov ✓ · Next 5 Dec</div>
                </div>
            </div>
            <div style="text-align: right;">
                <span class="pill-red">{format_inr(BASE_AXIS_COMPUTE['diff'])} ({BASE_AXIS_COMPUTE['return_pct']:.2f}%)</span>
                <div style="font-size: 10px; color: #94A3B8; margin-top: 3px;">Unrealised difference</div>
            </div>
        </div>
        <div style="background-color: #F8FAFC; border-radius: 10px; padding: 10px; margin-top: 12px; display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
            <div>
                <div style="font-size: 11px; color: #64748B;">Total Invested (7 mos)</div>
                <div style="font-size: 16px; font-weight: 700; color: #0F172A;">{format_inr(BASE_AXIS_COMPUTE['invested'])}</div>
            </div>
            <div>
                <div style="font-size: 11px; color: #64748B;">Current Portfolio Value</div>
                <div style="font-size: 16px; font-weight: 700; color: #0F172A;">{format_inr(BASE_AXIS_COMPUTE['value'])}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("ℹ See how your SIP works. Explain >", key="btn_explain_ab", use_container_width=True):
        navigate_to("sip_overview")

    st.markdown("<div style='margin-bottom: 14px;'></div>", unsafe_allow_html=True)

    # 2. Parag Parikh Flexi Cap Fund Card
    st.markdown(f"""
    <div class="mobile-card" style="margin-bottom: 8px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div style="display: flex; gap: 10px;">
                <div style="background-color: #DCFCE7; color: #00B386; font-weight: 700; font-size: 13px; width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center;">
                    PP
                </div>
                <div>
                    <div style="font-size: 15px; font-weight: 700; color: #0F172A;">{PARAG_PARIKH_DATA['name']}</div>
                    <div style="font-size: 12px; color: #64748B;">₹3,000 / month • <span style="color: #00B386; font-weight: 600;">Active SIP</span></div>
                    <div style="font-size: 11px; color: #94A3B8; margin-top: 2px;">{PARAG_PARIKH_DATA['schedule']}</div>
                </div>
            </div>
            <div style="text-align: right;">
                <span class="pill-green">{PARAG_PARIKH_DATA['pill_text']}</span>
                <div style="font-size: 10px; color: #94A3B8; margin-top: 3px;">{PARAG_PARIKH_DATA['tag']}</div>
            </div>
        </div>
        <div style="background-color: #F8FAFC; border-radius: 10px; padding: 10px; margin-top: 12px; display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
            <div>
                <div style="font-size: 11px; color: #64748B;">Total Invested (7 mos)</div>
                <div style="font-size: 16px; font-weight: 700; color: #0F172A;">{format_inr(PARAG_PARIKH_DATA['invested'])}</div>
            </div>
            <div>
                <div style="font-size: 11px; color: #64748B;">Current Portfolio Value</div>
                <div style="font-size: 16px; font-weight: 700; color: #0F172A;">{format_inr(PARAG_PARIKH_DATA['value'])}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("ℹ See how your SIP works. Explain >", key="btn_explain_pp", use_container_width=True):
        st.info("Detailed analysis is available for Axis Bluechip in this MVP.")

    st.markdown("""
    <div style="font-size: 11px; color: #64748B; text-align: center; margin-top: 12px;">
        ℹ Your return can differ from the fund's return because you invest every month.
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# SCREEN 3: SIP OVERVIEW
# =============================================================================
def render_screen_sip_overview():
    render_top_header("SIP Overview", "Axis Bluechip Fund", show_back=True, fallback_back="my_sips")

    data = BASE_AXIS_COMPUTE

    # Fund Summary Box
    st.markdown(f"""
    <div class="mobile-card">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
            <div style="background-color: #FEE2E2; color: #E5484D; font-weight: 700; font-size: 12px; width: 34px; height: 34px; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                AB
            </div>
            <div>
                <div style="font-size: 15px; font-weight: 700; color: #0F172A;">Axis Bluechip Fund</div>
                <div style="font-size: 11px; color: #64748B;">Monthly SIP: ₹2,000 • 7 instalments</div>
            </div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
            <div style="background-color: #F8FAFC; border-radius: 10px; padding: 10px;">
                <div style="font-size: 11px; color: #64748B;">Total Invested</div>
                <div style="font-size: 16px; font-weight: 700; color: #0F172A;">{format_inr(data['invested'])}</div>
            </div>
            <div style="background-color: #F8FAFC; border-radius: 10px; padding: 10px;">
                <div style="font-size: 11px; color: #64748B;">Current Portfolio Value</div>
                <div style="font-size: 16px; font-weight: 700; color: #0F172A;">{format_inr(data['value'])}</div>
            </div>
            <div style="background-color: #F8FAFC; border-radius: 10px; padding: 10px;">
                <div style="font-size: 11px; color: #64748B;">Absolute Difference</div>
                <div class="loss-red" style="font-size: 16px;">{format_inr(data['diff'])}</div>
            </div>
            <div style="background-color: #F8FAFC; border-radius: 10px; padding: 10px;">
                <div style="font-size: 11px; color: #64748B;">Return Percentage</div>
                <div class="loss-red" style="font-size: 16px;">{data['return_pct']:.2f}%</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Growth Curve Chart
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
        <span style="font-size: 13px; font-weight: 700; color: #0F172A;">Your 7-Month SIP Growth Curve</span>
        <span class="pill-neutral">7 monthly deposits</span>
    </div>
    """, unsafe_allow_html=True)

    fig = go.Figure()
    months = data["month_labels"] # M1 to M7

    # Invested Line (Grey)
    fig.add_trace(go.Scatter(
        x=months,
        y=data["month_end_invested"],
        mode="lines+markers",
        name=f"Invested ({format_inr(data['invested'])})",
        line=dict(color="#8A94A6", width=2.5),
        marker=dict(size=5, color="#8A94A6"),
    ))

    # Current Value Line (Blue)
    fig.add_trace(go.Scatter(
        x=months,
        y=data["month_end_values"],
        mode="lines+markers",
        name=f"Current Value ({format_inr(data['value'])})",
        line=dict(color="#2F5BEA", width=2.5),
        marker=dict(size=5, color="#2F5BEA"),
        fill='tonexty',
        fillcolor='rgba(47, 91, 234, 0.08)',
    ))

    fig.update_layout(
        height=220,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="center", x=0.5, font=dict(size=10)),
        xaxis=dict(showgrid=False, tickfont=dict(size=10, color="#64748B")),
        yaxis=dict(
            showgrid=True,
            gridcolor="#E2E8F0",
            gridwidth=1,
            griddash="dot",
            tickformat="₹~s",
            range=[0, 16000],
            tickfont=dict(size=10, color="#64748B"),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Yellow Info Card
    st.markdown(f"""
    <div class="yellow-card">
        <div style="display: flex; gap: 8px; align-items: flex-start;">
            <span style="font-size: 16px;">💡</span>
            <div>
                <div style="font-size: 13px; font-weight: 700; color: #92400E; margin-bottom: 4px;">
                    Why can your return differ from the fund's return?
                </div>
                <div style="font-size: 12px; color: #78350F; line-height: 1.45;">
                    A fund's return over a period assumes one lump sum on day 1. Your SIP bought units 7 separate times at 7 different prices, so your return can differ. Here, the fund is down <b>{data['fund_return_pct']:.2f}%</b> while your SIP is down <b>{abs(data['return_pct']):.2f}%</b>.
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Bifurcation Choices
    st.markdown("""
    <div style="margin-top: 14px; margin-bottom: 8px;">
        <div style="font-size: 12px; font-weight: 700; color: #0F172A;">CHOOSE WHAT YOU WANT TO UNDERSTAND</div>
        <div style="font-size: 11px; color: #64748B; margin-top: 2px;">
            Your personal money performance depends on your deposit dates, whereas the mutual fund's NAV shows overall market price history.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Choice 1: Analyse My Investment
    st.markdown("""
    <div class="mobile-card" style="border-left: 4px solid #4F46E5; margin-bottom: 10px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <div style="font-size: 14px; font-weight: 700; color: #0F172A;">1. Analyse My Investment</div>
            <span class="pill-indigo">Your Personal Money</span>
        </div>
        <div style="font-size: 12px; color: #64748B; line-height: 1.4; margin-bottom: 10px;">
            Understand how your actual cash contributions performed based on your deposit dates, 7 monthly instalments and annualised return.
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Analysis →", key="btn_open_analysis", use_container_width=True):
        navigate_to("my_investment")

    # Choice 2: Understand Fund History
    st.markdown("""
    <div class="mobile-card" style="border-left: 4px solid #00B386; margin-top: 10px; margin-bottom: 10px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <div style="font-size: 14px; font-weight: 700; color: #0F172A;">2. Understand Fund History</div>
            <span class="pill-green">Fund NAV History</span>
        </div>
        <div style="font-size: 12px; color: #64748B; line-height: 1.4; margin-bottom: 10px;">
            Examine how this mutual fund behaved since you started and across 1Y, 3Y and 5Y market cycles, completely separate from when you invested.
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open History →", key="btn_open_history", use_container_width=True):
        navigate_to("fund_history")


def extract_data_chips(text: str, computed: dict) -> list[str]:
    chips = []
    fmt = computed["formatted"]
    if fmt["invested"] in text:
        chips.append(f"Invested {fmt['invested']}")
    if fmt["value"] in text:
        chips.append(f"Current Value {fmt['value']}")
    if fmt["avg_cost"] in text:
        chips.append(f"Avg cost {fmt['avg_cost']}")
    if fmt["nav_now"] in text or fmt["nav_last"] in text:
        chips.append(f"NAV {fmt['nav_now']}")
    if fmt["units_total"] in text:
        chips.append(f"Units {fmt['units_total']}")
    if fmt["return_pct"] in text:
        chips.append(f"Return {fmt['return_pct']}")
    if not chips:
        chips = [f"Invested {fmt['invested']}", f"Avg cost {fmt['avg_cost']}", f"NAV {fmt['nav_now']}"]
    return chips[:4]


@st.fragment
def render_ask_card_fragment(data: dict):
    """Inline interactive Ask Card running inside st.fragment to eliminate page flicker."""
    if "ask_history" not in st.session_state:
        st.session_state["ask_history"] = []
    if "ask_pending_query" not in st.session_state:
        st.session_state["ask_pending_query"] = None

    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <div style="display: flex; align-items: center; gap: 6px;">
            <span style="font-size: 16px;">💬</span>
            <span style="font-size: 14px; font-weight: 700; color: #0F172A;">Ask about your SIP</span>
        </div>
        <span class="pill-green">AI ASSISTANT</span>
    </div>
    """, unsafe_allow_html=True)

    # 3 Suggested Quick Chips
    qc1, qc2, qc3 = st.columns(3)
    with qc1:
        if st.button("Why is SIP lower?", key="qc_why_lower", use_container_width=True):
            st.session_state["ask_pending_query"] = "Why is my SIP lower than the fund?"
            st.rerun(scope="fragment")
    with qc2:
        if st.button("What is avg cost?", key="qc_avg_cost", use_container_width=True):
            st.session_state["ask_pending_query"] = "What does average cost mean?"
            st.rerun(scope="fragment")
    with qc3:
        if st.button("Is my money gone?", key="qc_money_gone", use_container_width=True):
            st.session_state["ask_pending_query"] = "Is my money gone?"
            st.rerun(scope="fragment")

    # Input Form
    with st.form("inline_ask_form", clear_on_submit=True):
        f_col1, f_col2 = st.columns([0.83, 0.17])
        with f_col1:
            user_input = st.text_input(
                "Ask in your own words",
                placeholder="Ask in your own words...",
                label_visibility="collapsed",
                key="inline_ask_input"
            )
        with f_col2:
            submitted = st.form_submit_button("↑", type="primary")

        if submitted and user_input.strip():
            st.session_state["ask_pending_query"] = user_input.strip()
            st.rerun(scope="fragment")

    st.markdown("<div style='font-size: 10px; color: #94A3B8; margin-top: -6px; margin-bottom: 8px;'>Educational explanation, not investment advice.</div>", unsafe_allow_html=True)

    # Process pending query if triggered
    if st.session_state["ask_pending_query"]:
        q_text = st.session_state["ask_pending_query"]
        st.session_state["ask_pending_query"] = None

        with st.spinner("Checking numbers against your SIP data..."):
            is_expl = any(k in q_text.lower() for k in ["explain", "lower", "higher", "different", "why", "kyun"])
            res = process_question_pipeline(q_text, data, is_explanation=is_expl)
            chips = extract_data_chips(res["answer"], data)

            entry = {
                "id": str(time.time()),
                "question": q_text,
                "route": res["route"],
                "answer": res["answer"],
                "is_ai": res["is_ai"],
                "badge": res["badge"],
                "chips": chips,
                "fallback_used": res["fallback_used"]
            }
            st.session_state["ask_history"].append(entry)

    # Render History
    history = st.session_state["ask_history"]
    if history:
        latest = history[-1]

        # User Question Bubble
        st.markdown(f"""
        <div style="background-color: #F1F5F9; border-radius: 12px; padding: 10px 14px; margin-top: 6px; margin-bottom: 10px; color: #0F172A; font-weight: 600; font-size: 12px;">
            👤 {latest['question']}
        </div>
        """, unsafe_allow_html=True)

        # State 1: Answered (Verified or Fallback)
        if latest["route"] == "answer":
            if latest["fallback_used"]:
                st.markdown("""
                <div style="background-color: #FEF3C7; border: 1px solid #FDE68A; border-radius: 10px; padding: 8px 12px; font-size: 11px; color: #92400E; margin-bottom: 8px;">
                    We couldn't verify the generated answer, so here is our standard explanation.
                </div>
                """, unsafe_allow_html=True)

            chips_html = "".join([f"<span class='pill-neutral' style='font-size: 10px; margin-right: 4px;'>{c}</span>" for c in latest["chips"]])
            st.markdown(f"""
            <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px; margin-bottom: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.02);">
                <div style="font-size: 12px; color: #1E293B; line-height: 1.5; margin-bottom: 8px;">
                    {latest['answer']}
                </div>
                <div style="display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px;">
                    {chips_html}
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #F1F5F9; padding-top: 6px;">
                    <span style="font-size: 11px; font-weight: 600; color: #00796B;">✔ {latest['badge']}</span>
                    <span class="pill-neutral" style="font-size: 9px;">AI-generated explanation</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("How this was checked ▾"):
                st.markdown(r"""
                - **Check 1**: Valid JSON schema & route classification
                - **Check 2**: Zero bare digits outside `{placeholders}`
                - **Check 3**: All cited numbers match computed scenario data
                - **Check 4**: Zero financial advice phrases
                - **Check 5**: Zero panic / urgency wording
                - **Check 6**: Readability bounded (sentence $\le 22$ words, answer $\le 110$ words)
                - **Check 7**: Semantic relation verified by judge
                """)

            # Thumbs feedback & follow-up chips
            fb1, fb2, fb3 = st.columns([0.15, 0.15, 0.7])
            with fb1:
                if st.button("👍", key=f"thumb_up_{latest['id']}"):
                    st.toast("Thank you for your feedback!")
            with fb2:
                if st.button("👎", key=f"thumb_down_{latest['id']}"):
                    st.toast("Feedback recorded.")
            with fb3:
                pass

            st.markdown("<div style='font-size: 11px; font-weight: 700; color: #64748B; margin-top: 4px; margin-bottom: 4px;'>Suggested Follow-ups:</div>", unsafe_allow_html=True)
            fu_c1, fu_c2 = st.columns(2)
            with fu_c1:
                if st.button("Why more units last month?", key=f"fu_units_{latest['id']}", use_container_width=True):
                    st.session_state["ask_pending_query"] = "Why did I get more units last month?"
                    st.rerun(scope="fragment")
            with fu_c2:
                if st.button("What is average cost?", key=f"fu_rca_{latest['id']}", use_container_width=True):
                    st.session_state["ask_pending_query"] = "What does average cost mean?"
                    st.rerun(scope="fragment")

        # State 2: Advice Declined
        elif latest["route"] == "decline_advice":
            st.markdown(f"""
            <div style="background-color: #EEF2FF; border: 1px solid #C7D2FE; border-radius: 12px; padding: 14px; margin-bottom: 8px; color: #1E1B4B;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span style="font-weight: 700; font-size: 12px; color: #4F46E5;">Regulated Response</span>
                    <span class="pill-indigo" style="font-size: 9px;">Not answered: investment advice</span>
                </div>
                <div style="font-size: 12px; line-height: 1.5; color: #312E81;">
                    {latest['answer'].replace(chr(10), '<br>')}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # State 3: Prediction Declined
        elif latest["route"] == "decline_prediction":
            st.markdown(f"""
            <div style="background-color: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 12px; padding: 14px; margin-bottom: 8px; color: #334155;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span style="font-weight: 700; font-size: 12px; color: #475569;">Market Principles</span>
                    <span class="pill-neutral" style="font-size: 9px;">Not answered: price prediction</span>
                </div>
                <div style="font-size: 12px; line-height: 1.5; color: #334155;">
                    {latest['answer']}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # State 4: Not Sure
        elif latest["route"] == "not_sure":
            st.markdown(f"""
            <div style="background-color: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 12px; padding: 14px; margin-bottom: 8px; color: #475569;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span style="font-weight: 700; font-size: 12px; color: #64748B;">Data Boundary</span>
                    <span class="pill-neutral" style="font-size: 9px;">Not in your SIP data</span>
                </div>
                <div style="font-size: 12px; line-height: 1.5; color: #334155;">
                    {latest['answer']}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # State 5: Off-topic Redirect
        elif latest["route"] == "redirect_offtopic":
            st.markdown(f"""
            <div style="background-color: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 12px; padding: 12px; margin-bottom: 8px;">
                <div style="font-size: 12px; color: #475569; margin-bottom: 6px;">
                    {latest['answer']}
                </div>
                <span class="pill-neutral" style="font-size: 9px;">Off-topic redirect</span>
            </div>
            """, unsafe_allow_html=True)
            of1, of2 = st.columns(2)
            with of1:
                if st.button("Why is SIP lower?", key=f"of_why_{latest['id']}", use_container_width=True):
                    st.session_state["ask_pending_query"] = "Why is my SIP lower than the fund?"
                    st.rerun(scope="fragment")
            with of2:
                if st.button("What is average cost?", key=f"of_cost_{latest['id']}", use_container_width=True):
                    st.session_state["ask_pending_query"] = "What does average cost mean?"
                    st.rerun(scope="fragment")

        # Collapsed Earlier Questions Accordion
        if len(history) > 1:
            with st.expander(f"Earlier questions ({len(history) - 1})"):
                for idx, prev in enumerate(reversed(history[:-1])):
                    st.markdown(f"**Q: {prev['question']}**")
                    st.markdown(f"<div style='font-size: 11px; color: #475569; margin-bottom: 6px;'>{prev['answer'][:120]}...</div>", unsafe_allow_html=True)
                    st.markdown("<hr style='margin: 4px 0 8px 0;'>", unsafe_allow_html=True)


# =============================================================================
# SCREEN 4: MY INVESTMENT ANALYSIS (CORE AI SCREEN)
# =============================================================================
def render_screen_my_investment():
    render_top_header("My Investment Analysis", "Axis Bluechip Fund", show_back=True, fallback_back="sip_overview")
    render_segmented_toggle("my_investment")

    # Tester Mode Selector
    sc_keys = list(SCENARIOS.keys())
    selected_sc = st.selectbox(
        "Tester mode: try another sample SIP (this screen only)",
        sc_keys,
        index=sc_keys.index(st.session_state.get("selected_scenario", "base")),
        key="tester_mode_dropdown"
    )
    st.session_state["selected_scenario"] = selected_sc

    # Compute data for active scenario
    active_navs = SCENARIOS[selected_sc]["navs"]
    active_monthly = SCENARIOS[selected_sc]["monthly"]
    data = compute_sip(active_monthly, active_navs, scenario_name=selected_sc)

    # 1. SMART DIGEST GENERATION / RETRIEVAL
    mode = st.session_state.get("ai_vs_standard", "AI")
    
    # Session Caching for Smart Digest
    if selected_sc not in st.session_state["smart_digest_cache"]:
        with st.spinner("Generating verified Smart Digest..."):
            digest_data = generate_smart_digest_pipeline(data)
            st.session_state["smart_digest_cache"][selected_sc] = digest_data

    cached_digest = st.session_state["smart_digest_cache"][selected_sc]

    # Swap between AI and Standard if toggled
    if mode == "Standard":
        standard_text = get_standard_digest_template(data)
        display_what_happened = standard_text["what_happened"]
        display_what_explains = standard_text["what_explains"]
        display_what_to_understand = standard_text["what_to_understand"]
        digest_badge = "Standard explanation (not AI-generated)"
        digest_tag = "Standard template"
    else:
        display_what_happened = cached_digest["what_happened"]
        display_what_explains = cached_digest["what_explains"]
        display_what_to_understand = cached_digest["what_to_understand"]
        digest_badge = cached_digest["badge"]
        digest_tag = "• AI explanation"

    st.markdown(f"""
    <div class="mint-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 11px; font-weight: 700; color: #00796B;">SMART DIGEST <span class="pill-green" style="margin-left: 6px;">{digest_tag}</span></span>
            <span style="font-size: 11px; color: #00796B;">Updated Today</span>
        </div>
        <div style="font-size: 16px; font-weight: 800; color: #0F172A; margin-bottom: 10px;">
            What happened to your money
        </div>
        <div style="background-color: #FFFFFF; border-radius: 12px; padding: 12px; margin-bottom: 8px;">
            <div style="font-size: 13px; font-weight: 700; color: #0F172A; margin-bottom: 3px;">1. What happened?</div>
            <div style="font-size: 12px; color: #334155; line-height: 1.45;">
                {display_what_happened}
            </div>
        </div>
        <div style="background-color: #FFFFFF; border-radius: 12px; padding: 12px; margin-bottom: 8px;">
            <div style="font-size: 13px; font-weight: 700; color: #0F172A; margin-bottom: 3px;">2. What explains the observed movement?</div>
            <div style="font-size: 12px; color: #334155; line-height: 1.45;">
                {display_what_explains}
            </div>
        </div>
        <div style="background-color: #FFFFFF; border-radius: 12px; padding: 12px; margin-bottom: 8px;">
            <div style="font-size: 13px; font-weight: 700; color: #0F172A; margin-bottom: 3px;">3. What should the investor understand?</div>
            <div style="font-size: 12px; color: #334155; line-height: 1.45;">
                {display_what_to_understand}
            </div>
        </div>
        <div style="font-size: 11px; color: #00796B; margin-top: 6px; display: flex; align-items: center; gap: 4px;">
            <span>🛡</span> <span>Mutual fund values fluctuate daily with market conditions.</span>
        </div>
        <div style="font-size: 11px; font-weight: 600; color: #00796B; margin-top: 4px; display: flex; align-items: center; gap: 4px;">
            <span>✔</span> <span>{digest_badge}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. INLINE ASK ABOUT YOUR SIP CARD (st.fragment)
    st.markdown("<div class='mobile-card' style='padding: 14px;'>", unsafe_allow_html=True)
    render_ask_card_fragment(data)
    st.markdown("</div>", unsafe_allow_html=True)

    # 3. STAT CARDS (2x2 Grid)
    diff_class = "loss-red" if data['diff'] < 0 else "gain-green"
    st.markdown(f"""
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 14px;">
        <div class="mobile-card" style="margin-bottom: 0; padding: 12px;">
            <div style="font-size: 11px; color: #64748B;">Total Invested</div>
            <div style="font-size: 18px; font-weight: 800; color: #0F172A; margin-top: 2px;">{data['formatted']['invested']}</div>
            <div style="font-size: 11px; color: #94A3B8;">{data['formatted']['n_instalments']} instalments</div>
        </div>
        <div class="mobile-card" style="margin-bottom: 0; padding: 12px;">
            <div style="font-size: 11px; color: #64748B;">Current Value</div>
            <div style="font-size: 18px; font-weight: 800; color: #0F172A; margin-top: 2px;">{data['formatted']['value']}</div>
            <div style="font-size: 11px; color: #94A3B8;">{data['formatted']['units_total']} units × {data['formatted']['nav_now']}</div>
        </div>
        <div class="mobile-card" style="margin-bottom: 0; padding: 12px;">
            <div style="font-size: 11px; color: #64748B;">Total Difference</div>
            <div class="{diff_class}" style="font-size: 18px; margin-top: 2px;">{data['formatted']['diff']}</div>
            <div style="font-size: 11px; color: #94A3B8;">{data['formatted']['return_pct']} absolute</div>
        </div>
        <div class="mobile-card" style="margin-bottom: 0; padding: 12px;">
            <div style="font-size: 11px; color: #64748B;">Avg cost vs current NAV</div>
            <div style="font-size: 18px; font-weight: 800; color: #0F172A; margin-top: 2px;">{data['formatted']['avg_cost']} vs {data['formatted']['nav_now']}</div>
            <div style="font-size: 11px; color: #94A3B8;">Purchase avg vs today</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. CHART: "Your SIP so far"
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
        <span style="font-size: 14px; font-weight: 700; color: #0F172A;">Your SIP so far</span>
        <span class="pill-neutral">{data['formatted']['monthly']} / mo</span>
    </div>
    <div style="font-size: 11px; color: #64748B; margin-bottom: 6px;">
        Your value was above your invested amount until September and fell below it from October, as NAV dropped from ₹55.00 in August to ₹44.75 in November.
    </div>
    """, unsafe_allow_html=True)

    chart_fig = go.Figure()
    chart_months = data["month_labels"]

    # Invested Line
    chart_fig.add_trace(go.Scatter(
        x=chart_months,
        y=data["month_end_invested"],
        mode="lines",
        name=f"Total Invested {data['formatted']['invested']}",
        line=dict(color="#8A94A6", width=2.5),
    ))

    # Value Line
    chart_fig.add_trace(go.Scatter(
        x=chart_months,
        y=data["month_end_values"],
        mode="lines",
        name=f"Current Value {data['formatted']['value']}",
        line=dict(color="#2F5BEA", width=2.5),
    ))

    # Add peak annotation if base
    is_base = (selected_sc == "base")
    if is_base:
        chart_fig.add_annotation(
            x="M4", y=8421,
            text="+₹420 above invested",
            showarrow=True,
            arrowhead=2,
            arrowcolor="#2F5BEA",
            font=dict(size=9, color="#FFFFFF"),
            bgcolor="#2F5BEA",
            borderpad=3,
            ax=0, ay=-25
        )
        chart_fig.add_annotation(
            x="M7", y=12300,
            text="₹1,700 below invested",
            showarrow=True,
            arrowhead=2,
            arrowcolor="#E5484D",
            font=dict(size=9, color="#FFFFFF"),
            bgcolor="#E5484D",
            borderpad=3,
            ax=0, ay=25
        )

    chart_fig.update_layout(
        height=220,
        margin=dict(l=10, r=10, t=20, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="center", x=0.5, font=dict(size=10)),
        xaxis=dict(showgrid=False, tickfont=dict(size=10, color="#64748B")),
        yaxis=dict(showgrid=True, gridcolor="#E2E8F0", griddash="dot", tickformat="₹~s", tickfont=dict(size=10, color="#64748B")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(chart_fig, use_container_width=True, config={"displayModeBar": False})

    # Sub-chart: Value minus invested
    bar_fig = go.Figure()
    bar_colors = ["#2F5BEA" if g >= 0 else "#E5484D" for g in data["gap_per_month"]]
    bar_fig.add_trace(go.Bar(
        x=chart_months,
        y=data["gap_per_month"],
        marker_color=bar_colors,
        name="Value minus invested"
    ))
    bar_fig.update_layout(
        height=130,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(showgrid=False, tickfont=dict(size=9, color="#64748B")),
        yaxis=dict(showgrid=True, gridcolor="#E2E8F0", griddash="dot", tickfont=dict(size=9, color="#64748B")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False
    )
    st.markdown("<div style='font-size: 11px; font-weight: 700; color: #0F172A;'>Value minus invested <span style='font-weight: normal; color: #64748B;'>(Delta per month)</span></div>", unsafe_allow_html=True)
    st.plotly_chart(bar_fig, use_container_width=True, config={"displayModeBar": False})

    # Note below bar chart
    max_m = data["month_with_most_units"]
    st.markdown(f"""
    <div style="background-color: #F1F5F9; border-radius: 8px; padding: 8px 12px; font-size: 11px; color: #334155; margin-bottom: 14px;">
        💡 <b>Month {max_m['month_number']} (NAV ₹{max_m['nav']:.2f}):</b> your {data['formatted']['monthly']} bought <b>{max_m['units']:.2f} units</b>, the most of any month so far.
    </div>
    """, unsafe_allow_html=True)

    # 5. TIMELINE BREAKDOWN
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
        <span style="font-size: 14px; font-weight: 700; color: #0F172A;">Timeline Breakdown</span>
        <span class="pill-neutral">7 Months</span>
    </div>
    <div style="font-size: 11px; color: #64748B; margin-bottom: 8px;">
        How NAV movements and unit purchases reconciled across 7 months
    </div>
    """, unsafe_allow_html=True)

    if is_base:
        st.markdown("""
        <div class="mobile-card" style="padding: 12px; margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <span style="font-size: 13px; font-weight: 700; color: #0F172A;">Months 1-4 <span style="font-weight: normal; color: #64748B; font-size: 11px;">May-Aug 2023</span></span>
                <span class="pill-green">+5.25% (Your value)</span>
            </div>
            <div style="font-size: 11px; color: #475569;">NAV rose from ₹48.50 to ₹55.00 (+13.4%). Invested ₹8,000, value ₹8,420.</div>
        </div>
        <div class="mobile-card" style="padding: 12px; margin-bottom: 14px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <span style="font-size: 13px; font-weight: 700; color: #0F172A;">Months 5-7 <span style="font-weight: normal; color: #64748B; font-size: 11px;">Sep-Nov 2023</span></span>
                <span class="pill-red">-12.14% (Your value)</span>
            </div>
            <div style="font-size: 11px; color: #475569;">NAV fell from ₹55.00 to ₹44.75 (-18.6%). Invested ₹14,000, value ₹12,300.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Compact table for non-base scenarios
        table_html = "<table style='width: 100%; font-size: 11px; text-align: left; border-collapse: collapse; margin-bottom: 14px;'>"
        table_html += "<tr style='background: #F1F5F9; border-bottom: 1px solid #CBD5E1;'><th style='padding: 6px;'>Month</th><th style='padding: 6px;'>NAV</th><th style='padding: 6px;'>Units</th><th style='padding: 6px;'>Value</th></tr>"
        for i in range(data["n_instalments"]):
            bg = "#FEF3C7" if (i + 1 == max_m["month_number"]) else "#FFFFFF"
            table_html += f"<tr style='background: {bg}; border-bottom: 1px solid #E2E8F0;'><td style='padding: 6px;'>M{i+1}</td><td style='padding: 6px;'>₹{active_navs[i]:.2f}</td><td style='padding: 6px;'>{data['units_per_instalment'][i]:.2f}</td><td style='padding: 6px;'>{format_inr(data['month_end_values'][i])}</td></tr>"
        table_html += "</table>"
        st.markdown(table_html, unsafe_allow_html=True)

    # 6. INVESTOR FUNDAMENTALS (5 Expanders)
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
        <span style="font-size: 14px; font-weight: 700; color: #0F172A;">Investor Fundamentals</span>
        <span class="pill-neutral">5 core concepts</span>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("1. Invested Amount vs Current Value"):
        st.write(f"Invested amount is the cash deducted from your bank account: {data['formatted']['invested']} across {data['formatted']['n_instalments']} monthly instalments. Current value is your {data['formatted']['units_total']} units multiplied by today's NAV of {data['formatted']['nav_now']}, which is {data['formatted']['value']}. The difference reflects daily market movement, not fees or commission.")

    with st.expander("2. Unrealised Gain/Loss"):
        st.write("An unrealised difference is on paper only. It only becomes a permanent gain or loss if you redeem (sell) your units. As long as you remain invested, your unit count never drops, and future value depends on future NAV.")

    with st.expander("3. Understanding XIRR"):
        if data["n_instalments"] < 12:
            st.write("XIRR is an annualised return metric. An annualised number is shown only after 12 months because annualising a short holding period can produce extreme, misleading figures. Your personal return is shown as absolute difference (-12.14%).")
        else:
            st.write(f"For portfolios completing 12 or more instalments, annualised XIRR accounts for the exact dates of each contribution.")

    with st.expander("4. NAV Fluctuations & Unit Accumulation"):
        st.write("When NAV rises, your fixed monthly deposit buys fewer units. When NAV falls, your fixed monthly deposit buys more units (rupee-cost averaging). Over long market cycles, accumulating units at lower prices reduces your average cost per unit.")

    with st.expander("5. Personal SIP Return vs Fund Historical Return"):
        st.write("A fund factsheet reports point-to-point performance assuming a single lump-sum investment on day one. Your SIP return reflects the weighted average of multiple purchases across different price points. As a result, your personal return can be higher or lower than the fund's published return.")

    # 7. CORE TAKEAWAY CARD
    st.markdown("""
    <div style="background-color: #00796B; border-radius: 14px; padding: 16px; color: #FFFFFF; margin-top: 14px; margin-bottom: 14px;">
        <div style="display: flex; align-items: center; gap: 6px; font-weight: 700; font-size: 13px; color: #A7F3D0; margin-bottom: 6px;">
            <span>💡</span> <span>CORE TAKEAWAY</span>
        </div>
        <div style="font-size: 12px; line-height: 1.5; color: #F0FDF4;">
            Market movements naturally create phases where portfolio value sits above or below total contributions. Regular SIP investing focuses on accumulating units across varied market cycles without timing price levels.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 8. TRANSPARENCY EXPANDERS
    with st.expander("How we check this"):
        st.markdown(r"""
        **The 7-Step Eval Gate Pipeline (executed on every response):**
        1. **JSON & Route Validation**: Validates JSON formatting and permitted routing tags.
        2. **Digit Check**: Rejects any bare digits `0-9` outside of curly brace `{placeholders}`.
        3. **Hydration & Number Verification**: Ensures 100% of cited numbers exist in the computed data set.
        4. **Zero Investment Advice**: Scans against prohibited advice recommendations (`buy`, `sell`, `you should`).
        5. **Zero Fear/Urgency Terms**: Scans against sensationalised language (`panic`, `crash`, `danger`).
        6. **Readability Bounds**: Capped at $\le 22$ words per sentence and $\le 110$ words total.
        7. **Semantic Relation Judge**: LLM evaluation at temperature 0.0 confirming return relation matches code.

        **Fallback Policy:**
        If generated text fails any check, the prompt is automatically retried once with the failure reason. If it fails a second time, a verified, deterministic template is served with the badge `"Standard explanation (not AI-generated)"`.
        """)

    with st.expander("What AI adds vs a standard explanation"):
        st.write("A fixed template only covers pre-scripted conditions. Generative AI allows explanations to adapt dynamically to unique deposit histories, volatile fluctuations, and free-form investor questions while maintaining 100% mathematical precision via code placeholders.")
        chosen_mode = st.radio(
            "Toggle explanation mode for Smart Digest:",
            ["AI Explanation", "Standard Template"],
            index=0 if st.session_state.get("ai_vs_standard", "AI") == "AI" else 1,
            key="toggle_digest_mode_radio"
        )
        new_mode = "AI" if chosen_mode == "AI Explanation" else "Standard"
        if new_mode != st.session_state.get("ai_vs_standard", "AI"):
            st.session_state["ai_vs_standard"] = new_mode
            st.rerun()


# =============================================================================
# SCREEN 5: FUND HISTORY (STATIC SCREEN, ZERO AI)
# =============================================================================
def render_screen_fund_history():
    render_top_header("Fund Historical Performance", "Axis Bluechip Fund", show_back=True, fallback_back="sip_overview")
    render_segmented_toggle("fund_history")

    # Intro Mint Card (Notice: NO CRISIL badge!)
    st.markdown("""
    <div class="mint-card">
        <div style="font-size: 11px; font-weight: 700; color: #00796B; letter-spacing: 0.5px; text-transform: uppercase;">
            FUND-LEVEL HISTORICAL NAV
        </div>
        <div style="font-size: 16px; font-weight: 800; color: #0F172A; margin-top: 2px; margin-bottom: 4px;">
            Axis Bluechip Fund History
        </div>
        <div style="font-size: 12px; color: #064E3B; line-height: 1.45;">
            Analysing the mutual fund's unit price (NAV) across market cycles, completely independent of your personal instalment dates.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Horizon Selector Chips
    horizons = ["Since you started (7M)", "1Y", "3Y", "5Y"]
    selected_horizon_tab = st.radio(
        "Select Historical Horizon:",
        horizons,
        index=horizons.index(st.session_state.get("history_horizon", "Since you started (7M)")),
        horizontal=True,
        key="history_horizon_radio"
    )
    st.session_state["history_horizon"] = selected_horizon_tab

    # Map radio choice to data key
    key_map = {"Since you started (7M)": "7M", "1Y": "1Y", "3Y": "3Y", "5Y": "5Y"}
    h_data = FUND_HISTORY_HORIZONS[key_map[selected_horizon_tab]]

    # Graph Inspector Header
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; margin-bottom: 4px;">
        <span style="font-size: 14px; font-weight: 700; color: #0F172A;">{h_data['window_name']}</span>
        <span class="pill-indigo" style="font-size: 10px;">👆 Tap points to inspect</span>
    </div>
    """, unsafe_allow_html=True)

    # Plotly Green NAV Curve
    h_fig = go.Figure()
    x_pts = [p["date"] for p in h_data["points"]]
    y_pts = [p["nav"] for p in h_data["points"]]

    h_fig.add_trace(go.Scatter(
        x=x_pts,
        y=y_pts,
        mode="lines+markers",
        line=dict(color="#00B386", width=2.5),
        marker=dict(size=7, color="#00B386"),
        fill='tozeroy',
        fillcolor='rgba(0, 179, 134, 0.12)',
    ))

    # Add peak label if present
    for p in h_data["points"]:
        if "Peak" in p["label"]:
            h_fig.add_annotation(
                x=p["date"], y=p["nav"],
                text=p["label"],
                showarrow=True,
                arrowhead=2,
                arrowcolor="#00B386",
                font=dict(size=9, color="#00796B"),
                bgcolor="#E6F8F3",
                borderpad=3,
                ax=0, ay=-20
            )

    h_fig.update_layout(
        height=200,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(showgrid=False, tickfont=dict(size=10, color="#64748B")),
        yaxis=dict(showgrid=True, gridcolor="#E2E8F0", griddash="dot", tickformat="₹.1f", tickfont=dict(size=10, color="#64748B")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    st.plotly_chart(h_fig, use_container_width=True, config={"displayModeBar": False})

    # Rally and Dip Highlight Buttons
    btn1, btn2 = h_data["buttons"][0], h_data["buttons"][1]
    st.markdown(f"""
    <div style="background-color: #E6F8F3; border-radius: 10px; padding: 10px; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div style="font-size: 13px; font-weight: 700; color: #00796B;">{btn1['label']}</div>
            <div style="font-size: 11px; color: #064E3B;">{btn1['desc']}</div>
        </div>
        <span style="font-size: 14px; color: #00796B;">→</span>
    </div>
    <div style="background-color: #FEE2E2; border-radius: 10px; padding: 10px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div style="font-size: 13px; font-weight: 700; color: #E5484D;">{btn2['label']}</div>
            <div style="font-size: 11px; color: #991B1B;">{btn2['desc']}</div>
        </div>
        <span style="font-size: 14px; color: #E5484D;">→</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background-color: #F1F5F9; border-radius: 8px; padding: 8px 10px; font-size: 11px; color: #475569; margin-bottom: 14px;">
        👆 <b>Interactive Graph Inspector:</b> Tap any point or use the buttons above to see how NAV reacted during specific periods.
    </div>
    """, unsafe_allow_html=True)

    # Fund History Summary (Clean text, ZERO AI badges)
    st.markdown(f"""
    <div class="mobile-card">
        <div style="font-size: 12px; font-weight: 700; color: #64748B; margin-bottom: 6px;">FUND HISTORY SUMMARY</div>
        <div style="font-size: 12px; color: #334155; line-height: 1.5;">
            {h_data['summary']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Disabled Ask Preview Card
    st.markdown("""
    <div class="mobile-card" style="opacity: 0.85;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div style="display: flex; align-items: center; gap: 6px;">
                <span style="font-size: 16px;">💬</span>
                <span style="font-size: 14px; font-weight: 700; color: #64748B;">Ask about this fund</span>
            </div>
            <span class="pill-neutral">Coming soon</span>
        </div>
        <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px;">
            <span class="pill-neutral">Why did NAV fall from Aug to Nov?</span>
            <span class="pill-neutral">What is drawdown?</span>
            <span class="pill-neutral">Does a falling NAV mean the fund is failing?</span>
        </div>
        <div style="background: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 10px; padding: 8px 12px; font-size: 11px; color: #94A3B8;">
            Available on My Investment Analysis. Coming here next.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Historical Behaviour Patterns
    st.markdown("<div style='font-size: 13px; font-weight: 700; color: #0F172A; margin-bottom: 8px;'>Historical Behaviour Patterns</div>", unsafe_allow_html=True)
    for p in h_data["patterns"]:
        icon_arrow = "↗" if p["type"] == "rally" else "↘"
        color = "#00B386" if p["type"] == "rally" else "#E5484D"
        st.markdown(f"""
        <div class="mobile-card" style="padding: 10px 14px; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 13px; font-weight: 700; color: {color};">{p['title']} <span style="font-weight: normal; color: #64748B; font-size: 11px;">({p['subtitle']})</span></div>
                <div style="font-size: 11px; color: #64748B; margin-top: 2px;">{p['note']}</div>
            </div>
            <div style="font-size: 18px; color: {color}; font-weight: bold;">{icon_arrow}</div>
        </div>
        """, unsafe_allow_html=True)

    # Fund Key Statistics (2x3 Grid)
    st.markdown("<div style='font-size: 13px; font-weight: 700; color: #0F172A; margin-top: 12px; margin-bottom: 8px;'>Fund Key Statistics</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 14px;">
        <div class="mobile-card" style="margin-bottom: 0; padding: 10px;">
            <div style="font-size: 11px; color: #64748B;">Starting NAV</div>
            <div style="font-size: 16px; font-weight: 700; color: #0F172A;">{h_data['stats']['start_nav']}</div>
            <div style="font-size: 10px; color: #94A3B8;">{h_data['stats']['start_nav_sub']}</div>
        </div>
        <div class="mobile-card" style="margin-bottom: 0; padding: 10px;">
            <div style="font-size: 11px; color: #64748B;">Current NAV</div>
            <div style="font-size: 16px; font-weight: 700; color: #0F172A;">{h_data['stats']['current_nav']}</div>
            <div style="font-size: 10px; color: #94A3B8;">{h_data['stats']['current_nav_sub']}</div>
        </div>
        <div class="mobile-card" style="margin-bottom: 0; padding: 10px;">
            <div style="font-size: 11px; color: #64748B;">Period Return</div>
            <div style="font-size: 16px; font-weight: 700; color: #0F172A;">{h_data['stats']['period_return']}</div>
            <div style="font-size: 10px; color: #94A3B8;">{h_data['stats']['period_return_sub']}</div>
        </div>
        <div class="mobile-card" style="margin-bottom: 0; padding: 10px;">
            <div style="font-size: 11px; color: #64748B;">Maximum Drawdown</div>
            <div class="loss-red" style="font-size: 16px;">{h_data['stats']['max_drawdown']}</div>
            <div style="font-size: 10px; color: #94A3B8;">{h_data['stats']['max_drawdown_sub']}</div>
        </div>
        <div class="mobile-card" style="margin-bottom: 0; padding: 10px;">
            <div style="font-size: 11px; color: #64748B;">Benchmark (Nifty 50)</div>
            <div style="font-size: 16px; font-weight: 700; color: #0F172A;">{h_data['stats']['benchmark']}</div>
            <div style="font-size: 10px; color: #94A3B8;">{h_data['stats']['benchmark_sub']}</div>
        </div>
        <div class="mobile-card" style="margin-bottom: 0; padding: 10px;">
            <div style="font-size: 11px; color: #64748B;">Risk Category</div>
            <div style="font-size: 16px; font-weight: 700; color: #EA580C;">🟠 {h_data['stats']['risk_category']}</div>
            <div style="font-size: 10px; color: #94A3B8;">{h_data['stats']['risk_sub']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Learn to Read This Graph
    st.markdown("<div style='font-size: 13px; font-weight: 700; color: #0F172A; margin-bottom: 8px;'>Learn to Read This Graph</div>", unsafe_allow_html=True)
    for item in LEARN_GRAPH_ITEMS:
        st.markdown(f"""
        <div class="mobile-card" style="padding: 12px; margin-bottom: 8px;">
            <div style="font-size: 13px; font-weight: 700; color: #0F172A; margin-bottom: 4px;">{item['q']}</div>
            <div style="font-size: 11px; color: #475569; line-height: 1.45;">{item['a']}</div>
        </div>
        """, unsafe_allow_html=True)

    # Interactive Navy Quiz Card
    st.markdown("""
    <div class="navy-quiz-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span class="pill-green" style="background-color: #00B386; color: #FFFFFF;">QUICK KNOWLEDGE CHECK</span>
            <span style="font-size: 11px; color: #A5B4FC;">1 of 1</span>
        </div>
        <div style="font-size: 14px; font-weight: 700; color: #FFFFFF; line-height: 1.4; margin-bottom: 12px;">
            A fund's NAV is down about 8% since you started, but your SIP is down about 12%. Why can this happen?
        </div>
    </div>
    """, unsafe_allow_html=True)

    quiz_opts = FUND_HISTORY_QUIZ["options"]
    chosen_opt = st.radio(
        "Choose your answer:",
        quiz_opts,
        index=quiz_opts.index(st.session_state["quiz_selection"]) if st.session_state.get("quiz_selection") in quiz_opts else 0,
        key="quiz_radio_input"
    )
    st.session_state["quiz_selection"] = chosen_opt

    if chosen_opt == quiz_opts[1]:
        st.markdown(f"""
        <div style="background-color: #064E3B; border-radius: 12px; padding: 12px; color: #FFFFFF; font-size: 12px; line-height: 1.4; margin-top: 8px; margin-bottom: 14px; border-left: 4px solid #00B386;">
            <b>✔ Correct!</b> {FUND_HISTORY_QUIZ['explanation']}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background-color: #312E81; border-radius: 12px; padding: 12px; color: #E0E7FF; font-size: 12px; line-height: 1.4; margin-top: 8px; margin-bottom: 14px; border-left: 4px solid #F59E0B;">
            <b>Review:</b> Option B is the accurate reason. {FUND_HISTORY_QUIZ['explanation']}
        </div>
        """, unsafe_allow_html=True)

    # What Have I Learned About This Fund
    st.markdown("""
    <div class="mobile-card">
        <div style="font-size: 13px; font-weight: 700; color: #0F172A; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
            <span>🎓</span> <span>WHAT HAVE I LEARNED ABOUT THIS FUND?</span>
        </div>
        <div style="font-size: 12px; color: #334155; line-height: 1.5;">
            • Fund NAV dropped -7.73% while your SIP dropped -12.14% due to higher mid-cycle acquisition prices.<br>
            • Rally and drawdown periods affect lumpsum returns differently than recurring monthly SIP purchases.<br>
            • <b>Key Rule:</b> Historical performance is useful for understanding past fund behaviour, but it does NOT guarantee future returns.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Action Buttons
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("← Back to My SIPs", key="fhist_to_sips", use_container_width=True):
            navigate_to("my_sips")
    with c_btn2:
        if st.button("Review SIP Overview →", key="fhist_to_overview", use_container_width=True):
            navigate_to("sip_overview")


# =============================================================================
# MAIN ROUTER
# =============================================================================
def main():
    current_screen = st.session_state.get("screen", "home")

    if current_screen == "home":
        render_screen_home()
    elif current_screen == "my_sips":
        render_screen_my_sips()
    elif current_screen == "sip_overview":
        render_screen_sip_overview()
    elif current_screen == "my_investment":
        render_screen_my_investment()
    elif current_screen == "fund_history":
        render_screen_fund_history()
    else:
        render_screen_home()

    render_footer_disclaimer()
    render_bottom_navigation()


if __name__ == "__main__":
    main()
