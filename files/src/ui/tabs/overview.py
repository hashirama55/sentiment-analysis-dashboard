import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import re
from collections import Counter
from src.ui.components import render_metric_card, generate_word_cloud
from src.constants import STOP_WORDS

def render_overview_tab(fdf, granularity="Month"):
    counts  = fdf["sentiment"].value_counts()
    pos, neg, neu = counts.get("positive",0), counts.get("negative",0), counts.get("neutral",0)
    total   = len(fdf)
    avg_sc  = fdf["compound"].mean() if total else 0

    k1,k2,k3,k4,k5 = st.columns(5)
    render_metric_card(k1, f"{total:,}",        "Total Comments",                        "#ccd6f6")
    render_metric_card(k2, f"{pos:,}",          f"😊 Positive ({pos/max(total,1)*100:.1f}%)", "#00d4aa")
    render_metric_card(k3, f"{neg:,}",          f"😞 Negative ({neg/max(total,1)*100:.1f}%)", "#ff6b6b")
    render_metric_card(k4, f"{neu:,}",          f"😐 Neutral ({neu/max(total,1)*100:.1f}%)",  "#ffd166")
    render_metric_card(k5, f"{avg_sc:+.3f}",    "Avg Sentiment Score",                   "#00d4aa" if avg_sc>=0 else "#ff6b6b")

    st.markdown("<br>", unsafe_allow_html=True)
    ca, cb = st.columns([1,2])
    with ca:
        st.markdown('<p class="section-header">Sentiment Distribution</p>', unsafe_allow_html=True)
        fig = px.pie(values=[pos,neg,neu], names=["Positive","Negative","Neutral"],
                     hole=0.55, color_discrete_sequence=["#00d4aa","#ff6b6b","#ffd166"])
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#ccd6f6", height=300, margin=dict(t=5,b=5,l=5,r=5),
                          legend=dict(orientation="h",y=-0.15))
        fig.update_traces(textfont_color="#ccd6f6")
        st.plotly_chart(fig, use_container_width=True, key="overview_sentiment_pie")

    with cb:
        st.markdown(f'<p class="section-header">{granularity}ly Sentiment Trend</p>', unsafe_allow_html=True)
        date_col = "YearMonth" if granularity == "Month" else "Week"
        trend = fdf.groupby([date_col,"sentiment"]).size().reset_index(name="count")
        fig = px.line(trend, x=date_col, y="count", color="sentiment", markers=True,
                      color_discrete_map={"positive":"#00d4aa","negative":"#ff6b6b","neutral":"#ffd166"})
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#ccd6f6", height=300, legend_title_text="",
                          xaxis=dict(gridcolor="#2a2f45", tickangle=-30, title=granularity),
                          yaxis=dict(gridcolor="#2a2f45"), margin=dict(t=5,b=5,l=5,r=5))
        st.plotly_chart(fig, use_container_width=True, key="overview_sentiment_trend")

    cc, cd = st.columns([2,1])
    with cc:
        st.markdown('<p class="section-header">Top 15 Posts by Volume (stacked sentiment)</p>', unsafe_allow_html=True)
        top15 = fdf.groupby("Post Title").size().nlargest(15).index.tolist()
        ts = fdf[fdf["Post Title"].isin(top15)].groupby(["Post Title","sentiment"]).size().reset_index(name="count")
        fig = px.bar(ts, x="count", y="Post Title", color="sentiment", orientation="h", barmode="stack",
                     color_discrete_map={"positive":"#00d4aa","negative":"#ff6b6b","neutral":"#ffd166"})
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#ccd6f6", height=400, yaxis=dict(autorange="reversed"),
                          xaxis=dict(gridcolor="#2a2f45"), legend_title_text="",
                          margin=dict(t=5,b=5,l=5,r=5))
        st.plotly_chart(fig, use_container_width=True, key="overview_top_posts_bar")

    with cd:
        st.markdown('<p class="section-header">Language Breakdown</p>', unsafe_allow_html=True)
        lc = fdf["language"].value_counts().reset_index()
        lc.columns = ["Language","Count"]
        fig = px.bar(lc, x="Count", y="Language", orientation="h",
                     color="Count", color_continuous_scale=["#252840","#a29bfe"])
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#ccd6f6", height=400, showlegend=False,
                          coloraxis_showscale=False, yaxis=dict(autorange="reversed"),
                          xaxis=dict(gridcolor="#2a2f45"), margin=dict(t=5,b=5,l=5,r=5))
        st.plotly_chart(fig, use_container_width=True, key="overview_lang_bar")

    # Heatmap
    ce, cf = st.columns([1,1])
    with ce:
        st.markdown('<p class="section-header">Activity Heatmap (Hour × Day)</p>', unsafe_allow_html=True)
        dow_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        hd = fdf.groupby(["DayOfWeek","Hour"]).size().reset_index(name="count")
        hp = hd.pivot(index="DayOfWeek", columns="Hour", values="count").fillna(0)
        hp = hp.reindex([d for d in dow_order if d in hp.index])
        fig = go.Figure(go.Heatmap(z=hp.values,
            x=[f"{h:02d}:00" for h in hp.columns], y=hp.index.tolist(),
            colorscale=[[0,"#1e2130"],[0.5,"#a29bfe"],[1,"#00d4aa"]], showscale=False))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#ccd6f6", height=320,
                          xaxis=dict(tickangle=-45), margin=dict(t=5,b=5,l=5,r=5))
        st.plotly_chart(fig, use_container_width=True, key="overview_activity_heatmap")

    with cf:
        st.markdown('<p class="section-header">Avg Sentiment Score by Post</p>', unsafe_allow_html=True)
        at = fdf.groupby("Post Title")["compound"].agg(["mean","count"]).reset_index()
        at.columns = ["Post Title","avg","n"]
        at = at[at["n"]>=5].nlargest(15,"n").sort_values("avg")
        at["color"] = at["avg"].apply(lambda x: "#00d4aa" if x>=0.05 else "#ff6b6b" if x<=-0.05 else "#ffd166")
        fig = go.Figure(go.Bar(x=at["avg"], y=at["Post Title"], orientation="h",
                               marker_color=at["color"].tolist(),
                               text=at["avg"].round(3), textposition="outside"))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#ccd6f6", height=400,
                          xaxis=dict(gridcolor="#2a2f45", zeroline=True, zerolinecolor="#555"),
                          margin=dict(t=5,b=5,l=5,r=50))
        st.plotly_chart(fig, use_container_width=True, key="overview_avg_sentiment_bar")

    st.markdown('<p class="section-header">Interactive General Word Cloud (All Topics)</p>', unsafe_allow_html=True)
    all_words = []
    for text in fdf["Comment"].dropna():
        for w in re.findall(r'\b[a-zA-Z]{3,}\b', str(text).lower()):
            if w not in STOP_WORDS:
                all_words.append(w)
    top_overall = Counter(all_words).most_common(50)
    if top_overall:
        fig_cloud = generate_word_cloud(top_overall, height=360)
        st.plotly_chart(fig_cloud, use_container_width=True, key="overview_word_cloud")
    else:
        st.info("No text data available to generate a word cloud.")
