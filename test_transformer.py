from src.logic.classifiers import score_comment
import time

test_texts = [
    "Haaa internet yenyu 💥💥💥💥💥💥",
    "NetOne is actually getting better, I'm impressed.",
    "Worst service ever, I'm switching to Econet.",
    "zvakanaka",
    "bho"
]

print("Starting Sentiment Analysis with Hybrid Transformer...")
for text in test_texts:
    start = time.time()
    res = score_comment(text)
    end = time.time()
    print(f"Text: {text}")
    print(f"  Result: {res} (Time: {end-start:.2f}s)")
    print("-" * 20)
