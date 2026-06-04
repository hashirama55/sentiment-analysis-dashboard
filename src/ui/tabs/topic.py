import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import re
from collections import Counter
from src.ui.components import render_metric_card, generate_word_cloud
from src.constants import STOP_WORDS

def render_topic_tab(fdf, granularity="Month"):
    tc = fdf["topic"].value_counts()
    topic_meta = [
        ("network","📡","#fd79a8"),("billing","💰","#ffeaa7"),
        ("roaming","✈️","#55efc4"),("support","🎧","#74b9ff"),("general","📋","#8892b0"),
    ]
    cols_t = st.columns(5)
    for col,(topic,icon,color) in zip(cols_t, topic_meta):
        v = tc.get(topic,0)
        render_metric_card(col, f"{v:,}", f"{icon} {topic.title()} ({v/max(len(fdf),1)*100:.1f}%)", color)

    st.markdown("<br>", unsafe_allow_html=True)
    ta, tb = st.columns([1,2])
    with ta:
        st.markdown('<p class="section-header">Topic Distribution</p>', unsafe_allow_html=True)
        topic_colors = {"network":"#fd79a8","billing":"#ffeaa7","roaming":"#55efc4",
                        "support":"#74b9ff","general":"#8892b0"}
        fig = px.pie(values=list(tc.values), names=list(tc.index), hole=0.5,
                     color_discrete_map=topic_colors)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#ccd6f6", height=300,
                          legend=dict(orientation="h",y=-0.15), margin=dict(t=5,b=5,l=5,r=5))
        fig.update_traces(textfont_color="#ccd6f6")
        st.plotly_chart(fig, use_container_width=True, key="topic_distribution_pie")

    with tb:
        st.markdown(f'<p class="section-header">{granularity}ly Topic Trend</p>', unsafe_allow_html=True)
        date_col = "YearMonth" if granularity == "Month" else "Week"
        tt = fdf.groupby([date_col,"topic"]).size().reset_index(name="count")
        fig = px.line(tt, x=date_col, y="count", color="topic", markers=True,
                      color_discrete_map=topic_colors)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#ccd6f6", height=300, legend_title_text="",
                          xaxis=dict(gridcolor="#2a2f45", tickangle=-30, title=granularity),
                          yaxis=dict(gridcolor="#2a2f45"), margin=dict(t=5,b=5,l=5,r=5))
        st.plotly_chart(fig, use_container_width=True, key="topic_trend_line")

    tc1, tc2 = st.columns(2)
    with tc1:
        st.markdown('<p class="section-header">Topic × Sentiment Breakdown</p>', unsafe_allow_html=True)
        ts_heat = fdf.groupby(["topic","sentiment"]).size().reset_index(name="count")
        ts_p = ts_heat.pivot(index="topic", columns="sentiment", values="count").fillna(0)
        fig = go.Figure(go.Heatmap(
            z=ts_p.values, x=ts_p.columns.tolist(), y=ts_p.index.tolist(),
            colorscale=[[0,"#1e2130"],[0.5,"#a29bfe"],[1,"#00d4aa"]],
            text=ts_p.values.astype(int), texttemplate="%{text}", showscale=False,
        ))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#ccd6f6", height=300, margin=dict(t=5,b=5,l=5,r=5))
        st.plotly_chart(fig, use_container_width=True, key="topic_sentiment_heatmap")

    with tc2:
        st.markdown('<p class="section-header">Topic × Intent (Complaints vs Praise)</p>', unsafe_allow_html=True)
        ti_data = fdf[fdf["intent"].isin(["complaint","praise"])].groupby(
            ["topic","intent"]).size().reset_index(name="count")
        fig = px.bar(ti_data, x="topic", y="count", color="intent", barmode="group",
                     color_discrete_map={"complaint":"#ff6b6b","praise":"#00d4aa"})
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#ccd6f6", height=300, legend_title_text="",
                          xaxis=dict(gridcolor="#2a2f45"), yaxis=dict(gridcolor="#2a2f45"),
                          margin=dict(t=5,b=5,l=5,r=5))
        st.plotly_chart(fig, use_container_width=True, key="topic_intent_bar")

    # Per-topic keyword drilldown
    st.markdown('<p class="section-header">Top Keywords per Topic</p>', unsafe_allow_html=True)
    tabs_topics = st.tabs(["📡 Network","💰 Billing","✈️ Roaming","🎧 Support","📋 General"])
    for tab, topic_name in zip(tabs_topics, ["network","billing","roaming","support","general"]):
        with tab:
            sub = fdf[fdf["topic"] == topic_name]
            words = []
            for text in sub["Comment"].dropna():
                for w in re.findall(r'\b[a-zA-Z]{3,}\b', str(text).lower()):
                    if w not in STOP_WORDS:
                        words.append(w)
            top_w = Counter(words).most_common(20)
            if top_w:
                wdf = pd.DataFrame(top_w, columns=["word","freq"])
                color = {"network":"#fd79a8","billing":"#ffeaa7","roaming":"#55efc4",
                         "support":"#74b9ff","general":"#8892b0"}[topic_name]
                
                col_bar, col_cloud = st.columns(2)
                with col_bar:
                    st.markdown("<p class='section-header' style='font-size:0.95rem;color:#8892b0;margin-bottom:8px;'>Keyword Frequency</p>", unsafe_allow_html=True)
                    fig = go.Figure(go.Bar(x=wdf["freq"], y=wdf["word"], orientation="h",
                                           marker_color=color))
                    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                      font_color="#ccd6f6", height=320,
                                      yaxis=dict(autorange="reversed"),
                                      xaxis=dict(gridcolor="#2a2f45"),
                                      margin=dict(t=5,b=5,l=5,r=5))
                    st.plotly_chart(fig, use_container_width=True, key=f"topic_keywords_{topic_name}")
                with col_cloud:
                    st.markdown("<p class='section-header' style='font-size:0.95rem;color:#8892b0;margin-bottom:8px;'>Topic Word Cloud</p>", unsafe_allow_html=True)
                    fig_cloud = generate_word_cloud(top_w, height=320)
                    st.plotly_chart(fig_cloud, use_container_width=True, key=f"topic_cloud_{topic_name}")
            else:
                st.info("No data for this topic in current filter.")
