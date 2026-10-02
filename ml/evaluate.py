"""Evaluate a saved JobShield model on a CSV."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml"))
from preprocess import preprocess_text  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=str(ROOT / "data" / "demo_training_data.csv"))
    parser.add_argument("--model", default=str(ROOT / "models" / "jobshield_model.joblib"))
    args = parser.parse_args()

    bundle = joblib.load(args.model)
    pipe = bundle["pipeline"] if isinstance(bundle, dict) else bundle
    df = pd.read_csv(args.data, comment="#").dropna(subset=["text", "label"])
    X = df["text"].astype(str).map(preprocess_text)
    y = df["label"].astype(int)
    pred = pipe.predict(X)
    print(classification_report(y, pred))
    print("Confusion matrix:", confusion_matrix(y, pred).tolist())
    print(
        json.dumps(
            {
                "note": "Metrics come from a small synthetic demo dataset and do NOT "
                "represent real-world performance."
            }
        )
    )


if __name__ == "__main__":
    main()
