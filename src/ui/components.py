import math
import random
import plotly.graph_objects as go
import streamlit as st

def generate_word_cloud(words_freq, height=350):
    if not words_freq:
        return None
    
    max_freq = max(f for w, f in words_freq)
    min_freq = min(f for w, f in words_freq)
    freq_range = max_freq - min_freq if max_freq != min_freq else 1
    
    words = []
    x = []
    y = []
    sizes = []
    colors = []
    hovers = []
    
    palette = ["#00d4aa", "#ff6b6b", "#ffd166", "#74b9ff", "#a29bfe", "#fd79a8", "#55efc4", "#ffeaa7"]
    
    for i, (word, freq) in enumerate(words_freq):
        size = 12 + 38 * ((freq - min_freq) / freq_range)
        sizes.append(size)
        
        theta = i * 0.9
        r = 0.5 * math.sqrt(i)
        
        px = r * math.cos(theta) + random.uniform(-0.1, 0.1)
        py = r * math.sin(theta) + random.uniform(-0.1, 0.1)
        
        x.append(px)
        y.append(py)
        words.append(word)
        hovers.append(f"<b>{word}</b><br>Frequency: {freq}")
        colors.append(palette[i % len(palette)])
        
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode="text",
        text=words,
        hovertext=hovers,
        hoverinfo="text",
        textfont=dict(
            size=sizes,
            color=colors,
            family="Inter, sans-serif"
        )
    ))
    
    fig.update_layout(
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=5, b=5, l=5, r=5),
        height=height,
        showlegend=False
    )
    return fig

def render_metric_card(col, val, label, color):
    with col:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value" style="color:{color}">{val}</div>
            <div class="metric-label">{label}</div></div>""", unsafe_allow_html=True)
