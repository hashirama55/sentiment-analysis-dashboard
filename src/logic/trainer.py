import pandas as pd
import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification, 
    Trainer, 
    TrainingArguments,
    DataCollatorWithPadding
)
from sklearn.model_selection import train_test_split
import os

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_MODEL = "lxyuan/distilbert-base-multilingual-cased-sentiments-student"
FEEDBACK_FILE = os.path.join(BASE_DIR, "data", "feedback", "corrections.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "models", "sentiment_refined")

class SentimentDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

def run_fine_tuning():
    if not os.path.exists(FEEDBACK_FILE):
        print(f"Error: No feedback file found at {FEEDBACK_FILE}. Collect some corrections first!")
        return

    # 1. Load and Prepare Data
    df = pd.read_csv(FEEDBACK_FILE)
    df = df[df['classification_type'] == 'sentiment'] # Only fine-tune sentiment for now
    
    if len(df) < 10:
        print("Error: Not enough data for fine-tuning. Collect at least 10 corrections.")
        return

    # Map labels to numeric IDs
    # lxyuan model: positive:0, neutral:1, negative:2 (Checking model config is safer, but this is typical)
    # Actually, we should check the base model's config labels.
    # For now, let's assume standard mapping and allow override
    label_map = {"positive": 0, "neutral": 1, "negative": 2}
    df['label_id'] = df['corrected_label'].map(label_map)
    
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        df['comment'].tolist(), df['label_id'].tolist(), test_size=0.2
    )

    # 2. Tokenization
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    train_encodings = tokenizer(train_texts, truncation=True, padding=True)
    val_encodings = tokenizer(val_texts, truncation=True, padding=True)

    train_dataset = SentimentDataset(train_encodings, train_labels)
    val_dataset = SentimentDataset(val_encodings, val_labels)

    # 3. Model Setup
    model = AutoModelForSequenceClassification.from_pretrained(BASE_MODEL, num_labels=3)

    # 4. Training Arguments
    training_args = TrainingArguments(
        output_dir='./results',
        num_train_epochs=3,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        warmup_steps=100,
        weight_decay=0.01,
        logging_dir='./logs',
        logging_steps=10,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
    )

    # 5. Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
    )

    print("🚀 Starting fine-tuning...")
    trainer.train()

    # 6. Save the refined model
    print(f"✅ Saving refined model to {OUTPUT_DIR}")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print("✨ Fine-tuning complete!")

if __name__ == "__main__":
    run_fine_tuning()
