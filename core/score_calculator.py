"""
Programmatic score calculation and verification engine.
Guarantees mathematical integrity, bounds checking, and prevents LLM arithmetic hallucinations.
"""

from typing import List, Dict, Any, Tuple


class ScoreCalculator:
    """Performs rigorous programmatic calculation of marks and grade boundaries."""

    @classmethod
    def calculate_total_and_clamp(
        cls,
        criteria_evaluations: List[Dict[str, Any]],
        question_max_marks: float,
        allow_negative: bool = False
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """
        Validates and clamps individual criterion marks, then programmatically sums them.
        Ensures:
          0 <= criterion_awarded <= criterion_max
          0 <= total_awarded <= question_max_marks
        """
        clamped_criteria = []
        running_total = 0.0

        for crit in criteria_evaluations:
            c_name = crit.get("criterion", "Unnamed Criterion")
            max_m = float(crit.get("maximum_marks", 0.0))
            raw_awarded = float(crit.get("awarded_marks", 0.0))

            # Clamp awarded marks between 0 (or negative if allowed) and max_m
            lower_bound = -max_m if allow_negative else 0.0
            clamped_awarded = max(lower_bound, min(raw_awarded, max_m))

            running_total += clamped_awarded

            clamped_crit = dict(crit)
            clamped_crit["awarded_marks"] = round(clamped_awarded, 2)
            clamped_crit["maximum_marks"] = round(max_m, 2)
            clamped_criteria.append(clamped_crit)

        # Enforce question ceiling
        final_total = max(0.0, min(running_total, question_max_marks))
        return round(final_total, 2), clamped_criteria

    @classmethod
    def get_academic_grade_band(cls, percentage: float) -> Tuple[str, str]:
        """Maps percentage to standard academic classification."""
        if percentage >= 85.0:
            return "First Class with Distinction (A+)", "Exceptional mastery: Clear, precise, and thoroughly articulated."
        elif percentage >= 75.0:
            return "First Class (A)", "Strong understanding: Solid grasp of core concepts with minor omissions."
        elif percentage >= 60.0:
            return "Higher Second Class (B+)", "Good understanding: Covers key principles well with room for more detail."
        elif percentage >= 50.0:
            return "Second Class (B)", "Basic understanding: Demonstrates fundamental knowledge, but lacks technical depth."
        elif percentage >= 40.0:
            return "Pass Class (C)", "Marginal: Shows partial comprehension, but omitted several required points."
        else:
            return "Unsatisfactory / Needs Improvement (F)", "Needs improvement: Key concepts were not sufficiently addressed."
