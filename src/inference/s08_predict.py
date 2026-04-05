"""
s08_predict.py
Run inference on new articles using the production classifier.

Takes a CSV with a text_clean column, returns top-2 predictions with confidence.

Input:  data/modelling/supabase_inference_articles.csv (from s07_pull_supabase)
Output: data/modelling/classified_articles.csv
"""

import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sentence_transformers import SentenceTransformer

# -----------------------------
# CONFIG
# -----------------------------
MODEL_NAME = "all-MiniLM-L6-v2"
MODEL_DIR = Path("models")
DATA_DIR = Path("data/modelling")
TEXT_COL = "text_clean"
DEFAULT_INPUT = DATA_DIR / "supabase_inference_articles.csv"
DEFAULT_OUTPUT = DATA_DIR / "classified_articles.csv"


def classify_batch(texts, model, clf):
    """Classify a batch of texts. Returns DataFrame with top-2 predictions."""
    embeddings = model.encode(texts, show_progress_bar=True)
    proba = clf.predict_proba(embeddings)

    results = []
    for i in range(len(texts)):
        top2_idx = np.argsort(proba[i])[-2:][::-1]
        results.append({
            "top1": clf.classes_[top2_idx[0]],
            "top1_confidence": proba[i][top2_idx[0]],
            "top2": clf.classes_[top2_idx[1]],
            "top2_confidence": proba[i][top2_idx[1]],
            "confidence_gap": proba[i][top2_idx[0]] - proba[i][top2_idx[1]],
        })

    return pd.DataFrame(results)


def main(input_path=None, output_path=None):
    input_path = Path(input_path) if input_path else DEFAULT_INPUT
    output_path = Path(output_path) if output_path else DEFAULT_OUTPUT

    # Load model
    print("  Loading model...")
    model = SentenceTransformer(MODEL_NAME)
    clf = joblib.load(MODEL_DIR / "sbert_classifier_no_meta.joblib")
    print(f"  Classes: {list(clf.classes_)}")

    # Load articles
    df = pd.read_csv(input_path)
    print(f"  Input: {len(df)} articles from {input_path}")

    # Drop missing text
    missing = df[TEXT_COL].isna() | (df[TEXT_COL].str.strip() == "")
    if missing.any():
        print(f"  Dropped {missing.sum()} articles with missing text")
        df = df[~missing].copy()

    # Classify
    predictions = classify_batch(df[TEXT_COL].tolist(), model, clf)

    # Combine
    result = df.reset_index(drop=True)
    for col in predictions.columns:
        result[col] = predictions[col].values

    # Save
    result.to_csv(output_path, index=False)
    print(f"  Saved {len(result)} classified articles → {output_path}")

    # Summary
    dist = result["top1"].value_counts()
    print(f"\n  Prediction distribution:")
    for cls, count in dist.items():
        print(f"    {cls:<45} {count:>4} ({count/len(result):.1%})")

    mean_conf = result["top1_confidence"].mean()
    below_50 = (result["top1_confidence"] < 0.50).mean()
    print(f"\n  Mean confidence: {mean_conf:.3f}")
    print(f"  Below 50%: {below_50:.1%}")
    print("  Done.")


if __name__ == "__main__":
    main()
