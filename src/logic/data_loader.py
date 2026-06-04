import pandas as pd
import streamlit as st
from src.logic.classifiers import score_comments_batch, classify_intent, classify_topic, detect_language
from src.constants import DEFAULT_CHUNK_SIZE, MAX_COMMENTS

@st.cache_data(show_spinner=False)
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Raw Data")
    df.columns = df.columns.str.strip()
    df = df.rename(columns={"Name (click to view profile)": "Name", "(view source)": "Source"})
    df["Post Title"] = df["Post Title"].astype(str).str.strip()
    df = df[df["Comment"].notna()].copy()
    df["Comment"] = df["Comment"].astype(str).str.strip()
    df = df[df["Comment"] != ""]
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df[df["Date"].notna()]
    
    # Filter for dates starting from 2026
    df = df[df["Date"].dt.year >= 2026].copy()
    
    # Sort and limit to avoid Streamlit Cloud timeouts
    df = df.sort_values("Date", ascending=False).head(MAX_COMMENTS).copy()

    df["YearMonth"] = df["Date"].dt.strftime("%Y-%m")
    df["DateOnly"]  = df["Date"].dt.date
    df["DayOfWeek"] = df["Date"].dt.day_name()
    df["Hour"]      = df["Date"].dt.hour
    df["Week"]      = df["Date"].dt.to_period("W").apply(lambda r: str(r.start_time.date()))
    
    # Process in chunks
    all_chunks = []
    num_chunks = (len(df) // DEFAULT_CHUNK_SIZE) + (1 if len(df) % DEFAULT_CHUNK_SIZE > 0 else 0)
    
    progress_container = st.empty()
    
    for i in range(0, len(df), DEFAULT_CHUNK_SIZE):
        chunk_idx = i // DEFAULT_CHUNK_SIZE
        chunk = df.iloc[i : i + DEFAULT_CHUNK_SIZE].copy()
        
        # Update progress UI
        progress_val = min((chunk_idx) / num_chunks, 1.0)
        percentage = int(progress_val * 100)
        with progress_container.container():
            st.markdown(f"### 🔄 Analysing comments... {percentage}%")
            st.progress(progress_val)
        
        # Sentiment (Batch)
        comments = chunk["Comment"].tolist()
        sentiment_res = score_comments_batch(comments)
        
        chunk["compound"]   = [r["compound"] for r in sentiment_res]
        chunk["sentiment"]  = [r["label"] for r in sentiment_res]
        chunk["confidence"] = [r["confidence"] for r in sentiment_res]
        
        # Other classifiers
        chunk["intent"] = chunk["Comment"].apply(classify_intent)
        chunk["topic"]  = chunk["Comment"].apply(classify_topic)
        chunk["language"] = chunk["Comment"].apply(detect_language)
        
        all_chunks.append(chunk)
        
    progress_container.empty()
    df = pd.concat(all_chunks)
    df["Likes"] = pd.to_numeric(df["Likes"], errors="coerce").fillna(0).astype(int)
    
    return df
