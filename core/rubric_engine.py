"""
Rubric validation and configuration engine.
Ensures consistency, mathematical validity, and adherence to academic marking guidelines.
"""

from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field, field_validator


class RubricCriterionModel(BaseModel):
    criterion_name: str = Field(..., min_length=1, description="Name of the rubric criterion")
    maximum_marks: float = Field(..., gt=0, description="Maximum marks for this criterion")
    description: str = Field(default="", description="Description of the criterion")
    partial_credit_rules: str = Field(default="", description="Rules governing partial credit")
    expected_concepts: List[str] = Field(default_factory=list, description="Key concepts expected")
    critical_errors: List[str] = Field(default_factory=list, description="Errors that warrant penalty")


class QuestionRubricModel(BaseModel):
    question_text: str = Field(..., min_length=5)
    maximum_marks: float = Field(..., gt=0)
    model_answer: str = Field(..., min_length=10)
    evaluation_instructions: str = Field(default="")
    expected_keywords: List[str] = Field(default_factory=list)
    rubric: List[RubricCriterionModel] = Field(..., min_length=1)

    @field_validator("rubric")
    def validate_rubric_sum(cls, rubric, values):
        # We also validate this in validate_question_rubric to provide clear feedback
        return rubric


class RubricEngine:
    """Validates and formats grading rubrics."""

    TOLERANCE = 1e-4

    @classmethod
    def validate_question_rubric(
        cls,
        max_marks: float,
        criteria: List[Dict[str, Any]]
    ) -> Tuple[bool, str]:
        """
        Validates whether criteria marks sum exactly to question maximum marks.
        Returns:
            (is_valid: bool, message: str)
        """
        if not criteria:
            return False, "Rubric must contain at least one criterion."

        total_criterion_marks = 0.0
        for i, c in enumerate(criteria, start=1):
            name = c.get("criterion_name", "").strip()
            if not name:
                return False, f"Criterion #{i} must have a valid name."
            try:
                c_marks = float(c.get("maximum_marks", 0))
            except (ValueError, TypeError):
                return False, f"Criterion '{name}' has an invalid maximum mark value."

            if c_marks <= 0:
                return False, f"Criterion '{name}' maximum marks must be strictly positive (got {c_marks})."

            total_criterion_marks += c_marks

        if abs(total_criterion_marks - max_marks) > cls.TOLERANCE:
            return False, (
                f"Sum of criteria marks ({total_criterion_marks:.2f}) does not match "
                f"the question's total maximum marks ({max_marks:.2f}). "
                f"Difference: {total_criterion_marks - max_marks:+.2f} marks."
            )

        return True, "Rubric configuration is valid."

    @classmethod
    def create_default_rubric(cls, max_marks: float = 10.0) -> List[Dict[str, Any]]:
        """Provides a standard academic 3-tier default rubric scaled to max_marks."""
        tech_acc = round(max_marks * 0.4, 2)
        completeness = round(max_marks * 0.3, 2)
        terminology = round(max_marks - tech_acc - completeness, 2)

        return [
            {
                "criterion_name": "Technical Accuracy & Core Principles",
                "maximum_marks": tech_acc,
                "description": "Factual correctness, logical coherence, and accurate explanation of underlying concepts.",
                "partial_credit_rules": "Award full marks for thorough correctness; deduct proportionately for misconceptions.",
                "expected_concepts": ["Accurate core principle definition", "Logical cause-and-effect"],
                "critical_errors": ["Factually contradictory statements", "Confusing key definitions"],
            },
            {
                "criterion_name": "Completeness & Depth of Explanation",
                "maximum_marks": completeness,
                "description": "Coverage of necessary components, comprehensive steps, and illustrative context or examples.",
                "partial_credit_rules": "Award marks based on ratio of required sub-points adequately addressed.",
                "expected_concepts": ["All mandatory stages or components covered", "Relevant example or diagram explanation"],
                "critical_errors": ["Omitting essential half of the answer"],
            },
            {
                "criterion_name": "Terminology, Structure & Clarity",
                "maximum_marks": terminology,
                "description": "Appropriate use of domain terminology, coherent academic prose, and structured presentation.",
                "partial_credit_rules": "Award full marks if standard terms are used; accept equivalent standard synonyms.",
                "expected_concepts": ["Domain-specific nomenclature", "Clear structural flow"],
                "critical_errors": ["Excessively vague colloquialisms replacing standard academic terms"],
            },
        ]
