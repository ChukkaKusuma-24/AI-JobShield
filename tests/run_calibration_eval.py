"""Calibration and Distribution analysis for JobShield ML model."""
import sys
import csv
from pathlib import Path
import numpy as np

root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(root_dir / "tests"))
sys.path.insert(0, str(root_dir / "ml"))

from app.services import ml_service
from sklearn.metrics import brier_score_loss
from sklearn.calibration import calibration_curve

ml_service.load_model()
pipe = ml_service._state["pipeline"]

# Load demo synthetic dataset
data_path = root_dir / "data" / "demo_training_data.csv"
texts = []
labels = []
with open(data_path, "r", encoding="utf-8") as f:
    for row in csv.reader(f):
        if not row or row[0].startswith("#") or row[0] == "text":
            continue
        texts.append(row[0])
        labels.append(int(row[1]))

from preprocess import preprocess_text
clean_texts = [preprocess_text(t) for t in texts]
probas = pipe.predict_proba(clean_texts)[:, 1]

brier = brier_score_loss(labels, probas)
print(f"Dataset Total N: {len(labels)}")
print(f"Overall Synthetic Brier Score: {brier:.4f}")

# Distribution of probabilities on synthetic dataset
bins = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
hist, _ = np.histogram(probas, bins=bins)
print("\nSynthetic Probability Distribution:")
for i in range(len(hist)):
    print(f"[{bins[i]:.1f}, {bins[i+1]:.1f}): {hist[i]} ({hist[i]/len(probas)*100:.1f}%)")

# Calibration curve on synthetic dataset
prob_true, prob_pred = calibration_curve(labels, probas, n_bins=5)
print("\nCalibration Curve (Synthetic):")
for pt, pp in zip(prob_true, prob_pred):
    print(f"Mean Predicted P: {pp:.4f} | True Fraction: {pt:.4f}")

# Benchmark cases + Adversarial cases evaluation
from run_benchmark_step4 import BENCHMARK_CASES as bench_cases

real_texts = []
real_labels = []
real_names = []
# Cases 1, 2, 3, 13, 14, 15 are legitimate (label 0)
# Cases 6, 7, 8, 9, 10, 11, 12 are scam texts (label 1)
# Note: Cases 4 and 5 are legitimate text used by scammers (impersonation).
# If we test text-only scam classification:
for c in bench_cases:
    if c["id"] in [4, 5]:
        continue # Impersonation where text is legitimate
    txt = f"{c['title']} {c['company_name']} {c['description']} {c.get('salary', '')}"
    real_texts.append(txt)
    real_names.append(c["name"])
    real_labels.append(0 if c["category"] == "legitimate" else 1)

from run_adversarial_ml_eval import variations
for k, v in variations.items():
    txt = f"{v['title']} {v['company']} {v['text']} {v.get('salary', '')}"
    real_texts.append(txt)
    real_names.append(k)
    # A & C are legitimate (0), B & D are scam (1)
    real_labels.append(0 if k.startswith(("A", "C")) else 1)

clean_real = [preprocess_text(t) for t in real_texts]
real_probas = pipe.predict_proba(clean_real)[:, 1]
real_preds = (real_probas >= 0.5).astype(int)

from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

print("\n--- Realistic & Adversarial Test Set Evaluation ---")
print(f"Total Non-Synthetic Cases N: {len(real_labels)}")
print(f"Brier Score: {brier_score_loss(real_labels, real_probas):.4f}")
print(f"Accuracy: {accuracy_score(real_labels, real_preds):.4f}")
print(f"Precision: {precision_score(real_labels, real_preds):.4f}")
print(f"Recall: {recall_score(real_labels, real_preds):.4f}")
print(f"F1 Score: {f1_score(real_labels, real_preds):.4f}")
print(f"ROC-AUC: {roc_auc_score(real_labels, real_probas):.4f}")

hist_real, _ = np.histogram(real_probas, bins=bins)
print("\nReal-World / Adversarial Probability Distribution:")
for i in range(len(hist_real)):
    print(f"[{bins[i]:.1f}, {bins[i+1]:.1f}): {hist_real[i]} ({hist_real[i]/len(real_probas)*100:.1f}%)")

