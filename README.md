# 📊 NetOne Facebook Sentiment Dashboard

A specialized Streamlit dashboard for analyzing Facebook comment sentiment, intent, and topics for NetOne. This tool features a custom pipeline designed to handle a mix of English, Shona, and local slang.

## 🚀 Key Features

- **Multi-lingual Sentiment Analysis:** Combines VADER with custom Shona and Slang lexicons for accurate sentiment scoring.
- **Intent Classification:** Automatically categorizes comments into `complaint`, `praise`, `inquiry`, or `spam`.
- **Topic Modeling:** Identifies key areas of discussion such as `network`, `billing`, `roaming`, `support`, and `general`.
- **Dynamic Date Filtering:** Filter comments starting from 2026 with adjustable granularity (Month or Week).
- **Trend Monitoring:** Includes spike detection for complaints (Mean + 1.5σ threshold) and weekly/monthly topic heatmaps.
- **Interactive Explorer:** Deep dive into specific comments with keyword searching and multi-filter support.

## 🛠️ Project Structure

- `app.py`: Main Streamlit application entry point.
- `src/logic/`: Backend logic for data loading and NLP classifiers.
- `src/ui/`: UI components, sidebar layout, and individual dashboard tabs.
- `data.xlsx`: The raw dataset used for analysis.

## ⚙️ Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/hashirama55/sentiment-analysis-dashboard.git
   cd sentiment-analysis-dashboard
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## 🏃 Running the App

To start the dashboard, run the following command from the project root:

```bash
streamlit run app.py
```

## 🧠 Pipeline Details


- **Sentiment:** lxyuan/distilbert-base-multilingual-cased-sentiments-student + Shona/Slang lexicon.
- **Intent:** Keyword-based pattern matching for complaints, praise, inquiries, and spam.
- **Topics:** Regex-based categorization for core business units.
- **Spikes:** Statistical anomaly detection on daily complaint volumes.
