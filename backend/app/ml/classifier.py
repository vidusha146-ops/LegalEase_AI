"""
LegalEase AI - Machine Learning Legal Problem Classifier
Combines domain-specific TF-IDF feature extraction with balanced Logistic Regression.
Evaluated via Stratified 5-Fold Cross-Validation with Macro-F1 and Confusion Matrix.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline

from app.core.constants import LEGAL_DOMAINS
from app.ml.preprocessor import LegalTextPreprocessor

logger = logging.getLogger(__name__)

CURRENT_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = CURRENT_DIR / "artifacts"
DATA_DIR = CURRENT_DIR / "data"
CORPUS_PATH = DATA_DIR / "legal_problems_corpus.json"
MODEL_PATH = ARTIFACTS_DIR / "legal_domain_classifier.joblib"
METRICS_PATH = ARTIFACTS_DIR / "evaluation_metrics.json"


class LegalProblemClassifier:
    """
    ML Classifier for categorizing Indian citizen legal grievances
    into the 10 statutory legal domains.
    """

    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or MODEL_PATH
        self.pipeline: Optional[Pipeline] = None
        self.classes: List[str] = sorted(LEGAL_DOMAINS)
        self.metrics: Optional[Dict[str, Any]] = None

    def _build_pipeline(self) -> Pipeline:
        """Constructs the standard Scikit-Learn pipeline."""
        return Pipeline(
            [
                (
                    "tfidf",
                    TfidfVectorizer(
                        preprocessor=LegalTextPreprocessor.clean,
                        ngram_range=(1, 2),
                        min_df=1,
                        max_df=0.95,
                        sublinear_tf=True,
                    ),
                ),
                (
                    "clf",
                    LogisticRegression(
                        C=2.5,
                        max_iter=1000,
                        class_weight="balanced",
                        solver="lbfgs",
                        random_state=42,
                    ),
                ),
            ]
        )

    def load_dataset(self) -> Tuple[List[str], List[str]]:
        """Loads documented grievance corpus from JSON."""
        if not CORPUS_PATH.exists():
            raise FileNotFoundError(f"Corpus file not found at {CORPUS_PATH}")
        with open(CORPUS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        texts = [item["text"] for item in data]
        labels = [item["domain"] for item in data]
        return texts, labels

    def train_and_evaluate(self, n_splits: int = 5) -> Dict[str, Any]:
        """
        Executes Stratified K-Fold Cross-Validation to prevent data leakage,
        computes Macro-F1, Precision, Recall, and Confusion Matrix,
        then trains the final model on the full dataset and saves artifacts.
        """
        texts, labels = self.load_dataset()
        X = np.array(texts)
        y = np.array(labels)

        unique_labels = sorted(list(set(y)))
        self.classes = unique_labels

        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        y_true_all = []
        y_pred_all = []

        fold_f1_scores = []

        for fold, (train_idx, test_idx) in enumerate(skf.split(X, y), 1):
            fold_pipe = self._build_pipeline()
            fold_pipe.fit(X[train_idx], y[train_idx])
            y_pred = fold_pipe.predict(X[test_idx])

            y_true_all.extend(y[test_idx])
            y_pred_all.extend(y_pred)

            _, _, f1, _ = precision_recall_fscore_support(
                y[test_idx], y_pred, average="macro", zero_division=0
            )
            fold_f1_scores.append(float(f1))

        # Overall Cross-Validation Metrics
        p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(
            y_true_all, y_pred_all, average="macro", zero_division=0
        )
        p_weighted, r_weighted, f1_weighted, _ = precision_recall_fscore_support(
            y_true_all, y_pred_all, average="weighted", zero_division=0
        )

        cm = confusion_matrix(y_true_all, y_pred_all, labels=unique_labels).tolist()
        class_rep = classification_report(
            y_true_all, y_pred_all, labels=unique_labels, output_dict=True, zero_division=0
        )

        # Train final pipeline on 100% of the dataset
        self.pipeline = self._build_pipeline()
        self.pipeline.fit(X, y)

        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.pipeline, self.model_path)

        metrics = {
            "n_samples": len(texts),
            "n_classes": len(unique_labels),
            "classes": unique_labels,
            "cv_splits": n_splits,
            "macro_precision": round(float(p_macro), 4),
            "macro_recall": round(float(r_macro), 4),
            "macro_f1": round(float(f1_macro), 4),
            "weighted_f1": round(float(f1_weighted), 4),
            "fold_f1_scores": [round(f, 4) for f in fold_f1_scores],
            "confusion_matrix": cm,
            "classification_report": class_rep,
            "dataset_limitations": [
                "Dataset comprises 114 curated realistic Indian citizen grievance scenarios.",
                "Cross-domain overlaps exist between Cyber Fraud and Consumer Disputes.",
                "Real citizen inquiries may contain multi-lingual Hinglish code-switching.",
                "Continuous performance evaluation and active learning retraining recommended."
            ],
        }

        with open(METRICS_PATH, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)

        self.metrics = metrics
        logger.info(f"Model saved to {self.model_path} with Macro-F1: {metrics['macro_f1']}")
        return metrics

    def ensure_model_loaded(self) -> None:
        """Loads saved model pipeline or triggers training if not present."""
        if self.pipeline is not None:
            return

        if self.model_path.exists():
            self.pipeline = joblib.load(self.model_path)
            self.classes = list(self.pipeline.classes_)
            if METRICS_PATH.exists():
                with open(METRICS_PATH, "r", encoding="utf-8") as f:
                    self.metrics = json.load(f)
        else:
            logger.info("No saved classifier artifact found. Training now...")
            self.train_and_evaluate()

    def predict(self, text: str) -> Dict[str, Any]:
        """
        Predicts the legal domain for a citizen grievance narrative.
        Returns top prediction, confidence probability, and top 3 candidate domains.
        """
        self.ensure_model_loaded()
        if not text or not text.strip():
            return {
                "predicted_domain": "GENERAL_LEGAL_INQUIRY",
                "confidence": 0.0,
                "probabilities": {},
                "top_domains": [],
            }

        probs = self.pipeline.predict_proba([text])[0]
        classes = list(self.pipeline.classes_)

        prob_dict = {cls: round(float(prob), 4) for cls, prob in zip(classes, probs)}
        sorted_domains = sorted(prob_dict.items(), key=lambda x: x[1], reverse=True)

        top_domain, top_prob = sorted_domains[0]

        return {
            "predicted_domain": top_domain,
            "confidence": top_prob,
            "probabilities": prob_dict,
            "top_domains": [
                {"domain": d, "confidence": p} for d, p in sorted_domains[:3]
            ],
        }


# Singleton instance
_classifier_instance: Optional[LegalProblemClassifier] = None


def get_classifier() -> LegalProblemClassifier:
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = LegalProblemClassifier()
        _classifier_instance.ensure_model_loaded()
    return _classifier_instance
