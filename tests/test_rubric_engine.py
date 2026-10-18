"""
Unit tests for Rubric Engine validation and boundary checking.
"""

import pytest
from core.rubric_engine import RubricEngine


def test_valid_rubric_sum():
    criteria = [
        {"criterion_name": "Technical Accuracy", "maximum_marks": 4.0},
        {"criterion_name": "Completeness", "maximum_marks": 3.0},
        {"criterion_name": "Terminology", "maximum_marks": 3.0},
    ]
    is_valid, msg = RubricEngine.validate_question_rubric(10.0, criteria)
    assert is_valid is True
    assert "valid" in msg.lower()


def test_invalid_rubric_sum_mismatch():
    criteria = [
        {"criterion_name": "Technical Accuracy", "maximum_marks": 4.0},
        {"criterion_name": "Completeness", "maximum_marks": 3.0},
    ]  # Sum = 7.0, expected = 10.0
    is_valid, msg = RubricEngine.validate_question_rubric(10.0, criteria)
    assert is_valid is False
    assert "does not match" in msg


def test_empty_criteria_rejected():
    is_valid, msg = RubricEngine.validate_question_rubric(10.0, [])
    assert is_valid is False
    assert "at least one criterion" in msg


def test_negative_or_zero_criterion_marks():
    criteria = [
        {"criterion_name": "Negative Criterion", "maximum_marks": -2.0},
        {"criterion_name": "Remaining Marks", "maximum_marks": 12.0},
    ]
    is_valid, msg = RubricEngine.validate_question_rubric(10.0, criteria)
    assert is_valid is False
    assert "strictly positive" in msg


def test_default_rubric_scaling():
    rubric = RubricEngine.create_default_rubric(max_marks=15.0)
    assert len(rubric) == 3
    total_m = sum(c["maximum_marks"] for c in rubric)
    assert abs(total_m - 15.0) < 1e-4
