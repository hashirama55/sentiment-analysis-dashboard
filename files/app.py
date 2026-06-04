import streamlit as st
from src.logic.data_loader import load_data
from src.ui.styles import apply_custom_styles
from src.ui.sidebar import render_sidebar
from src.ui.tabs.overview import render_overview_tab
from src.ui.tabs.intent import render_intent_tab
from src.ui.tabs.topic import render_topic_tab
from src.ui.tabs.trend import render_trend_tab
from src.ui.tabs.explorer import render_explorer_tab

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="NetOne Sentiment Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply Styles
apply_custom_styles()

# Load Data
df = load_data("data.xlsx")

# Render Sidebar
fdf, granularity = render_sidebar(df)

# Main Page Header
st.markdown("# 📊 NetOne Facebook Sentiment Dashboard")
st.markdown(f"*Analysing **{len(fdf):,}** comments · Shona + English + Slang pipeline*")
st.divider()

# Tabs Setup
TAB_OVERVIEW, TAB_INTENT, TAB_TOPIC, TAB_TREND, TAB_EXPLORER = st.tabs([
    "📈 Overview", "🎯 Complaint Detection", "🏷️ Topic Modeling", "🚨 Trend Monitoring", "💬 Explorer"
])

# Render Tabs
with TAB_OVERVIEW:
    render_overview_tab(fdf, granularity)

with TAB_INTENT:
    render_intent_tab(fdf, granularity)

with TAB_TOPIC:
    render_topic_tab(fdf, granularity)

with TAB_TREND:
    render_trend_tab(fdf, granularity)

with TAB_EXPLORER:
    render_explorer_tab(fdf)

# Footer
st.divider()
st.markdown("""<p style='text-align:center;color:#555;font-size:0.73rem;'>
    Pipeline: VADER + Shona/Slang lexicon · Rule-based intent classifier (complaint/praise/inquiry/spam) ·
    Keyword topic model (network/billing/roaming/support) · Spike detection: mean + 1.5σ threshold
</p>""", unsafe_allow_html=True)
