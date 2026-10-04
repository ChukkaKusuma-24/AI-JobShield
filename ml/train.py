"""Train calibrated TF-IDF + Logistic Regression model for AI JobShield (Step 8)."""
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
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import PredefinedSplit
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml"))
from preprocess import preprocess_text  # noqa: E402


def load_dataset(path: Path) -> pd.DataFrame:
    """Load training CSV and validate columns."""
    df = pd.read_csv(path, comment="#")
    if "text" not in df.columns or "label" not in df.columns:
        raise ValueError("CSV must contain columns: text, label")
    df = df.dropna(subset=["text", "label"]).copy()
    df["label"] = df["label"].astype(int)
    return df


def split_data_group_aware(
    df: pd.DataFrame,
    seed: int = 42,
    train_frac: float = 0.70,
    val_frac: float = 0.15,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Perform leakage-resistant stratified group split by group_id."""
    if "group_id" not in df.columns:
        # Fallback to stratified random split if no group_id
        from sklearn.model_selection import train_test_split

        train_val, test_df = train_test_split(
            df, test_size=1.0 - train_frac - val_frac, random_state=seed, stratify=df["label"]
        )
        val_size = val_frac / (train_frac + val_frac)
        train_df, val_df = train_test_split(
            train_val, test_size=val_size, random_state=seed, stratify=train_val["label"]
        )
        return train_df, val_df, test_df

    rng = np.random.RandomState(seed)
    train_idx, val_idx, test_idx = [], [], []

    for label in [0, 1]:
        sub = df[df["label"] == label]
        groups = list(sub["group_id"].unique())
        rng.shuffle(groups)

        n_total = len(sub)
        n_train = int(n_total * train_frac)
        n_val = int(n_total * val_frac)

        curr_train, curr_val, curr_test = 0, 0, 0
        t_grp, v_grp, te_grp = [], [], []

        for g in groups:
            g_len = len(sub[sub["group_id"] == g])
            if curr_train + g_len <= n_train or (curr_val >= n_val and curr_test >= (n_total - n_train - n_val)):
                t_grp.append(g)
                curr_train += g_len
            elif curr_val + g_len <= n_val:
                v_grp.append(g)
                curr_val += g_len
            else:
                te_grp.append(g)
                curr_test += g_len

        train_idx.extend(sub[sub["group_id"].isin(t_grp)].index)
        val_idx.extend(sub[sub["group_id"].isin(v_grp)].index)
        test_idx.extend(sub[sub["group_id"].isin(te_grp)].index)

    return df.loc[train_idx].copy(), df.loc[val_idx].copy(), df.loc[test_idx].copy()


def train(
    data_path: Path,
    model_path: Path,
    alternative: str = "logistic",
    seed: int = 42,
) -> dict:
    """Train calibrated pipeline and evaluate on holdout test set."""
    df = load_dataset(data_path)

    # 1. Leakage-resistant group-aware partition
    train_df, val_df, test_df = split_data_group_aware(df, seed=seed)

    X_train = [preprocess_text(t) for t in train_df["text"]]
    y_train = list(train_df["label"])
    X_val = [preprocess_text(t) for t in val_df["text"]]
    y_val = list(val_df["label"])
    X_test = [preprocess_text(t) for t in test_df["text"]]
    y_test = list(test_df["label"])

    X_train_val = X_train + X_val
    y_train_val = y_train + y_val
    test_fold = [-1] * len(X_train) + [0] * len(X_val)
    ps = PredefinedSplit(test_fold)

    # 2. Pipeline setup
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)

    if alternative == "naive_bayes":
        base_clf = MultinomialNB()
        cal = CalibratedClassifierCV(estimator=base_clf, cv=ps, method="sigmoid")
        pipe = Pipeline([("tfidf", vec), ("clf", cal)])
        pipe.fit(X_train_val, y_train_val)
    else:
        base_clf = LogisticRegression(
            class_weight="balanced",
            random_state=seed,
            C=1.0,
            max_iter=1000,
            solver="liblinear",
        )
        cal = CalibratedClassifierCV(estimator=base_clf, cv=ps, method="sigmoid")
        pipe = Pipeline([("tfidf", vec), ("clf", cal)])
        pipe.fit(X_train_val, y_train_val)
        # Attach base coefficients to calibrated classifier for explainability
        cal.coef_ = cal.calibrated_classifiers_[0].estimator.coef_

    # 3. Untouched Test Set Evaluation
    y_pred_proba = pipe.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba >= 0.5).astype(int)

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    roc = roc_auc_score(y_test, y_pred_proba)
    pr_auc = average_precision_score(y_test, y_pred_proba)
    brier = brier_score_loss(y_test, y_pred_proba)
    cm = confusion_matrix(y_test, y_pred).tolist()

    metrics = {
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1": round(float(f1), 4),
        "roc_auc": round(float(roc), 4),
        "pr_auc": round(float(pr_auc), 4),
        "brier_score": round(float(brier), 4),
        "confusion_matrix": cm,
        "dataset_size": int(len(df)),
        "train_size": len(train_df),
        "val_size": len(val_df),
        "test_size": len(test_df),
        "vocabulary_size": len(vec.vocabulary_),
        "dataset_path": str(data_path),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "is_calibrated": True,
        "calibration_method": "sigmoid_platt",
        "classifier": alternative,
        "random_seed": seed,
    }

    # 4. Save Model Artifacts
    paths_to_save = [model_path]
    backend_alt = ROOT / "backend" / "models" / "jobshield_model.joblib"
    if backend_alt != model_path:
        paths_to_save.append(backend_alt)

    for p in paths_to_save:
        p.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"pipeline": pipe, "preprocess": "ml.preprocess.preprocess_text"}, p)
        metrics_p = p.parent / "metrics.json"
        metrics_p.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    # 5. Confusion Matrix PNG
    fig, ax = plt.subplots(figsize=(4, 3.5))
    ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["Legit(0)", "Scam(1)"])
    ax.set_yticklabels(["Legit(0)", "Scam(1)"])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(f"Confusion Matrix (Holdout N={len(test_df)})")
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
    parser.add_argument("--data", default=str(ROOT / "data" / "training_data_v2.csv"))
    parser.add_argument("--model", default=str(ROOT / "models" / "jobshield_model.joblib"))
    parser.add_argument("--alternative", default="logistic", choices=["logistic", "naive_bayes"])
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        fallback = ROOT / "data" / "demo_training_data.csv"
        if fallback.exists():
            data_path = fallback
        else:
            from build_dataset_v2 import build_and_save

            build_and_save()
            data_path = ROOT / "data" / "training_data_v2.csv"

    train(data_path, Path(args.model), args.alternative)


if __name__ == "__main__":
    main()
