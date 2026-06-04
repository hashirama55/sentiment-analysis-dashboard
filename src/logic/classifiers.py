import re
import string
import torch
import os
from transformers import pipeline
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from src.constants import (
    SHONA_WORDS, SHONA_POS, SHONA_NEG, 
    SPAM_KW, COMPLAINT_KW, PRAISE_KW, INQUIRY_KW, 
    TOPIC_PATTERNS
)

# Initialize VADER for fallback and slang detection
analyzer = SentimentIntensityAnalyzer()

# Global variable for transformer pipeline (Lazy Loading)
_sentiment_pipeline = None

def get_transformer_pipeline():
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        # Prioritize locally fine-tuned model if it exists
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        refined_path = os.path.join(base_dir, "models", "sentiment_refined")
        if os.path.exists(refined_path):
            model_name = refined_path
            print(f"Loading REFINED model from {refined_path}")
        else:
            # Fallback to base distilled multilingual model
            model_name = "lxyuan/distilbert-base-multilingual-cased-sentiments-student"
            print(f"Loading BASE model: {model_name}")
        
        # Auto-detect GPU
        device = 0 if torch.cuda.is_available() else -1
        if device == 0:
            print("CUDA detected! Using GPU for inference.")
        else:
            print("Using CPU for inference.")
            
        _sentiment_pipeline = pipeline("sentiment-analysis", model=model_name, device=device)
    return _sentiment_pipeline

def detect_language(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return "unknown"
    words = set(re.findall(r'\b\w+\b', text.lower()))
    hits = len(words & SHONA_WORDS)
    if hits >= 2: return "shona/mixed"
    if hits == 1: return "mixed (en+shona)"
    return "english"

def score_comment(text: str) -> dict:
    if not isinstance(text, str) or not text.strip():
        return {"compound": 0, "label": "neutral", "confidence": 0}
    
    # 1. Transformer Score (Contextual Understanding)
    try:
        pipe = get_transformer_pipeline()
        # lxyuan model outputs labels: 'positive', 'neutral', 'negative'
        raw_res = pipe(text[:512])[0]
        label_val = {"positive": 1, "neutral": 0, "negative": -1}
        t_score = label_val.get(raw_res['label'], 0)
        t_confidence = raw_res['score']
        # Convert to a compound-like score (-1 to 1)
        transformer_compound = t_score * t_confidence
    except Exception:
        # Fallback to VADER compound if transformer fails
        vader = analyzer.polarity_scores(text)
        transformer_compound = vader["compound"]
        t_confidence = 0.5

    # 2. Slang & Emoji Score (Local Nuance)
    tokens = re.findall(r'\b\w+\b|[\U00010000-\U0010ffff]', text.lower())
    extra = sum(SHONA_POS.get(t, 0) for t in tokens)
    extra += sum(SHONA_NEG.get(t, 0) for t in tokens)
    extra_norm = max(-1.0, min(1.0, extra / 5))

    # 3. Hybrid Blending
    # We give high weight to Transformer for context, but allow Slang to override/augment
    # This ensures "Haaa ... 💥💥💥" remains positive even if the transformer is unsure
    if extra != 0:
        # Blend transformer and slang
        adjusted = (transformer_compound * 0.4) + (extra_norm * 0.6)
    else:
        # Trust transformer more if no specific slang detected
        adjusted = transformer_compound

    adjusted = max(-1.0, min(1.0, adjusted))
    label = "positive" if adjusted >= 0.15 else "negative" if adjusted <= -0.15 else "neutral"
    
    # Final confidence is a mix of model confidence and slang intensity
    final_conf = round(max(t_confidence * 100, abs(adjusted) * 100), 1)
    
    return {
        "compound": round(adjusted, 4), 
        "label": label, 
        "confidence": final_conf
    }

# Pre-compile regex for performance
_TOKEN_RE = re.compile(r'\b\w+\b|[\U00010000-\U0010ffff]')

def score_comments_batch(texts: list[str]) -> list[dict]:
    """Processes a batch of texts for sentiment analysis using the transformer pipeline."""
    if not texts:
        return []
    
    # Pre-clean texts and handle empty strings
    cleaned_texts = [str(t)[:512] if isinstance(t, str) and t.strip() else "" for t in texts]
    
    # 1. Transformer Batch Score
    try:
        pipe = get_transformer_pipeline()
        non_empty_indices = [i for i, t in enumerate(cleaned_texts) if t]
        non_empty_texts = [cleaned_texts[i] for i in non_empty_indices]
        
        batch_results = [None] * len(texts)
        if non_empty_texts:
            pipe_res = pipe(non_empty_texts, batch_size=len(non_empty_texts), truncation=True)
            for idx, res in zip(non_empty_indices, pipe_res):
                batch_results[idx] = res
                
    except Exception as e:
        print(f"Batch transformer error: {e}")
        batch_results = [None] * len(texts)

    final_results = []
    for i, text in enumerate(texts):
        if not isinstance(text, str) or not text.strip():
            final_results.append({"compound": 0, "label": "neutral", "confidence": 0})
            continue
            
        raw_res = batch_results[i]
        if raw_res:
            label_val = {"positive": 1, "neutral": 0, "negative": -1}
            t_score = label_val.get(raw_res['label'], 0)
            t_confidence = raw_res['score']
            transformer_compound = t_score * t_confidence
        else:
            vader = analyzer.polarity_scores(text)
            transformer_compound = vader["compound"]
            t_confidence = 0.5

        # 2. Slang & Emoji Score (Optimized)
        tokens = _TOKEN_RE.findall(text.lower())
        extra = sum(SHONA_POS.get(t, 0) for t in tokens)
        extra += sum(SHONA_NEG.get(t, 0) for t in tokens)
        
        if extra != 0:
            extra_norm = max(-1.0, min(1.0, extra / 5))
            adjusted = (transformer_compound * 0.4) + (extra_norm * 0.6)
        else:
            adjusted = transformer_compound

        adjusted = max(-1.0, min(1.0, adjusted))
        label = "positive" if adjusted >= 0.15 else "negative" if adjusted <= -0.15 else "neutral"
        final_conf = round(max(t_confidence * 100, abs(adjusted) * 100), 1)
        
        final_results.append({
            "compound": round(adjusted, 4), 
            "label": label, 
            "confidence": final_conf
        })
        
    return final_results

def classify_intent(text: str) -> str:
    """Returns: complaint | praise | inquiry | spam"""
    if not isinstance(text, str): return "inquiry"
    t = text.lower()
    for p in SPAM_KW:
        if re.search(p, t, re.I): return "spam"
    scores = {"complaint": 0, "praise": 0, "inquiry": 0}
    for p in COMPLAINT_KW:
        if re.search(p, t, re.I): scores["complaint"] += 1
    for p in PRAISE_KW:
        if re.search(p, t, re.I): scores["praise"] += 1
    for p in INQUIRY_KW:
        if re.search(p, t, re.I): scores["inquiry"] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "inquiry"

def classify_topic(text: str) -> str:
    """Returns: network | billing | roaming | support | general"""
    if not isinstance(text, str): return "general"
    t = text.lower()
    scores = {k: 0 for k in TOPIC_PATTERNS}
    for topic, patterns in TOPIC_PATTERNS.items():
        for p in patterns:
            if re.search(p, t, re.I):
                scores[topic] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"
