import streamlit as st
import os
import sys
import pandas as pd

# Ensure the root directory is in sys.path for absolute imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ui.styles import apply_custom_styles
from src.ui.sidebar import render_dataset_selector, render_sidebar_filters
from src.ui.tabs.overview import render_overview_tab
from src.ui.tabs.intent import render_intent_tab
from src.ui.tabs.topic import render_topic_tab
from src.ui.tabs.trend import render_trend_tab
from src.ui.tabs.explorer import render_explorer_tab

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Sentiment Analysis Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply Styles
apply_custom_styles()

# Render Dataset Selector in Sidebar
df, dataset_name, source_type = render_dataset_selector()

# Empty State / Landing Screen when no dataset is loaded
if df is None or len(df) == 0:
    st.markdown("# 📊 Sentiment Analysis Dashboard")
    st.markdown("*Upload a dataset to run multilingual sentiment, intent, and topic analysis.*")
    st.divider()

    st.info("👈 **Please upload a dataset using the sidebar on the left to begin analysis.**", icon="ℹ️")

    st.markdown("### 🚀 Dashboard Capabilities")
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            st.markdown("#### 💬 Multilingual Sentiment")
            st.caption("DistilBERT multilingual transformer combined with Shona, English, and slang lexicons to accurately score compound sentiment.")
    with c2:
        with st.container(border=True):
            st.markdown("#### 🎯 Intent & Topic Mining")
            st.caption("Automated classification of customer intent (complaints, praise, inquiries, spam) and keyword telecom topic detection.")
    with c3:
        with st.container(border=True):
            st.markdown("#### 🚨 Trend & Spike Alerts")
            st.caption("Daily and weekly timelines, 7-day rolling averages, and statistical spike detection (μ + 1.5σ) for rapid incident awareness.")

    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("#### 📋 Dataset Format Guidelines")
        st.markdown("""
        You can upload any **CSV** (`.csv`) or **Excel** (`.xlsx`, `.xls`) file.
        The system automatically detects columns, but you can also customize mappings in the sidebar.
        """)
        sample_guide = pd.DataFrame([
            {"Column": "Comment / Text *", "Status": "Required", "Description": "The text feedback, review, or comment to analyze", "Example": "NetOne 4G network was down today in Bulawayo"},
            {"Column": "Date", "Status": "Optional", "Description": "Timestamp for timeline trends & spike detection (auto-generated if omitted)", "Example": "2026-03-01 08:30:00"},
            {"Column": "Post Title / Category", "Status": "Optional", "Description": "Topic, campaign, channel, or post title", "Example": "Network Upgrade"},
            {"Column": "Likes / Score", "Status": "Optional", "Description": "Engagement or upvote count (defaults to 0)", "Example": "14"},
        ])
        st.dataframe(sample_guide, width="stretch", hide_index=True)

        col_sample_dl, col_default_switch = st.columns(2)
        with col_sample_dl:
            sample_template_path = os.path.join(os.path.dirname(__file__), "data", "sample_dataset_template.csv")
            if os.path.exists(sample_template_path):
                with open(sample_template_path, "rb") as f:
                    template_bytes = f.read()
                st.download_button(
                    label="Download Sample CSV Template",
                    data=template_bytes,
                    file_name="sample_dataset_template.csv",
                    mime="text/csv",
                    icon=":material/download:"
                )
        with col_default_switch:
            if st.button("Load Preloaded NetOne Dataset", type="primary", icon=":material/database:"):
                st.session_state.data_source_mode = "Default (NetOne)"
                st.rerun()

    st.stop()

# Render Filters in Sidebar
fdf, granularity = render_sidebar_filters(df, dataset_name)

# Main Page Header
if source_type == "default":
    st.markdown("# 📊 NetOne Facebook Sentiment Dashboard")
    st.markdown(f"*Analysing **{len(fdf):,}** of **{len(df):,}** comments · Multilingual Transformer + Shona/Slang Lexicon pipeline*")
else:
    st.markdown(f"# 📊 Sentiment Analysis Dashboard: {dataset_name}")
    st.markdown(f"*Analysing **{len(fdf):,}** of **{len(df):,}** comments from **{dataset_name}** · Multilingual Transformer + Lexicon pipeline*")

st.divider()

if len(fdf) == 0:
    st.warning("⚠️ No comments match the current filters. Please adjust your filter selections in the sidebar.")
else:
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
    Pipeline: DistilBERT Multilingual Transformer + Shona/Slang lexicon · Rule-based intent classifier (complaint/praise/inquiry/spam) ·
    Keyword topic model (network/billing/roaming/support) · Spike detection: mean + 1.5σ threshold
</p>""", unsafe_allow_html=True)
