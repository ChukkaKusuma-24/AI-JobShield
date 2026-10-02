"""Train TF-IDF + classifier model for AI JobShield."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml"))
from preprocess import preprocess_text  # noqa: E402


def load_csv(path: Path) -> pd.DataFrame:
    # Skip comment lines starting with #
    df = pd.read_csv(path, comment="#")
    if "text" not in df.columns or "label" not in df.columns:
        raise ValueError("CSV must contain columns: text, label")
    df = df.dropna(subset=["text", "label"])
    df["label"] = df["label"].astype(int)
    df["text_clean"] = df["text"].astype(str).map(preprocess_text)
    return df


def build_pipeline(alternative: str = "logistic") -> Pipeline:
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
    if alternative == "naive_bayes":
        clf = MultinomialNB()
    else:
        clf = LogisticRegression(class_weight="balanced", max_iter=1000, solver="liblinear")
    return Pipeline([("tfidf", vectorizer), ("clf", clf)])


def train(data_path: Path, model_path: Path, alternative: str = "logistic") -> dict:
    df = load_csv(data_path)
    X = df["text_clean"]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    pipe = build_pipeline(alternative)
    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)

    cm = confusion_matrix(y_test, y_pred).tolist()
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "confusion_matrix": cm,
        "dataset_size": int(len(df)),
        "dataset_path": str(data_path),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "is_demo_data": True,
        "classifier": alternative,
        "disclaimer": (
            "Metrics come from a small synthetic demo dataset and do NOT "
            "represent real-world performance."
        ),
    }

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": pipe, "preprocess": "ml.preprocess.preprocess_text"}, model_path)

    metrics_path = model_path.parent / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    # Confusion matrix PNG
    fig, ax = plt.subplots(figsize=(4, 3.5))
    ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["Legit(0)", "Suspicious(1)"])
    ax.set_yticklabels(["Legit(0)", "Suspicious(1)"])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix (DEMO)")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, cm[i][j], ha="center", va="center", color="black")
    fig.tight_layout()
    fig.savefig(model_path.parent / "confusion_matrix.png", dpi=120)
    plt.close(fig)

    print(json.dumps(metrics, indent=2))
    print(f"Model saved to {model_path}")
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=str(ROOT / "data" / "demo_training_data.csv"))
    parser.add_argument("--model", default=str(ROOT / "models" / "jobshield_model.joblib"))
    parser.add_argument("--alternative", default="logistic", choices=["logistic", "naive_bayes"])
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        # Auto-generate demo data
        from generate_demo_data import generate

        data_path.parent.mkdir(parents=True, exist_ok=True)
        import csv

        rows = generate(400)
        with data_path.open("w", newline="", encoding="utf-8") as f:
            f.write("# DEMO SYNTHETIC DATASET\n")
            writer = csv.DictWriter(f, fieldnames=["text", "label", "source"])
            writer.writeheader()
            writer.writerows(rows)
        print(f"Generated demo data at {data_path}")

    train(data_path, Path(args.model), args.alternative)


if __name__ == "__main__":
    main()
