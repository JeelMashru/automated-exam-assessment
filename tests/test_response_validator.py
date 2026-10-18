"""
Unit tests for Response Validator, JSON cleaning, and Pydantic schema validation.
"""

import pytest
import json
from core.response_validator import ResponseValidator


def test_clean_json_string_with_markdown_ticks():
    raw = "```json\n{\n  \"assessment_id\": \"A1\",\n  \"student_id\": \"S1\"\n}\n```"
    cleaned = ResponseValidator.clean_json_string(raw)
    assert cleaned.startswith("{")
    assert cleaned.endswith("}")
    parsed = json.loads(cleaned)
    assert parsed["assessment_id"] == "A1"


def test_clean_json_with_conversational_chatter():
    raw = "Here is your requested evaluation:\n\n{\"assessment_id\": \"A1\", \"student_id\": \"S1\"}\n\nHope this helps!"
    cleaned = ResponseValidator.clean_json_string(raw)
    assert cleaned == "{\"assessment_id\": \"A1\", \"student_id\": \"S1\"}"


def test_valid_llm_json_validation():
    valid_payload = {
        "assessment_id": "ASSESS_101",
        "student_id": "STUD_202",
        "question_id": "Q1",
        "maximum_marks": 10.0,
        "awarded_marks": 7.5,
        "criteria": [
            {
                "criterion": "Technical Accuracy",
                "maximum_marks": 5.0,
                "awarded_marks": 4.0,
                "evidence": "Accurate definitions",
                "justification": "Good explanation",
                "missing_concepts": [],
                "errors": []
            },
            {
                "criterion": "Terminology",
                "maximum_marks": 5.0,
                "awarded_marks": 3.5,
                "evidence": "Used proper terms",
                "justification": "Clear terminology",
                "missing_concepts": [],
                "errors": []
            }
        ],
        "strengths": ["Clear definitions"],
        "conceptual_gaps": ["No diagrams"],
        "improvement_suggestions": ["Add diagrams"],
        "review_required": True,
        "review_status": "Pending Human Review"
    }

    raw_str = json.dumps(valid_payload)
    success, res_dict, err = ResponseValidator.validate_and_compute(raw_str, expected_question_max_marks=10.0)

    assert success is True
    assert err is None
    assert res_dict["awarded_marks"] == 7.5
    assert len(res_dict["criteria"]) == 2


def test_malformed_json_failure():
    bad_json = "{'invalid_json': true, missing_quotes_key: }"
    success, res_dict, err = ResponseValidator.validate_and_compute(bad_json, expected_question_max_marks=10.0)
    assert success is False
    assert "JSON parse error" in err
