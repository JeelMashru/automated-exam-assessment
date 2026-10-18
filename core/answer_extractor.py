"""
Answer Extractor module: cleans, segments, and prepares extracted student text for evaluation.
Includes prompt-injection sanitation and question-answer mapping.
"""

import re
from typing import Dict, List, Any


class AnswerExtractor:
    """Prepares and maps extracted student text for downstream LLM evaluation."""

    # Patterns commonly used in prompt injection attempts within submitted answers
    INJECTION_PATTERNS = [
        r"(?i)ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"(?i)you\s+must\s+give\s+(me\s+)?(10|full|maximum)\s+marks",
        r"(?i)system\s*:\s*award\s+full\s+marks",
        r"(?i)override\s+scoring\s+to\s+\d+",
        r"(?i)<script\b[^>]*>",
        r"(?i)<!--\s*#include",
    ]

    @classmethod
    def sanitize_untrusted_text(cls, text: str) -> str:
        """
        Sanitizes student answer text to mitigate prompt injection.
        Disarms prompt injection attempts by neutralizing delimiter attacks and wrapping
        untrusted content safely.
        """
        if not text:
            return ""

        sanitized = text
        # Neutralize potential markdown code-block breakages
        sanitized = sanitized.replace("```", "'''")

        # Flag and annotate suspicious injection tokens
        for pattern in cls.INJECTION_PATTERNS:
            sanitized = re.sub(
                pattern,
                r"[DISARMED SUBMISSION TEXT: '\g<0>']",
                sanitized
            )

        return sanitized.strip()

    @classmethod
    def segment_by_questions(
        cls,
        full_text: str,
        question_count: int = 1
    ) -> Dict[int, str]:
        """
        Attempts to heuristically split student text into sections by question numbers
        e.g., 'Q1:', 'Question 1:', 'Ans 1.', etc.
        Falls back to assigning all text to Q1 if single question or headers not found.
        """
        if question_count <= 1:
            return {1: full_text}

        sections = {}
        # Regex to match question markers like "Q1", "Question 1", "Ans 1", "Answer 1"
        q_pattern = r"(?i)(?:question|q|ans|answer)\s*(\d+)[\s.:\)]"
        matches = list(re.finditer(q_pattern, full_text))

        if not matches:
            # Cannot automatically split; assign full text to Q1 as fallback
            return {1: full_text}

        for i, match in enumerate(matches):
            q_num = int(match.group(1))
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
            content = full_text[start_pos:end_pos].strip()
            sections[q_num] = content

        # Ensure all expected questions exist in dictionary
        for q in range(1, question_count + 1):
            if q not in sections:
                sections[q] = ""

        return sections
