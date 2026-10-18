"""
Unit tests for programmatic Score Calculator and bounding logic.
"""

import pytest
from core.score_calculator import ScoreCalculator


def test_score_calculation_normal():
    criteria = [
        {"criterion": "Accuracy", "maximum_marks": 4.0, "awarded_marks": 3.5},
        {"criterion": "Completeness", "maximum_marks": 3.0, "awarded_marks": 2.5},
        {"criterion": "Terminology", "maximum_marks": 3.0, "awarded_marks": 2.0},
    ]
    total, clamped = ScoreCalculator.calculate_total_and_clamp(criteria, question_max_marks=10.0)
    assert total == 8.0
    assert len(clamped) == 3


def test_score_clamping_exceeds_maximum():
    # LLM hallucinates 6.0 on a 4.0 criterion and 5.0 on a 3.0 criterion
    criteria = [
        {"criterion": "Accuracy", "maximum_marks": 4.0, "awarded_marks": 6.0},
        {"criterion": "Completeness", "maximum_marks": 3.0, "awarded_marks": 5.0},
    ]
    total, clamped = ScoreCalculator.calculate_total_and_clamp(criteria, question_max_marks=7.0)
    # Each criterion clamped to max (4.0 and 3.0)
    assert clamped[0]["awarded_marks"] == 4.0
    assert clamped[1]["awarded_marks"] == 3.0
    assert total == 7.0


def test_score_clamping_negative_marks():
    # Negative marks not allowed by default
    criteria = [
        {"criterion": "Accuracy", "maximum_marks": 4.0, "awarded_marks": -3.0},
    ]
    total, clamped = ScoreCalculator.calculate_total_and_clamp(criteria, question_max_marks=4.0, allow_negative=False)
    assert clamped[0]["awarded_marks"] == 0.0
    assert total == 0.0


def test_academic_grade_banding():
    grade, desc = ScoreCalculator.get_academic_grade_band(88.0)
    assert "Distinction" in grade

    grade_f, desc_f = ScoreCalculator.get_academic_grade_band(32.0)
    assert "Fail" in grade_f or "Unsatisfactory" in grade_f
