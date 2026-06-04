import pandas as pd
import os
from datetime import datetime

# Path relative to project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FEEDBACK_FILE = os.path.join(BASE_DIR, "data", "feedback", "corrections.csv")

def save_feedback(comment, original_label, corrected_label, classification_type):
    """
    Saves user feedback to a CSV file.
    classification_type: 'sentiment' | 'intent' | 'topic'
    """
    new_data = pd.DataFrame([{
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "comment": comment,
        "classification_type": classification_type,
        "original_label": original_label,
        "corrected_label": corrected_label
    }])
    
    if not os.path.exists(FEEDBACK_FILE):
        os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)
        new_data.to_csv(FEEDBACK_FILE, index=False)
    else:
        new_data.to_csv(FEEDBACK_FILE, mode='a', header=False, index=False)
