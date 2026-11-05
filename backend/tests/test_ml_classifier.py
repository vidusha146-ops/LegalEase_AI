"""
LegalEase AI - Automated Tests for Machine Learning Legal Problem Classifier
"""

import json
from pathlib import Path
import pytest

from app.ml.preprocessor import LegalTextPreprocessor
from app.ml.classifier import (
    LegalProblemClassifier,
    get_classifier,
    CORPUS_PATH,
    MODEL_PATH,
    METRICS_PATH,
)
from app.core.constants import LEGAL_DOMAINS


def test_dataset_integrity():
    """Verifies that the legal problem corpus contains all required domains and valid structure."""
    assert CORPUS_PATH.exists()
    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) >= 100
    domains_present = set(item["domain"] for item in data)
    for expected_domain in LEGAL_DOMAINS:
        assert expected_domain in domains_present, f"Domain {expected_domain} missing from dataset"

    for item in data:
        assert len(item["text"].strip()) >= 20
        assert item["domain"] in LEGAL_DOMAINS
        assert "sub_category" in item
        assert "key_ingredients" in item


def test_preprocessor_cleaning():
    """Verifies domain-specific text preprocessing and stop-word preservation."""
    sample = "I paid Rs. 45,000 via UPI on https://fakebank.com, but received NO goods and seller DENIED refund! Ref F.I.R."
    cleaned = LegalTextPreprocessor.clean(sample)

    # Check normalization
    assert "rupees_45000" in cleaned
    assert "unified_payments_interface_upi" in cleaned
    assert "fir_police_complaint" in cleaned
    assert "https" not in cleaned
    # Preserved statutory markers
    assert "no" in cleaned
    assert "denied" in cleaned


def test_classifier_cross_validation_and_artifacts():
    """Verifies that the trained model and cross-validation metrics are persistent and valid."""
    classifier = get_classifier()
    assert MODEL_PATH.exists()
    assert METRICS_PATH.exists()

    with open(METRICS_PATH, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    assert metrics["n_classes"] == 10
    assert metrics["cv_splits"] == 5
    assert 0.0 < metrics["macro_f1"] <= 1.0
    assert 0.0 < metrics["macro_precision"] <= 1.0
    assert 0.0 < metrics["macro_recall"] <= 1.0
    assert len(metrics["confusion_matrix"]) == 10
    assert len(metrics["dataset_limitations"]) > 0


def test_classifier_predictions():
    """Tests ML domain inference across representative citizen grievances."""
    classifier = get_classifier()

    # 1. Cheque Bounce
    res_cheque = classifier.predict("Client gave cheque of Rs 2 lakhs which bounced for insufficient funds. Need to send 138 notice.")
    assert res_cheque["predicted_domain"] == "CHEQUE_BOUNCE_NI_ACT"
    assert res_cheque["confidence"] > 0.20

    # 2. RTI Query
    res_rti = classifier.predict("Filed RTI application with municipal corporation 40 days ago regarding road contract budget, no response received.")
    assert res_rti["predicted_domain"] == "RTI_GOVERNANCE"

    # 3. Consumer Dispute
    res_consumer = classifier.predict("Purchased washing machine with 2 year warranty. Motor burned in 2 months and dealer refuses replacement.")
    assert res_consumer["predicted_domain"] == "CONSUMER_PROTECTION"
