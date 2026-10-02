"""ML model load / predict service."""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from app.config import get_settings, ROOT_DIR

logger = logging.getLogger(__name__)

_state: dict[str, Any] = {"pipeline": None, "available": False}


def _ensure_preprocess_path():
    ml_dir = str(ROOT_DIR / "ml")
    if ml_dir not in sys.path:
        sys.path.insert(0, ml_dir)


def preprocess(text: str) -> str:
    _ensure_preprocess_path()
    from preprocess import preprocess_text

    return preprocess_text(text)


def _auto_train() -> bool:
    settings = get_settings()
    data = Path(settings.DEMO_DATA_PATH)
    model = Path(settings.ML_MODEL_PATH)
    try:
        _ensure_preprocess_path()
        if not data.exists():
            from generate_demo_data import generate
            import csv

            data.parent.mkdir(parents=True, exist_ok=True)
            rows = generate(400)
            with data.open("w", newline="", encoding="utf-8") as f:
                f.write("# DEMO SYNTHETIC DATASET\n")
                w = csv.DictWriter(f, fieldnames=["text", "label", "source"])
                w.writeheader()
                w.writerows(rows)

        sys.path.insert(0, str(ROOT_DIR / "ml"))
        from train import train

        train(data, model, settings.ML_ALTERNATIVE)
        return model.exists()
    except Exception as exc:
        logger.warning("Auto-train failed: %s", exc)
        return False


def load_model() -> bool:
    settings = get_settings()
    path = Path(settings.ML_MODEL_PATH)
    if not path.exists():
        logger.info("Model missing – attempting auto-train from demo data")
        if not _auto_train():
            _state["pipeline"] = None
            _state["available"] = False
            return False

    try:
        bundle = joblib.load(path)
        pipe = bundle["pipeline"] if isinstance(bundle, dict) else bundle
        _state["pipeline"] = pipe
        _state["available"] = True
        return True
    except Exception as exc:
        logger.warning("Failed to load model: %s", exc)
        _state["pipeline"] = None
        _state["available"] = False
        return False


def is_available() -> bool:
    return bool(_state.get("available") and _state.get("pipeline") is not None)


def predict(text: str) -> dict[str, Any]:
    if not is_available():
        return {"available": False, "scam_probability": None, "top_terms": []}

    pipe = _state["pipeline"]
    clean = preprocess(text)
    try:
        proba = None
        if hasattr(pipe, "predict_proba"):
            proba = float(pipe.predict_proba([clean])[0][1])
        else:
            pred = int(pipe.predict([clean])[0])
            proba = float(pred)

        top_terms = _top_contributing_terms(pipe, clean)
        return {
            "available": True,
            "scam_probability": round(proba, 4),
            "top_terms": top_terms,
        }
    except Exception as exc:
        logger.warning("ML predict failed: %s", exc)
        return {"available": False, "scam_probability": None, "top_terms": []}


def _top_contributing_terms(pipe, clean: str, k: int = 8) -> list[dict]:
    try:
        vec = pipe.named_steps["tfidf"]
        clf = pipe.named_steps["clf"]
        X = vec.transform([clean])
        feature_names = np.array(vec.get_feature_names_out())
        row = X.toarray()[0]
        nonzero = np.where(row > 0)[0]
        if nonzero.size == 0:
            return []

        if hasattr(clf, "coef_"):
            coefs = clf.coef_[0]
            scores = row[nonzero] * coefs[nonzero]
        else:
            # Naive Bayes: use feature log probs difference if available
            if hasattr(clf, "feature_log_prob_"):
                scores = row[nonzero] * (
                    clf.feature_log_prob_[1][nonzero] - clf.feature_log_prob_[0][nonzero]
                )
            else:
                return []

        order = np.argsort(scores)[::-1][:k]
        terms = []
        for i in order:
            idx = nonzero[i]
            terms.append(
                {
                    "term": str(feature_names[idx]),
                    "weight": round(float(scores[i]), 4),
                }
            )
        return terms
    except Exception:
        return []
