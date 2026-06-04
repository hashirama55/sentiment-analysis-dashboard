import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from src.ui.components import render_metric_card

def render_intent_tab(fdf, granularity="Month"):
    ic = fdf["intent"].value_counts()
    total_i = len(fdf)
    i1,i2,i3,i4 = st.columns(4)
    intent_meta = [
        ("complaint","🚨","#ff6b6b"),("praise","🌟","#00d4aa"),
        ("inquiry","❓","#74b9ff"),("spam","🤖","#a29bfe"),
    ]
    for col,(intent,icon,color) in zip([i1,i2,i3,i4], intent_meta):
        v = ic.get(intent,0)
        render_metric_card(col, f"{v:,}", f"{icon} {intent.title()} ({v/max(total_i,1)*100:.1f}%)", color)

    st.markdown("<br>", unsafe_allow_html=True)
    ia, ib = st.columns([1,2])
    with ia:
        st.markdown('<p class="section-header">Intent Distribution</p>', unsafe_allow_html=True)
        fig = px.pie(
            values=list(ic.values), names=list(ic.index), hole=0.5,
            color_discrete_map={"complaint":"#ff6b6b","praise":"#00d4aa","inquiry":"#74b9ff","spam":"#a29bfe"})
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#ccd6f6", height=320,
                          legend=dict(orientation="h",y=-0.15), margin=dict(t=5,b=5,l=5,r=5))
        fig.update_traces(textfont_color="#ccd6f6")
        st.plotly_chart(fig, use_container_width=True, key="intent_distribution_pie")

    with ib:
        st.markdown(f'<p class="section-header">{granularity}ly Intent Trend</p>', unsafe_allow_html=True)
        date_col = "YearMonth" if granularity == "Month" else "Week"
        it = fdf.groupby([date_col,"intent"]).size().reset_index(name="count")
        fig = px.line(it, x=date_col, y="count", color="intent", markers=True,
                      color_discrete_map={"complaint":"#ff6b6b","praise":"#00d4aa","inquiry":"#74b9ff","spam":"#a29bfe"})
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#ccd6f6", height=280, legend_title_text="",
                          xaxis=dict(gridcolor="#2a2f45", tickangle=-30, title=granularity),
                          yaxis=dict(gridcolor="#2a2f45"), margin=dict(t=5,b=5,l=5,r=5))
        st.plotly_chart(fig, use_container_width=True, key="intent_trend_line")

    ic2, ic3 = st.columns(2)
    with ic2:
        st.markdown('<p class="section-header">Intent Mix per Top Post</p>', unsafe_allow_html=True)
        top10p = fdf.groupby("Post Title").size().nlargest(10).index.tolist()
        ip = fdf[fdf["Post Title"].isin(top10p)].groupby(["Post Title","intent"]).size().reset_index(name="count")
        fig = px.bar(ip, x="count", y="Post Title", color="intent", orientation="h", barmode="stack",
                     color_discrete_map={"complaint":"#ff6b6b","praise":"#00d4aa","inquiry":"#74b9ff","spam":"#a29bfe"})
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#ccd6f6", height=380, yaxis=dict(autorange="reversed"),
                          xaxis=dict(gridcolor="#2a2f45"), legend_title_text="",
                          margin=dict(t=5,b=5,l=5,r=5))
        st.plotly_chart(fig, use_container_width=True, key="intent_mix_bar")

    with ic3:
        st.markdown('<p class="section-header">Complaint Rate by Post (top 12)</p>', unsafe_allow_html=True)
        cr = fdf[fdf["Post Title"].isin(top10p)].copy()
        cr["is_complaint"] = (cr["intent"] == "complaint").astype(int)
        cr_rate = cr.groupby("Post Title").agg(
            total=("is_complaint","count"), complaints=("is_complaint","sum")
        ).reset_index()
        cr_rate["rate"] = cr_rate["complaints"] / cr_rate["total"] * 100
        cr_rate = cr_rate.sort_values("rate", ascending=True)
        fig = go.Figure(go.Bar(
            x=cr_rate["rate"], y=cr_rate["Post Title"], orientation="h",
            marker=dict(color=cr_rate["rate"],
                        colorscale=[[0,"#00d4aa"],[0.5,"#ffd166"],[1,"#ff6b6b"]],
                        showscale=True,
                        colorbar=dict(title=dict(text="%", font=dict(color="#ccd6f6")),
                                      tickfont=dict(color="#ccd6f6"))),
            text=cr_rate["rate"].round(1).astype(str)+"%", textposition="outside",
        ))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#ccd6f6", height=380,
                          xaxis=dict(gridcolor="#2a2f45", title="Complaint %"),
                          margin=dict(t=5,b=5,l=5,r=80))
        st.plotly_chart(fig, use_container_width=True, key="complaint_rate_bar")

    # Sentiment vs intent heatmap
    st.markdown('<p class="section-header">Sentiment × Intent Heatmap</p>', unsafe_allow_html=True)
    si_heat = fdf.groupby(["intent","sentiment"]).size().reset_index(name="count")
    si_pivot = si_heat.pivot(index="intent", columns="sentiment", values="count").fillna(0)
    fig = go.Figure(go.Heatmap(
        z=si_pivot.values, x=si_pivot.columns.tolist(), y=si_pivot.index.tolist(),
        colorscale=[[0,"#1e2130"],[0.5,"#a29bfe"],[1,"#00d4aa"]],
        text=si_pivot.values.astype(int), texttemplate="%{text}", showscale=False,
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font_color="#ccd6f6", height=280, margin=dict(t=5,b=5,l=5,r=5))
    st.plotly_chart(fig, use_container_width=True, key="sentiment_intent_heatmap")
