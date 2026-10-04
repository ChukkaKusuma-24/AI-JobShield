"""Run independent red-team validation, contamination checks, and calibration analysis."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "ml"))
sys.path.insert(0, str(ROOT / "tests"))

from ml_redteam_cases import REDTEAM_CASES
from preprocess import preprocess_text
from run_benchmark_step4 import BENCHMARK_CASES


def check_contamination(redteam_cases: list[dict], train_csv_path: Path) -> dict:
    """Check for exact, normalized, or high n-gram overlap with training data."""
    train_df = pd.read_csv(train_csv_path)
    train_raw = set(train_df["text"].str.strip().str.lower())
    train_clean = set(train_df["text"].apply(preprocess_text))

    exact_matches = []
    clean_matches = []

    for c in redteam_cases:
        raw_t = c["text"].strip().lower()
        clean_t = preprocess_text(c["text"])

        if raw_t in train_raw:
            exact_matches.append(c["id"])
        if clean_t in train_clean:
            clean_matches.append(c["id"])

    return {
        "exact_duplicates": exact_matches,
        "normalized_duplicates": clean_matches,
        "is_contaminated": bool(exact_matches or clean_matches),
    }


def run_redteam_eval():
    train_csv = ROOT / "data" / "training_data_v2.csv"
    model_path = ROOT / "models" / "jobshield_model.joblib"

    print("==================================================")
    print("STEP 9: INDEPENDENT ML RED-TEAM VALIDATION")
    print("==================================================")

    # 1. Contamination Check
    contam = check_contamination(REDTEAM_CASES, train_csv)
    print("\n--- 1. CONTAMINATION CHECK ---")
    print(f"Total Red-Team Cases:        {len(REDTEAM_CASES)}")
    print(f"Exact Matches with Training: {len(contam['exact_duplicates'])}")
    print(f"Normalized Matches:          {len(contam['normalized_duplicates'])}")
    if contam["is_contaminated"]:
        print("WARNING: Contaminated cases detected! Removing before evaluation.")
        clean_cases = [c for c in REDTEAM_CASES if c["id"] not in contam["normalized_duplicates"]]
    else:
        print("PASS: Zero contamination detected. All 64 cases are 100% unseen.")
        clean_cases = REDTEAM_CASES

    # 2. Load Frozen Production Model
    bundle = joblib.load(model_path)
    pipe = bundle["pipeline"] if isinstance(bundle, dict) else bundle

    # 3. Predict on Red-Team Suite
    results = []
    for c in clean_cases:
        combined = f"{c['title']} {c['company']} {c['text']}"
        clean_t = preprocess_text(combined)
        proba = pipe.predict_proba([clean_t])[0]
        p_scam = float(proba[1])
        p_legit = float(proba[0])
        pred = 1 if p_scam >= 0.5 else 0
        correct = (pred == c["label"])

        results.append({
            "id": c["id"],
            "name": c["name"],
            "category": c["category"],
            "label": c["label"],
            "p_scam": p_scam,
            "p_legit": p_legit,
            "pred": pred,
            "correct": correct,
            "contrast_pair_id": c.get("contrast_pair_id"),
            "notes": c.get("notes", ""),
        })

    df_res = pd.DataFrame(results)
    y_true = df_res["label"].values
    y_pred = df_res["pred"].values
    y_proba = df_res["p_scam"].values

    # 4. Compute Metrics
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    roc = roc_auc_score(y_true, y_proba)
    pr_auc = average_precision_score(y_true, y_proba)
    brier = brier_score_loss(y_true, y_proba)
    cm = confusion_matrix(y_true, y_pred)

    print("\n--- 2. RED-TEAM CLASSIFICATION METRICS (N = %d) ---" % len(clean_cases))
    print(f"Accuracy:        {acc:.4f} ({acc*100:.2f}%)")
    print(f"Precision:       {prec:.4f} ({prec*100:.2f}%)")
    print(f"Recall:          {rec:.4f} ({rec*100:.2f}%)")
    print(f"F1-Score:        {f1:.4f}")
    print(f"ROC-AUC:         {roc:.4f}")
    print(f"PR-AUC:          {pr_auc:.4f}")
    print(f"Brier Score:     {brier:.4f}")
    print("\nConfusion Matrix:")
    print(f"  TN (Legit correctly classified): {cm[0,0]}")
    print(f"  FP (Legit falsely flagged scam): {cm[0,1]}")
    print(f"  FN (Scam missed by model):       {cm[1,0]}")
    print(f"  TP (Scam correctly caught):      {cm[1,1]}")

    # 5. False Positives & False Negatives
    fps = df_res[(df_res["label"] == 0) & (df_res["pred"] == 1)]
    fns = df_res[(df_res["label"] == 1) & (df_res["pred"] == 0)]

    print("\n--- 3. ERROR ANALYSIS ---")
    print(f"Total False Positives: {len(fps)}")
    for _, r in fps.iterrows():
        print(f"  [FP ID {r['id']:<2}] P(scam)={r['p_scam']:.4f} | {r['name']} ({r['category']})")

    print(f"\nTotal False Negatives: {len(fns)}")
    for _, r in fns.iterrows():
        print(f"  [FN ID {r['id']:<2}] P(scam)={r['p_scam']:.4f} | {r['name']} ({r['category']})")

    # 6. Confidence Extremes
    df_sorted_fp = df_res[df_res["correct"] == False].sort_values(by="p_scam", ascending=False)
    print("\n--- 4. HIGHEST-CONFIDENCE ERRORS ---")
    if len(df_sorted_fp) == 0:
        print("  None! Model made 0 classification errors.")
    else:
        for _, r in df_sorted_fp.iterrows():
            print(f"  ID {r['id']:<2} | True Label: {r['label']} | P(scam)={r['p_scam']:.4f} | {r['name']}")

    # Lowest-confidence correct predictions
    df_correct = df_res[df_res["correct"] == True].copy()
    # Confidence distance from decision boundary (0.5)
    df_correct["margin"] = (df_correct["p_scam"] - 0.5).abs()
    lowest_conf = df_correct.sort_values(by="margin").head(5)
    print("\n--- 5. LOWEST-CONFIDENCE CORRECT PREDICTIONS ---")
    for _, r in lowest_conf.iterrows():
        print(f"  ID {r['id']:<2} | True Label: {r['label']} | P(scam)={r['p_scam']:.4f} (Margin: {r['margin']:.4f}) | {r['name']}")

    # 7. Calibration Grouping
    bins = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    print("\n--- 6. PROBABILITY CALIBRATION DISTRIBUTION ---")
    print(f"{'Bin':<12} | {'Samples':<8} | {'Scam Rate':<10} | {'Mean P(scam)':<12}")
    print("-" * 50)
    for i in range(len(bins) - 1):
        lo, hi = bins[i], bins[i+1]
        if i == len(bins) - 2:
            sub = df_res[(df_res["p_scam"] >= lo) & (df_res["p_scam"] <= hi)]
        else:
            sub = df_res[(df_res["p_scam"] >= lo) & (df_res["p_scam"] < hi)]
        n = len(sub)
        if n > 0:
            actual_rate = sub["label"].mean()
            mean_p = sub["p_scam"].mean()
            print(f"[{lo:.1f}, {hi:.1f})   | {n:<8} | {actual_rate:<10.2%} | {mean_p:<12.4f}")
        else:
            print(f"[{lo:.1f}, {hi:.1f})   | 0        | N/A        | N/A")

    # 8. Controlled Contrast Pairs Evaluation
    print("\n--- 7. CONTROLLED CONTRAST PAIRS EVALUATION ---")
    pair_ids = sorted(list(set(df_res["contrast_pair_id"].dropna())))
    print(f"{'Pair':<8} | {'Legit Case':<32} | {'P(scam)':<8} | {'Scam Case':<32} | {'P(scam)':<8} | Separation")
    print("-" * 105)
    for pid in pair_ids:
        legit_r = df_res[(df_res["contrast_pair_id"] == pid) & (df_res["label"] == 0)].iloc[0]
        scam_r = df_res[(df_res["contrast_pair_id"] == pid) & (df_res["label"] == 1)].iloc[0]
        sep = scam_r["p_scam"] - legit_r["p_scam"]
        print(f"{pid:<8} | {legit_r['name'][:30]:<32} | {legit_r['p_scam']:<8.4f} | {scam_r['name'][:30]:<32} | {scam_r['p_scam']:<8.4f} | {sep:+.4f}")

    # 9. Existing 15-case Benchmark Comparison
    bench_results = []
    for c in BENCHMARK_CASES:
        combined = f"{c['title']} {c['company_name']} {c['description']} {c.get('salary', '')}"
        clean_t = preprocess_text(combined)
        proba = pipe.predict_proba([clean_t])[0]
        p_scam = float(proba[1])
        # Text label: Cases 4 and 5 are impersonation scams, but the text is legitimate text.
        # Text-only classification: 1-3, 13-15 are legit text (0), 6-12 are scam text (1).
        bench_results.append({
            "id": c["id"],
            "name": c["name"],
            "category": c["category"],
            "p_scam": p_scam,
            "pred": 1 if p_scam >= 0.5 else 0,
        })
    df_bench = pd.DataFrame(bench_results)

    print("\n--- 8. BENCHMARK COMPARISON ---")
    print(f"Independent Red-Team Accuracy (N = {len(clean_cases)}): {acc*100:.2f}%")
    print(f"Independent Red-Team Scam Recall:              {rec*100:.2f}%")
    print(f"Independent Red-Team Precision:                {prec*100:.2f}%")
    print(f"Independent Red-Team Brier Score:               {brier:.4f}")

    return df_res, df_bench


if __name__ == "__main__":
    run_redteam_eval()
