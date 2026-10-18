"""
Unit tests for BLEU, ROUGE-L, and similarity metrics.
"""

import pytest
from core.similarity_metrics import SimilarityMetrics


def test_identical_texts_high_similarity():
    ref = "Virtual memory creates an illusion of a large main memory space using paging."
    cand = "Virtual memory creates an illusion of a large main memory space using paging."

    metrics = SimilarityMetrics.compute_all_metrics(ref, cand)
    assert metrics["bleu_score"] > 90.0
    assert metrics["rouge_l_score"] > 90.0


def test_partial_overlap_similarity():
    ref = "Virtual memory creates an illusion of a large main memory space using paging."
    cand = "Paging is a memory management technique used in computers to load pages."

    metrics = SimilarityMetrics.compute_all_metrics(ref, cand)
    assert 0.0 <= metrics["bleu_score"] <= 100.0
    assert 0.0 <= metrics["rouge_l_score"] <= 100.0


def test_empty_string_handling():
    metrics = SimilarityMetrics.compute_all_metrics("", "")
    assert metrics["bleu_score"] == 0.0
    assert metrics["rouge_l_score"] == 0.0

    metrics_half = SimilarityMetrics.compute_all_metrics("Some model reference", "")
    assert metrics_half["bleu_score"] == 0.0
    assert metrics_half["rouge_l_score"] == 0.0
