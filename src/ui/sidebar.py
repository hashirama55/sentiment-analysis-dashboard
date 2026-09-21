import streamlit as st
import pandas as pd
from src.constants import MAX_COMMENTS
from src.logic.data_loader import (
    load_data,
    load_uploaded_data,
    get_excel_sheet_names,
    get_file_preview_and_columns,
    detect_column_candidates
)

def render_dataset_selector() -> tuple[pd.DataFrame | None, str, str]:
    """
    Renders the dataset source switcher in the sidebar.
    Returns:
        tuple of (df, dataset_name, source_type)
        where df may be None if user selected upload mode but hasn't uploaded a file yet.
    """
    st.sidebar.markdown("### 📁 Dataset Source")
    
    # Initialize session state for source selection if not present
    if "data_source_mode" not in st.session_state:
        st.session_state.data_source_mode = "Default (NetOne)"

    source_mode = st.sidebar.segmented_control(
        "Dataset Source Mode",
        options=["Default (NetOne)", "Upload Dataset"],
        default=st.session_state.data_source_mode,
        label_visibility="collapsed"
    )
    st.session_state.data_source_mode = source_mode

    if source_mode == "Default (NetOne)":
        with st.sidebar:
            st.caption("ℹ️ Preloaded NetOne Facebook customer comments dataset.")
        try:
            df = load_data("data.xlsx")
            return df, "NetOne Facebook Comments", "default"
        except Exception as e:
            st.sidebar.error(f"Error loading default dataset: {e}")
            return None, "Error", "default"

    else: # "Upload Dataset"
        uploaded_file = st.sidebar.file_uploader(
            "Upload CSV or Excel file",
            type=["csv", "xlsx", "xls"],
            help="Supported formats: CSV (.csv), Excel (.xlsx, .xls)",
            key="dataset_file_uploader"
        )

        if uploaded_file is None:
            st.sidebar.info("Upload a file above to begin analysis.")
            return None, "", "uploaded"

        file_bytes = uploaded_file.getvalue()
        file_name = uploaded_file.name

        # Check for Excel sheets
        selected_sheet = None
        if file_name.lower().endswith((".xlsx", ".xls")):
            sheet_names = get_excel_sheet_names(file_bytes)
            if len(sheet_names) > 1:
                default_idx = sheet_names.index("Raw Data") if "Raw Data" in sheet_names else 0
                selected_sheet = st.sidebar.selectbox("Select Sheet", sheet_names, index=default_idx)
            elif sheet_names:
                selected_sheet = sheet_names[0]

        # Inspect columns & preview
        try:
            columns, preview_df = get_file_preview_and_columns(file_bytes, file_name, sheet_name=selected_sheet)
        except Exception as e:
            st.sidebar.error(f"Failed to read dataset columns: {e}")
            return None, file_name, "uploaded"

        if not columns:
            st.sidebar.error("The uploaded file does not appear to contain any columns.")
            return None, file_name, "uploaded"

        detected = detect_column_candidates(columns)

        with st.sidebar.expander("⚙️ Column Mapping & Options", expanded=False):
            st.caption("Auto-detected best matching columns. You can override below:")
            
            # Text / Comment Column (Required)
            text_idx = columns.index(detected["text"]) if detected["text"] in columns else 0
            text_col = st.selectbox(
                "Text / Comment Column *",
                options=columns,
                index=text_idx,
                help="Column containing customer comment or review text"
            )

            # Date Column (Optional)
            date_options = ["(None - Auto-generate)"] + columns
            date_idx = date_options.index(detected["date"]) if detected["date"] in date_options else 0
            date_col = st.selectbox(
                "Date Column (optional)",
                options=date_options,
                index=date_idx,
                help="Column containing dates. If none, chronological dates are generated."
            )

            # Category / Post Title (Optional)
            title_options = ["(None - General)"] + columns
            title_idx = title_options.index(detected["title"]) if detected["title"] in title_options else 0
            title_col = st.selectbox(
                "Category / Post Column (optional)",
                options=title_options,
                index=title_idx,
                help="Column containing post title, topic, or channel name"
            )

            # Likes / Engagement (Optional)
            likes_options = ["(None - 0)"] + columns
            likes_idx = likes_options.index(detected["likes"]) if detected["likes"] in likes_options else 0
            likes_col = st.selectbox(
                "Likes Column (optional)",
                options=likes_options,
                index=likes_idx,
                help="Column containing like or upvote count"
            )

            # Limit
            max_comments = st.slider(
                "Max comments to analyze",
                min_value=50,
                max_value=2000,
                value=min(max(len(preview_df) * 10, 200), MAX_COMMENTS),
                step=50,
                help="Number of comments to process. Higher counts take slightly longer."
            )

        try:
            df = load_uploaded_data(
                file_bytes=file_bytes,
                file_name=file_name,
                sheet_name=selected_sheet,
                text_col=text_col,
                date_col=date_col,
                title_col=title_col,
                likes_col=likes_col,
                max_comments=max_comments
            )
            st.sidebar.caption(f"✅ Loaded **{len(df):,}** comments from *{file_name}*")
            return df, file_name, "uploaded"
        except Exception as e:
            st.sidebar.error(f"Error analyzing dataset: {e}")
            return None, file_name, "uploaded"

def render_sidebar_filters(df: pd.DataFrame, dataset_name: str = "") -> tuple[pd.DataFrame, str]:
    """
    Renders filtering widgets in the sidebar for an active dataset.
    """
    st.sidebar.divider()
    st.sidebar.markdown("### 🔧 Filters")
    
    if len(df) >= MAX_COMMENTS:
        st.sidebar.warning(f"Showing latest {MAX_COMMENTS} comments for optimal performance.")

    # Topic / Post Filter
    all_topics_list = sorted(df["Post Title"].astype(str).unique().tolist())
    selected_topics = st.sidebar.multiselect(
        "Post / Topic",
        all_topics_list,
        default=[],
        placeholder="All topics"
    )

    # Sentiment Filter
    sentiments = st.sidebar.multiselect(
        "Sentiment",
        ["positive", "neutral", "negative"],
        default=["positive", "neutral", "negative"]
    )

    # Intent Filter
    intents = st.sidebar.multiselect(
        "Intent",
        ["complaint", "praise", "inquiry", "spam"],
        default=["complaint", "praise", "inquiry", "spam"]
    )

    # Topic Category Filter
    topics_filter = st.sidebar.multiselect(
        "Topic Category",
        ["network", "billing", "roaming", "support", "general"],
        default=["network", "billing", "roaming", "support", "general"]
    )

    # Language Filter
    available_languages = sorted(df["language"].unique().tolist())
    languages = st.sidebar.multiselect(
        "Language",
        available_languages,
        default=available_languages
    )

    st.sidebar.divider()
    granularity = st.sidebar.radio("Time Granularity", ["Month", "Week"], index=0, horizontal=True)
    
    date_col = "YearMonth" if granularity == "Month" else "Week"
    time_options = sorted(df[date_col].dropna().unique().tolist())
    
    if len(time_options) > 1:
        t_start, t_end = st.sidebar.select_slider(
            f"Select {granularity} Range", 
            options=time_options, 
            value=(time_options[0], time_options[-1])
        )
    elif len(time_options) == 1:
        t_start = t_end = time_options[0]
        st.sidebar.info(f"Single {granularity.lower()} present: {t_start}")
    else:
        t_start = t_end = None

    min_conf = st.sidebar.slider("Min. confidence %", 0, 100, 0, 5)

    # Apply filters
    fdf = df.copy()
    if selected_topics:
        fdf = fdf[fdf["Post Title"].isin(selected_topics)]
    if sentiments:
        fdf = fdf[fdf["sentiment"].isin(sentiments)]
    if intents:
        fdf = fdf[fdf["intent"].isin(intents)]
    if topics_filter:
        fdf = fdf[fdf["topic"].isin(topics_filter)]
    if languages:
        fdf = fdf[fdf["language"].isin(languages)]
    
    if t_start and t_end:
        fdf = fdf[(fdf[date_col] >= t_start) & (fdf[date_col] <= t_end)]
        
    fdf = fdf[fdf["confidence"] >= min_conf]

    # Quick reset or cache clear button
    with st.sidebar:
        if st.button("🔄 Clear Cache & Refresh", help="Clears cache and re-runs model inference", icon=":material/refresh:"):
            st.cache_data.clear()
            st.rerun()

    return fdf, granularity

def render_sidebar(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Backwards-compatible wrapper that renders filters for a given DataFrame."""
    return render_sidebar_filters(df)
