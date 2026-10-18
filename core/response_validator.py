"""
Pydantic schema validation for LLM evaluation responses.
Parses, sanitizes, and verifies structural and numerical bounds.
"""

import json
import re
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field, ValidationError
from core.score_calculator import ScoreCalculator


class CriterionEvaluationModel(BaseModel):
    criterion: str = Field(..., description="Name of the criterion")
    maximum_marks: float = Field(..., ge=0.0)
    awarded_marks: float = Field(..., ge=0.0)
    evidence: str = Field(default="")
    justification: str = Field(default="")
    missing_concepts: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class LLMEvaluationResponseModel(BaseModel):
    assessment_id: str
    student_id: str
    question_id: str
    maximum_marks: float
    awarded_marks: float
    criteria: List[CriterionEvaluationModel]
    strengths: List[str] = Field(default_factory=list)
    conceptual_gaps: List[str] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)
    review_required: bool = True
    review_status: str = "Pending Human Review"


class ResponseValidator:
    """Validates raw LLM strings into validated, programmatically checked evaluation models."""

    @classmethod
    def clean_json_string(cls, raw_text: str) -> str:
        """Strips markdown backticks, preambles, and conversational artifacts."""
        text = raw_text.strip()
        # Remove ```json ... ``` or ``` ... ```
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        # Extract first JSON object if surrounded by extra text
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            text = text[first_brace : last_brace + 1]

        return text

    @classmethod
    def validate_and_compute(
        cls,
        raw_llm_output: str,
        expected_question_max_marks: float,
        rubric_reference: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Parses raw LLM string, verifies against Pydantic schema, clamps scores,
        and recomputes total marks programmatically.

        Returns:
            (success: bool, validated_dict: dict | None, error_message: str | None)
        """
        cleaned = cls.clean_json_string(raw_llm_output)
        try:
            parsed_json = json.loads(cleaned)
        except Exception as e:
            return False, None, f"JSON parse error: {str(e)}. Cleaned text preview: {cleaned[:200]}"

        try:
            model = LLMEvaluationResponseModel(**parsed_json)
        except ValidationError as ve:
            return False, None, f"Schema validation error: {str(ve)}"

        # Convert criteria to dicts for score calculator
        criteria_list = [c.model_dump() for c in model.criteria]

        # Programmatically clamp and sum marks
        recomputed_total, clamped_criteria = ScoreCalculator.calculate_total_and_clamp(
            criteria_evaluations=criteria_list,
            question_max_marks=expected_question_max_marks,
            allow_negative=False
        )

        result_dict = {
            "assessment_id": model.assessment_id,
            "student_id": model.student_id,
            "question_id": model.question_id,
            "maximum_marks": expected_question_max_marks,
            "awarded_marks": recomputed_total,
            "criteria": clamped_criteria,
            "strengths": model.strengths,
            "conceptual_gaps": model.conceptual_gaps,
            "improvement_suggestions": model.improvement_suggestions,
            "review_required": True,
            "review_status": "Pending Human Review"
        }

        return True, result_dict, None
