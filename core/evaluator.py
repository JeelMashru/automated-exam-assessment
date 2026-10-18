"""
Automated Evaluation Orchestrator (LLM-as-a-Judge Engine).
Orchestrates prompt assembly, LLM execution, schema validation, score calculation,
and lexical/semantic similarity metric computation.
"""

from typing import Dict, Any, List, Optional
from core.answer_extractor import AnswerExtractor
from core.prompt_templates import SYSTEM_PROMPT, build_evaluator_prompt
from core.response_validator import ResponseValidator
from core.similarity_metrics import SimilarityMetrics
from core.llm_client import BaseLLMProvider, get_llm_provider


class ExamEvaluator:
    """End-to-end evaluation pipeline coordinating LLM, validator, and metrics."""

    def __init__(self, provider: Optional[BaseLLMProvider] = None):
        self.provider = provider or get_llm_provider()

    def evaluate_submission(
        self,
        assessment_id: str,
        student_id: str,
        question_id: str,
        question_text: str,
        maximum_marks: float,
        model_answer: str,
        rubric_criteria: List[Dict[str, Any]],
        student_answer: str,
        instructions: str = "",
        calibration_mode: str = "balanced",
    ) -> Dict[str, Any]:
        """
        Executes complete assessment workflow for a single question response.

        Returns:
            {
                "success": bool,
                "data": dict | None,
                "error": str | None,
                "metrics": dict
            }
        """
        # 1. Sanitize untrusted student text (adversarial prompt injection defense)
        sanitized_answer = AnswerExtractor.sanitize_untrusted_text(student_answer)

        # 2. Compute Lexical & Semantic Similarity Metrics
        metrics = SimilarityMetrics.compute_all_metrics(
            reference=model_answer,
            candidate=sanitized_answer
        )

        # 3. Build structured evaluator prompt
        prompt = build_evaluator_prompt(
            assessment_id=assessment_id,
            student_id=student_id,
            question_id=question_id,
            question_text=question_text,
            maximum_marks=maximum_marks,
            model_answer=model_answer,
            rubric_criteria=rubric_criteria,
            student_answer=sanitized_answer,
            instructions=instructions,
            calibration_mode=calibration_mode
        )

        # 4. Invoke LLM provider
        try:
            raw_response = self.provider.generate_assessment(
                system_instruction=SYSTEM_PROMPT,
                prompt=prompt,
                temperature=0.0
            )
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": f"LLM generation failed: {str(e)}",
                "metrics": metrics
            }

        # 5. Validate JSON response schema and recalculate marks programmatically
        valid, validated_result, val_err = ResponseValidator.validate_and_compute(
            raw_llm_output=raw_response,
            expected_question_max_marks=maximum_marks,
            rubric_reference=rubric_criteria
        )

        if not valid:
            return {
                "success": False,
                "data": None,
                "error": f"Response validation failed: {val_err}",
                "metrics": metrics
            }

        # 6. Attach similarity metrics to validated result
        validated_result["bleu_score"] = metrics["bleu_score"]
        validated_result["rouge_l_score"] = metrics["rouge_l_score"]
        validated_result["semantic_similarity"] = metrics["semantic_similarity"]
        validated_result["metrics_disclaimer"] = metrics["disclaimer"]
        validated_result["provider_info"] = self.provider.get_provider_info()

        return {
            "success": True,
            "data": validated_result,
            "error": None,
            "metrics": metrics
        }
