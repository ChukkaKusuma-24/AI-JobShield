"""Comprehensive evaluation and comparison script for the retrained ML model."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import PredefinedSplit
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "ml"))
sys.path.insert(0, str(ROOT / "tests"))

from preprocess import preprocess_text
from run_adversarial_ml_eval import variations
from run_benchmark_step4 import BENCHMARK_CASES


def train_and_evaluate():
    # 1. Load V2 Dataset
    data_path = ROOT / "data" / "training_data_v2.csv"
    df = pd.read_csv(data_path)

    # 2. Leakage-Resistant Stratified Group Split
    rng = np.random.RandomState(42)
    train_idx, val_idx, test_idx = [], [], []

    for label in [0, 1]:
        sub = df[df["label"] == label]
        groups = list(sub["group_id"].unique())
        rng.shuffle(groups)
        n_total = len(sub)
        n_train = int(n_total * 0.70)
        n_val = int(n_total * 0.15)
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

    X_train = [preprocess_text(t) for t in df.loc[train_idx, "text"]]
    y_train = list(df.loc[train_idx, "label"])
    X_val = [preprocess_text(t) for t in df.loc[val_idx, "text"]]
    y_val = list(df.loc[val_idx, "label"])
    X_test = [preprocess_text(t) for t in df.loc[test_idx, "text"]]
    y_test = list(df.loc[test_idx, "label"])

    X_train_val = X_train + X_val
    y_train_val = y_train + y_val
    test_fold = [-1] * len(X_train) + [0] * len(X_val)
    ps = PredefinedSplit(test_fold)

    # 3. Fit Pipeline
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
    clf = LogisticRegression(class_weight="balanced", random_state=42, C=1.0, max_iter=1000, solver="liblinear")
    cal = CalibratedClassifierCV(estimator=clf, cv=ps, method="sigmoid")
    pipe = Pipeline([("tfidf", vec), ("clf", cal)])

    pipe.fit(X_train_val, y_train_val)
    cal.coef_ = cal.calibrated_classifiers_[0].estimator.coef_

    # 4. Untouched Test Set Evaluation
    y_pred_proba = pipe.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba >= 0.5).astype(int)

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc = roc_auc_score(y_test, y_pred_proba)
    pr_auc = average_precision_score(y_test, y_pred_proba)
    brier = brier_score_loss(y_test, y_pred_proba)
    cm = confusion_matrix(y_test, y_pred)

    print("==================================================")
    print("1. UNTOUCHED HOLDOUT TEST SET (N = %d)" % len(y_test))
    print("==================================================")
    print(f"Accuracy:        {acc:.4f} ({acc*100:.2f}%)")
    print(f"Precision:       {prec:.4f} ({prec*100:.2f}%)")
    print(f"Recall:          {rec:.4f} ({rec*100:.2f}%)")
    print(f"F1-Score:        {f1:.4f}")
    print(f"ROC-AUC:         {roc:.4f}")
    print(f"PR-AUC:          {pr_auc:.4f}")
    print(f"Brier Score:     {brier:.4f}")
    print("Confusion Matrix:")
    print(f"  TN={cm[0,0]:<3} FP={cm[0,1]:<3}")
    print(f"  FN={cm[1,0]:<3} TP={cm[1,1]:<3}")

    # 5. Top Contributing Features Inspection
    feature_names = np.array(vec.get_feature_names_out())
    coefs = cal.coef_[0]
    top_scam_idx = np.argsort(coefs)[::-1][:20]
    top_legit_idx = np.argsort(coefs)[:20]

    print("\n==================================================")
    print("2. TOP SCAM-ASSOCIATED FEATURES")
    print("==================================================")
    for idx in top_scam_idx:
        print(f"  {feature_names[idx]:<25} : {coefs[idx]:+.4f}")

    print("\n==================================================")
    print("3. TOP LEGITIMATE-ASSOCIATED FEATURES")
    print("==================================================")
    for idx in top_legit_idx:
        print(f"  {feature_names[idx]:<25} : {coefs[idx]:+.4f}")

    # Check sensitive terms
    sensitive_terms = ["bank", "account", "payment", "crypto", "telegram", "whatsapp", "remote", "salary", "tcs", "infosys"]
    print("\n==================================================")
    print("4. SENSITIVE TERM WEIGHT CHECK")
    print("==================================================")
    for term in sensitive_terms:
        if term in vec.vocabulary_:
            idx = vec.vocabulary_[term]
            print(f"  Term '{term:<10}' weight: {coefs[idx]:+.4f}")
        else:
            print(f"  Term '{term:<10}' NOT in vocabulary (masked or filtered)")

    # 6. Benchmark Cases Evaluation
    print("\n==================================================")
    print("5. 15 BENCHMARK CASES EVALUATION")
    print("==================================================")
    print(f"{'ID':<3} | {'Case Name':<31} | {'Cat':<5} | {'P(scam)':<8} | {'Pred':<4}")
    print("-" * 60)
    for c in BENCHMARK_CASES:
        combined = f"{c['title']} {c['company_name']} {c['description']} {c.get('salary', '')}"
        clean = preprocess_text(combined)
        p_scam = pipe.predict_proba([clean])[0][1]
        pred = 1 if p_scam >= 0.5 else 0
        cat_short = "Legit" if c["category"] == "Legitimate" else "Scam"
        print(f"{c['id']:<3} | {c['name']:<31} | {cat_short:<5} | {p_scam:<8.4f} | {pred:<4}")

    # 7. Adversarial Cases Evaluation
    print("\n==================================================")
    print("6. ADVERSARIAL CASES EVALUATION (16 CASES)")
    print("==================================================")
    print(f"{'Key':<32} | {'True':<5} | {'P(scam)':<8} | {'Pred':<4}")
    print("-" * 60)
    for k, v in variations.items():
        combined = f"{v['title']} {v['company']} {v['text']} {v.get('salary', '')}"
        clean = preprocess_text(combined)
        p_scam = pipe.predict_proba([clean])[0][1]
        pred = 1 if p_scam >= 0.5 else 0
        true_label = "Legit" if k.startswith(("A", "C")) else "Scam"
        print(f"{k:<32} | {true_label:<5} | {p_scam:<8.4f} | {pred:<4}")

    return pipe, vec


if __name__ == "__main__":
    train_and_evaluate()
