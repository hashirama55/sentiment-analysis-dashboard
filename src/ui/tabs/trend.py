import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def render_trend_tab(fdf, granularity="Month"):
    st.markdown('<p class="section-header">Daily Comment Volume with Spike Detection</p>', unsafe_allow_html=True)

    daily = fdf.groupby("DateOnly").agg(
        total=("Comment","count"),
        complaints=("intent", lambda x: (x=="complaint").sum()),
        negative=("sentiment", lambda x: (x=="negative").sum()),
        compound=("compound","mean"),
    ).reset_index()
    daily["DateOnly"] = pd.to_datetime(daily["DateOnly"])
    daily["complaint_rate"] = daily["complaints"] / daily["total"].clip(lower=1) * 100
    daily["neg_rate"]       = daily["negative"]   / daily["total"].clip(lower=1) * 100

    # Spike detection: days where complaint count > mean + 1.5*std
    mean_c = daily["complaints"].mean()
    std_c  = daily["complaints"].std()
    spike_threshold = mean_c + 1.5 * std_c
    daily["is_spike"] = daily["complaints"] > spike_threshold

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily["DateOnly"], y=daily["total"],
        mode="lines", name="Total Comments",
        line=dict(color="#a29bfe", width=1.5), fill="tozeroy",
        fillcolor="rgba(162,155,254,0.08)"
    ))
    fig.add_trace(go.Scatter(
        x=daily["DateOnly"], y=daily["complaints"],
        mode="lines", name="Complaints",
        line=dict(color="#ff6b6b", width=2)
    ))
    fig.add_trace(go.Scatter(
        x=daily["DateOnly"], y=daily["negative"],
        mode="lines", name="Negative",
        line=dict(color="#ffd166", width=1.5, dash="dot")
    ))
    # Spike markers
    spikes = daily[daily["is_spike"]]
    fig.add_trace(go.Scatter(
        x=spikes["DateOnly"], y=spikes["complaints"],
        mode="markers", name="Complaint Spike",
        marker=dict(color="#ff6b6b", size=10, symbol="star",
                    line=dict(color="#fff", width=1.5))
    ))
    fig.add_hline(y=spike_threshold, line_dash="dash",
                  line_color="rgba(255, 107, 107, 0.27)",
                  annotation_text=f"Spike threshold ({spike_threshold:.0f})",
                  annotation_font_color="#ff6b6b")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#ccd6f6", height=380, legend_title_text="",
        xaxis=dict(gridcolor="#2a2f45"), yaxis=dict(gridcolor="#2a2f45"),
        margin=dict(t=20,b=5,l=5,r=5)
    )
    st.plotly_chart(fig, use_container_width=True, key="trend_comment_volume")

    # Complaint rate line
    tr1, tr2 = st.columns(2)
    with tr1:
        st.markdown('<p class="section-header">Daily Complaint Rate (%)</p>', unsafe_allow_html=True)
        fig = px.area(daily, x="DateOnly", y="complaint_rate",
                      color_discrete_sequence=["#ff6b6b"])
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#ccd6f6", height=280, legend_title_text="",
                          xaxis=dict(gridcolor="#2a2f45"),
                          yaxis=dict(gridcolor="#2a2f45", title="Complaint %"),
                          margin=dict(t=5,b=5,l=5,r=5))
        st.plotly_chart(fig, use_container_width=True, key="trend_complaint_rate")

    with tr2:
        st.markdown('<p class="section-header">7-Day Rolling Avg Sentiment Score</p>', unsafe_allow_html=True)
        daily["rolling_compound"] = daily["compound"].rolling(7, min_periods=1).mean()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily["DateOnly"], y=daily["compound"],
                                 mode="lines", name="Daily",
                                 line=dict(color="#3a3f5c", width=1)))
        fig.add_trace(go.Scatter(x=daily["DateOnly"], y=daily["rolling_compound"],
                                 mode="lines", name="7-day avg",
                                 line=dict(color="#00d4aa", width=2.5)))
        fig.add_hline(y=0, line_dash="dash", line_color="#555")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#ccd6f6", height=280, legend_title_text="",
                          xaxis=dict(gridcolor="#2a2f45"),
                          yaxis=dict(gridcolor="#2a2f45", title="Avg Score"),
                          margin=dict(t=5,b=5,l=5,r=5))
        st.plotly_chart(fig, use_container_width=True, key="trend_rolling_avg")

    # Weekly topic heatmap
    st.markdown(f'<p class="section-header">{granularity}ly Topic Volume Heatmap (potential outage/campaign signals)</p>', unsafe_allow_html=True)
    date_col = "YearMonth" if granularity == "Month" else "Week"
    wt = fdf.groupby([date_col,"topic"]).size().reset_index(name="count")
    wt_pivot = wt.pivot(index="topic", columns=date_col, values="count").fillna(0)
    fig = go.Figure(go.Heatmap(
        z=wt_pivot.values,
        x=wt_pivot.columns.tolist(),
        y=wt_pivot.index.tolist(),
        colorscale=[[0,"#1e2130"],[0.4,"#a29bfe"],[1,"#ff6b6b"]],
        text=wt_pivot.values.astype(int), texttemplate="%{text}",
        showscale=True,
        colorbar=dict(title=dict(text="Comments", font=dict(color="#ccd6f6")),
                      tickfont=dict(color="#ccd6f6"))
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font_color="#ccd6f6", height=320,
                      xaxis=dict(tickangle=-45), margin=dict(t=5,b=5,l=5,r=5))
    st.plotly_chart(fig, use_container_width=True, key="trend_weekly_topic_heatmap")

    # Spike log
    st.markdown('<p class="section-header">🚨 Detected Complaint Spikes</p>', unsafe_allow_html=True)
    if len(spikes) == 0:
        st.success("No spikes detected in the current filtered date range.")
    else:
        for _, row in spikes.sort_values("DateOnly", ascending=False).iterrows():
            sample = fdf[
                (fdf["DateOnly"].astype(str) == str(row["DateOnly"].date())) &
                (fdf["intent"] == "complaint")
            ]["Comment"].head(2).tolist()
            sample_text = " · ".join([c[:80]+"…" for c in sample]) if sample else "—"
            top_topic = fdf[
                fdf["DateOnly"].astype(str) == str(row["DateOnly"].date())
            ]["topic"].value_counts().idxmax() if len(fdf[fdf["DateOnly"].astype(str)==str(row["DateOnly"].date())])>0 else "—"
            st.markdown(f"""<div class="spike-card">
                <span class="spike-date">📅 {row['DateOnly'].strftime('%d %b %Y')}</span>
                &nbsp;&nbsp;
                <span style="color:#ffd166;font-size:0.85rem;">
                    {int(row['total'])} comments &nbsp;·&nbsp;
                    {int(row['complaints'])} complaints ({row['complaint_rate']:.1f}%) &nbsp;·&nbsp;
                    avg score: {row['compound']:+.3f} &nbsp;·&nbsp;
                    top topic: <b>{top_topic}</b>
                </span>
                <div class="spike-desc">Sample: {sample_text}</div>
            </div>""", unsafe_allow_html=True)
