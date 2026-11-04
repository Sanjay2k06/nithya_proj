"""
Evaluation Metrics Computation (Accuracy, Precision, Recall, F1, Confusion Matrix).
"""

from typing import Dict, Any, List
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

from ml.config import CLASS_NAMES


def compute_metrics(
    y_true: List[int],
    y_pred: List[int],
    class_names: List[str] = CLASS_NAMES
) -> Dict[str, Any]:
    """
    Computes standard academic and industrial evaluation metrics.
    """
    y_t = np.array(y_true)
    y_p = np.array(y_pred)

    acc = float(accuracy_score(y_t, y_p))
    macro_prec = float(precision_score(y_t, y_p, average="macro", zero_division=0))
    macro_rec = float(recall_score(y_t, y_p, average="macro", zero_division=0))
    macro_f1 = float(f1_score(y_t, y_p, average="macro", zero_division=0))

    per_class_prec = precision_score(y_t, y_p, average=None, zero_division=0).tolist()
    per_class_rec = recall_score(y_t, y_p, average=None, zero_division=0).tolist()
    per_class_f1 = f1_score(y_t, y_p, average=None, zero_division=0).tolist()

    cm = confusion_matrix(y_t, y_p, labels=list(range(len(class_names)))).tolist()

    per_class_summary = {}
    for idx, name in enumerate(class_names):
        per_class_summary[name] = {
            "precision": float(per_class_prec[idx]) if idx < len(per_class_prec) else 0.0,
            "recall": float(per_class_rec[idx]) if idx < len(per_class_rec) else 0.0,
            "f1_score": float(per_class_f1[idx]) if idx < len(per_class_f1) else 0.0,
        }

    return {
        "accuracy": acc,
        "macro_precision": macro_prec,
        "macro_recall": macro_rec,
        "macro_f1": macro_f1,
        "per_class": per_class_summary,
        "confusion_matrix": cm,
        "class_names": class_names,
        "total_samples": len(y_true)
    }
