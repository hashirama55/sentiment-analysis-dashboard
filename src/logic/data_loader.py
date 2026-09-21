import io
import os
import gc
import re
import pandas as pd
import streamlit as st
from src.logic.classifiers import score_comments_batch, classify_intent, classify_topic, detect_language
from src.constants import DEFAULT_CHUNK_SIZE, MAX_COMMENTS

def get_excel_sheet_names(file_bytes: bytes) -> list[str]:
    """Returns sheet names from an Excel file in bytes, or empty list if not valid Excel."""
    try:
        xl = pd.ExcelFile(io.BytesIO(file_bytes))
        return xl.sheet_names
    except Exception:
        return []

def read_raw_file(file_bytes: bytes, file_name: str, sheet_name: str | None = None, nrows: int | None = None) -> pd.DataFrame:
    """
    Reads an uploaded CSV or Excel file into a raw pandas DataFrame.
    Supports encodings like utf-8, latin1, utf-8-sig, cp1252 for CSVs.
    """
    lower_name = file_name.lower()
    if lower_name.endswith((".xlsx", ".xls")):
        # If no sheet name specified, try 'Raw Data' if present, otherwise sheet 0
        if not sheet_name:
            sheets = get_excel_sheet_names(file_bytes)
            sheet_name = "Raw Data" if "Raw Data" in sheets else 0
        df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name, nrows=nrows)
    else:
        # CSV parsing with fallback encodings
        encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252"]
        df = None
        for enc in encodings:
            try:
                df = pd.read_csv(io.BytesIO(file_bytes), nrows=nrows, encoding=enc)
                break
            except (UnicodeDecodeError, Exception):
                continue
        if df is None:
            # Final attempt letting pandas try
            df = pd.read_csv(io.BytesIO(file_bytes), nrows=nrows)

    # Clean whitespace in column names
    df.columns = [str(c).strip() for c in df.columns]
    return df

def detect_column_candidates(columns: list[str]) -> dict:
    """
    Auto-detects the most likely column mappings for an uploaded dataset.
    Returns dictionary with keys: 'text', 'date', 'title', 'likes'.
    """
    cols_lower = {col.lower(): col for col in columns}
    
    # 1. Text / Comment Column
    text_candidates = ["comment", "text", "review", "message", "body", "content", "feedback", "tweet", "post", "inquiry"]
    detected_text = None
    for cand in text_candidates:
        for c_low, orig in cols_lower.items():
            if cand in c_low:
                detected_text = orig
                break
        if detected_text:
            break
    if not detected_text and columns:
        detected_text = columns[0]

    # 2. Date Column
    date_candidates = ["date", "time", "created", "timestamp", "datetime", "published"]
    detected_date = None
    for cand in date_candidates:
        for c_low, orig in cols_lower.items():
            if cand in c_low:
                detected_date = orig
                break
        if detected_date:
            break

    # 3. Post Title / Category Column
    title_candidates = ["post title", "post", "title", "category", "topic", "channel", "group", "subject"]
    detected_title = None
    for cand in title_candidates:
        for c_low, orig in cols_lower.items():
            if cand in c_low and orig != detected_text and orig != detected_date:
                detected_title = orig
                break
        if detected_title:
            break

    # 4. Likes Column
    likes_candidates = ["likes", "like", "upvotes", "upvote", "score", "stars", "rating"]
    detected_likes = None
    for cand in likes_candidates:
        for c_low, orig in cols_lower.items():
            if cand in c_low and orig not in [detected_text, detected_date, detected_title]:
                detected_likes = orig
                break
        if detected_likes:
            break

    return {
        "text": detected_text,
        "date": detected_date,
        "title": detected_title,
        "likes": detected_likes,
    }

def get_file_preview_and_columns(file_bytes: bytes, file_name: str, sheet_name: str | None = None, n: int = 5) -> tuple[list[str], pd.DataFrame]:
    """Reads a fast preview of rows and returns the column names and sample DataFrame."""
    preview_df = read_raw_file(file_bytes, file_name, sheet_name=sheet_name, nrows=n)
    return list(preview_df.columns), preview_df

def process_and_classify_dataframe(
    df: pd.DataFrame,
    text_col: str,
    date_col: str | None = None,
    title_col: str | None = None,
    likes_col: str | None = None,
    max_comments: int = MAX_COMMENTS
) -> pd.DataFrame:
    """
    Standardizes raw dataframe into standard schema and runs the NLP classification pipeline.
    """
    if text_col not in df.columns:
        raise ValueError(f"Selected text column '{text_col}' not found in dataset.")

    # Rename common auxiliary columns if present
    rename_dict = {}
    for col in df.columns:
        if "Name (click to view profile)" in col:
            rename_dict[col] = "Name"
        elif "(view source)" in col:
            rename_dict[col] = "Source"
    if rename_dict:
        df = df.rename(columns=rename_dict)

    # 1. Clean Comment Text
    df = df[df[text_col].notna()].copy()
    df["Comment"] = df[text_col].astype(str).str.strip()
    df = df[df["Comment"] != ""]
    # Drop rows that are literally placeholder strings
    df = df[~df["Comment"].str.lower().isin(["nan", "null", "none", "n/a"])]

    if len(df) == 0:
        raise ValueError(f"No valid text entries found in column '{text_col}'.")

    # 2. Handle Date Column
    has_valid_dates = False
    if date_col and date_col in df.columns and date_col != "(None - Auto-generate)":
        parsed_dates = pd.to_datetime(df[date_col], errors="coerce")
        valid_date_count = parsed_dates.notna().sum()
        if valid_date_count > 0:
            df["Date"] = parsed_dates
            # If some are NaT, fill them with median or forward fill
            if parsed_dates.isna().any():
                fill_val = df["Date"].dropna().median() if not df["Date"].dropna().empty else pd.Timestamp.now()
                df["Date"] = df["Date"].fillna(fill_val)
            has_valid_dates = True

    if not has_valid_dates:
        # Generate synthetic chronological dates spaced by 1 hour backwards from now
        now = pd.Timestamp.now()
        df["Date"] = [now - pd.Timedelta(hours=i) for i in range(len(df))]

    # 3. Handle Post Title / Category
    if title_col and title_col in df.columns and title_col != "(None - General)":
        df["Post Title"] = df[title_col].astype(str).str.strip()
        df["Post Title"] = df["Post Title"].replace({"": "General", "nan": "General"})
    elif "Post Title" in df.columns:
        df["Post Title"] = df["Post Title"].astype(str).str.strip()
    else:
        df["Post Title"] = "General"

    # 4. Handle Likes
    if likes_col and likes_col in df.columns and likes_col != "(None - 0)":
        df["Likes"] = pd.to_numeric(df[likes_col], errors="coerce").fillna(0).astype(int)
    elif "Likes" in df.columns:
        df["Likes"] = pd.to_numeric(df["Likes"], errors="coerce").fillna(0).astype(int)
    else:
        df["Likes"] = 0

    # 5. Handle Auxiliary fields (Name, Source)
    if "Name" not in df.columns:
        df["Name"] = "Anonymous"
    if "Source" not in df.columns:
        df["Source"] = ""

    # 6. Sort and Limit
    if has_valid_dates:
        df = df.sort_values("Date", ascending=False)
    df = df.head(max_comments).copy()

    # 7. Date-derived attributes
    df["YearMonth"] = df["Date"].dt.strftime("%Y-%m")
    df["DateOnly"]  = df["Date"].dt.date
    df["DayOfWeek"] = df["Date"].dt.day_name()
    df["Hour"]      = df["Date"].dt.hour
    df["Week"]      = df["Date"].dt.to_period("W").apply(lambda r: str(r.start_time.date()))

    # 8. Run NLP Inference in Chunks with Progress Bar
    all_chunks = []
    num_chunks = (len(df) // DEFAULT_CHUNK_SIZE) + (1 if len(df) % DEFAULT_CHUNK_SIZE > 0 else 0)
    
    progress_container = st.empty()
    
    for i in range(0, len(df), DEFAULT_CHUNK_SIZE):
        chunk_idx = i // DEFAULT_CHUNK_SIZE
        chunk = df.iloc[i : i + DEFAULT_CHUNK_SIZE].copy()
        
        # Update progress UI
        if num_chunks > 0:
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
        gc.collect()

    progress_container.empty()
    processed_df = pd.concat(all_chunks, ignore_index=True)
    return processed_df

@st.cache_data(show_spinner=False)
def load_uploaded_data(
    file_bytes: bytes,
    file_name: str,
    sheet_name: str | None = None,
    text_col: str = "Comment",
    date_col: str | None = None,
    title_col: str | None = None,
    likes_col: str | None = None,
    max_comments: int = MAX_COMMENTS
) -> pd.DataFrame:
    """
    Cached data loader for uploaded files (CSV or Excel).
    """
    raw_df = read_raw_file(file_bytes, file_name, sheet_name=sheet_name)
    return process_and_classify_dataframe(
        raw_df,
        text_col=text_col,
        date_col=date_col,
        title_col=title_col,
        likes_col=likes_col,
        max_comments=max_comments
    )

@st.cache_data(show_spinner=False)
def load_data(path: str = "data.xlsx", max_comments: int = MAX_COMMENTS) -> pd.DataFrame:
    """
    Backwards-compatible loader for local files (default dataset).
    """
    with open(path, "rb") as f:
        file_bytes = f.read()
    sheets = get_excel_sheet_names(file_bytes)
    sheet_name = "Raw Data" if "Raw Data" in sheets else (sheets[0] if sheets else None)
    
    return load_uploaded_data(
        file_bytes=file_bytes,
        file_name=os.path.basename(path),
        sheet_name=sheet_name,
        text_col="Comment",
        date_col="Date",
        title_col="Post Title",
        likes_col="Likes",
        max_comments=max_comments
    )
