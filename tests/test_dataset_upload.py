import io
import pandas as pd
import pytest
from src.logic.data_loader import (
    get_excel_sheet_names,
    read_raw_file,
    detect_column_candidates,
    process_and_classify_dataframe,
    load_uploaded_data
)

def test_detect_column_candidates_standard():
    cols = ["Comment", "Date", "Post Title", "Likes"]
    mapping = detect_column_candidates(cols)
    assert mapping["text"] == "Comment"
    assert mapping["date"] == "Date"
    assert mapping["title"] == "Post Title"
    assert mapping["likes"] == "Likes"

def test_detect_column_candidates_custom_variations():
    cols = ["ID", "Customer_Feedback", "Created_Timestamp", "Department_Channel", "Upvote_Score"]
    mapping = detect_column_candidates(cols)
    assert mapping["text"] == "Customer_Feedback"
    assert mapping["date"] == "Created_Timestamp"
    assert mapping["title"] == "Department_Channel"
    assert mapping["likes"] == "Upvote_Score"

def test_read_raw_csv_bytes():
    csv_data = "Comment,Date\n\"Great service\",2026-03-01\n\"Network is down\",2026-03-02\n".encode("utf-8")
    df = read_raw_file(csv_data, "test.csv")
    assert len(df) == 2
    assert list(df.columns) == ["Comment", "Date"]

def test_process_and_classify_custom_columns():
    raw_data = pd.DataFrame({
        "Review_Text": [
            "NetOne network is very slow in Bulawayo",
            "Thank you for the quick assistance, very helpful!",
            "How do I activate roaming?"
        ],
        "Timestamp": [
            "2026-03-10 10:00:00",
            "2026-03-10 11:30:00",
            "2026-03-10 14:15:00"
        ],
        "Category": ["Network", "Support", "Roaming"],
        "Stars": [1, 5, 3]
    })
    
    processed_df = process_and_classify_dataframe(
        df=raw_data,
        text_col="Review_Text",
        date_col="Timestamp",
        title_col="Category",
        likes_col="Stars",
        max_comments=10
    )
    
    assert len(processed_df) == 3
    expected_cols = [
        "Comment", "Date", "Post Title", "Likes", "YearMonth", 
        "DateOnly", "DayOfWeek", "Hour", "Week", "compound", 
        "sentiment", "confidence", "intent", "topic", "language"
    ]
    for col in expected_cols:
        assert col in processed_df.columns, f"Missing expected column: {col}"
        
    assert set(processed_df["sentiment"].unique()).issubset({"positive", "neutral", "negative"})
    assert set(processed_df["intent"].unique()).issubset({"complaint", "praise", "inquiry", "spam"})
    assert set(processed_df["topic"].unique()).issubset({"network", "billing", "roaming", "support", "general"})

def test_process_and_classify_missing_dates_auto_generates():
    raw_data = pd.DataFrame({
        "Text": [
            "Network keeps dropping today",
            "Best network in the country woye!",
        ]
    })
    processed_df = process_and_classify_dataframe(
        df=raw_data,
        text_col="Text",
        date_col=None,
        title_col=None,
        likes_col=None,
        max_comments=10
    )
    assert len(processed_df) == 2
    assert "Date" in processed_df.columns
    assert processed_df["Date"].notna().all()
    assert processed_df["Post Title"].iloc[0] == "General"
    assert processed_df["Likes"].iloc[0] == 0

def test_process_and_classify_drops_empty_comments():
    raw_data = pd.DataFrame({
        "Comment": ["Valid comment", "", "   ", None, "nan", "Another comment"],
        "Date": ["2026-01-01"] * 6
    })
    processed_df = process_and_classify_dataframe(
        df=raw_data,
        text_col="Comment",
        max_comments=10
    )
    assert len(processed_df) == 2
    assert set(processed_df["Comment"].tolist()) == {"Valid comment", "Another comment"}

if __name__ == "__main__":
    print("Running tests...")
    test_detect_column_candidates_standard()
    test_detect_column_candidates_custom_variations()
    test_read_raw_csv_bytes()
    test_process_and_classify_custom_columns()
    test_process_and_classify_missing_dates_auto_generates()
    test_process_and_classify_drops_empty_comments()
    print("All unit tests passed successfully!")
