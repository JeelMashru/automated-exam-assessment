"""
Unit tests for Database Repository, Human Overrides, and Audit Trail persistence.
"""

import pytest
from database.db import init_db, get_db
from database.models import Assessment, Submission, Evaluation, AuditLog
from database.repository import AssessmentRepository


@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()


def test_assessment_creation_and_retrieval():
    assessment = AssessmentRepository.create_assessment(
        title="Test Examination 2026",
        subject="Computer Architecture",
        course_code="CS202",
        institution="Dept of CS",
        questions_data=[
            {
                "question_text": "Define cache coherence and write-through policy.",
                "maximum_marks": 10.0,
                "model_answer": "Cache coherence ensures that multiple caches in a multiprocessor system reflect updated data.",
                "rubric": [
                    {"criterion_name": "Accuracy", "maximum_marks": 5.0},
                    {"criterion_name": "Completeness", "maximum_marks": 5.0},
                ]
            }
        ]
    )

    assert assessment.id is not None
    assert assessment.title == "Test Examination 2026"

    # Add submission and evaluation
    sub = AssessmentRepository.add_submission(
        assessment_id=assessment.id,
        student_identifier="TEST_STU_01",
        original_filename="test.pdf",
        file_path="uploads/test.pdf",
        extracted_text="Cache coherence keeps caches consistent.",
        page_count=1,
        word_count=5
    )

    ev = AssessmentRepository.save_evaluation(
        submission_id=sub.id,
        question_id=assessment.questions[0].id,
        maximum_marks=10.0,
        ai_awarded_marks=6.0,
        criteria_scores=[{"criterion": "Accuracy", "maximum_marks": 5.0, "awarded_marks": 3.0}],
        strengths=["Basic coherence defined"],
        conceptual_gaps=["Omitted write-through policy"],
        improvement_suggestions=["Explain write-through mechanics"],
        review_status="Pending Human Review"
    )

    assert ev.ai_awarded_marks == 6.0
    assert ev.final_awarded_marks == 6.0

    # Perform Human Override
    updated_ev = AssessmentRepository.override_evaluation(
        evaluation_id=ev.id,
        new_score=7.0,
        comments="Awarded 1 mark extra for succinct phrasing.",
        reviewer_name="Dr. Examiner",
        status="Approved"
    )

    assert updated_ev.final_awarded_marks == 7.0
    assert updated_ev.review_status == "Approved"

    # Verify Audit Trail
    audit_trail = AssessmentRepository.get_audit_trail(ev.id)
    assert len(audit_trail) >= 1
    assert audit_trail[0]["previous_score"] == 6.0
    assert audit_trail[0]["new_score"] == 7.0
    assert audit_trail[0]["changed_by"] == "Dr. Examiner"
