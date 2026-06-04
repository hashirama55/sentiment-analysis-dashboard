import streamlit as st

def render_sidebar(df):
    st.sidebar.markdown("## 🔧 Filters")

    all_topics_list = sorted(df["Post Title"].astype(str).unique().tolist())
    selected_topics = st.sidebar.multiselect("Post / Topic", all_topics_list, default=[], placeholder="All topics")

    sentiments = st.sidebar.multiselect(
        "Sentiment", ["positive", "neutral", "negative"],
        default=["positive", "neutral", "negative"]
    )
    intents = st.sidebar.multiselect(
        "Intent", ["complaint", "praise", "inquiry", "spam"],
        default=["complaint", "praise", "inquiry", "spam"]
    )
    topics_filter = st.sidebar.multiselect(
        "Topic Category", ["network", "billing", "roaming", "support", "general"],
        default=["network", "billing", "roaming", "support", "general"]
    )
    languages = st.sidebar.multiselect(
        "Language", sorted(df["language"].unique().tolist()),
        default=sorted(df["language"].unique().tolist())
    )

    st.sidebar.divider()
    granularity = st.sidebar.radio("Time Granularity", ["Month", "Week"], index=0, horizontal=True)
    
    date_col = "YearMonth" if granularity == "Month" else "Week"
    time_options = sorted(df[date_col].unique().tolist())
    
    if len(time_options) > 1:
        t_start, t_end = st.sidebar.select_slider(
            f"Select {granularity} Range", 
            options=time_options, 
            value=(time_options[0], time_options[-1])
        )
    elif len(time_options) == 1:
        t_start = t_end = time_options[0]
        st.sidebar.info(f"Only one {granularity.lower()} available: {t_start}")
    else:
        t_start = t_end = None
        st.sidebar.warning(f"No data available for the selected granularity.")

    min_conf = st.sidebar.slider("Min. confidence %", 0, 100, 0, 5)

    # Apply filters
    fdf = df.copy()
    if selected_topics:  fdf = fdf[fdf["Post Title"].isin(selected_topics)]
    if sentiments:       fdf = fdf[fdf["sentiment"].isin(sentiments)]
    if intents:          fdf = fdf[fdf["intent"].isin(intents)]
    if topics_filter:    fdf = fdf[fdf["topic"].isin(topics_filter)]
    if languages:        fdf = fdf[fdf["language"].isin(languages)]
    
    if t_start and t_end:
        fdf = fdf[(fdf[date_col] >= t_start) & (fdf[date_col] <= t_end)]
        
    fdf = fdf[fdf["confidence"] >= min_conf]

    return fdf, granularity
