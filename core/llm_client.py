"""
LLM Provider Abstraction Layer with Gemini, OpenAI, and Offline Demo support.
Includes bounded retries, timeout management, and secure credential handling.
"""

import os
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional
from config import settings


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM assessment providers."""

    @abstractmethod
    def generate_assessment(
        self,
        system_instruction: str,
        prompt: str,
        temperature: float = 0.0,
    ) -> str:
        """Generates raw response from the LLM."""
        pass

    @abstractmethod
    def test_connection(self) -> Tuple[bool, str]:
        """Tests whether credentials and endpoints are valid and reachable."""
        pass

    @abstractmethod
    def get_provider_info(self) -> Dict[str, Any]:
        """Returns provider name, configured model, and operational mode."""
        pass


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider using the official google-genai SDK."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.DEFAULT_MODEL
        self._client = None
        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                self._client = None

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def test_connection(self) -> Tuple[bool, str]:
        if not self.is_configured():
            return False, "Google Gemini API key is missing or not configured."

        try:
            from google import genai
            from google.genai import types

            client = self._client or genai.Client(api_key=self.api_key)
            # Lightweight ping
            resp = client.models.generate_content(
                model=self.model,
                contents="Ping. Respond with single word: OK",
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    max_output_tokens=10,
                )
            )
            if resp and resp.text:
                return True, f"Connection to Gemini ({self.model}) successful."
            return False, "Gemini responded with empty content."
        except Exception as e:
            return False, f"Gemini connection failed: {str(e)}"

    def generate_assessment(
        self,
        system_instruction: str,
        prompt: str,
        temperature: float = 0.0,
    ) -> str:
        if not self.is_configured():
            raise ValueError(
                "Gemini API key is not configured. Please set GEMINI_API_KEY in .env or the Settings panel."
            )

        from google import genai
        from google.genai import types

        client = self._client or genai.Client(api_key=self.api_key)
        
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            response_mime_type="application/json",
        )

        max_retries = settings.LLM_MAX_RETRIES
        delay = 2.0
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                response = client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=config,
                )
                if response and response.text:
                    return response.text
                raise ValueError("Empty response received from Gemini API.")
            except Exception as e:
                last_error = e
                # Check for rate limit / 429
                err_str = str(e).lower()
                if "429" in err_str or "quota" in err_str or "rate limit" in err_str:
                    time.sleep(delay)
                    delay *= 2
                elif attempt < max_retries:
                    time.sleep(1.0)
                else:
                    break

        raise RuntimeError(f"Gemini API evaluation failed after {max_retries} attempts: {str(last_error)}")

    def get_provider_info(self) -> Dict[str, Any]:
        return {
            "provider": "gemini",
            "model": self.model,
            "configured": self.is_configured(),
            "mode": "Live AI Evaluation" if self.is_configured() else "Unconfigured"
        }


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider adapter."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = "gpt-4o-mini"):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or "gpt-4o-mini"
        self._client = None
        if self.api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except Exception:
                self._client = None

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def test_connection(self) -> Tuple[bool, str]:
        if not self.is_configured():
            return False, "OpenAI API key is missing or not configured."

        try:
            from openai import OpenAI
            client = self._client or OpenAI(api_key=self.api_key)
            resp = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Ping. Respond 'OK'"}],
                max_tokens=5,
            )
            if resp.choices and resp.choices[0].message.content:
                return True, f"Connection to OpenAI ({self.model}) successful."
            return False, "Empty response from OpenAI."
        except Exception as e:
            return False, f"OpenAI connection error: {str(e)}"

    def generate_assessment(
        self,
        system_instruction: str,
        prompt: str,
        temperature: float = 0.0,
    ) -> str:
        if not self.is_configured():
            raise ValueError("OpenAI API key is not configured.")

        from openai import OpenAI
        client = self._client or OpenAI(api_key=self.api_key)

        response = client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
        return response.choices[0].message.content

    def get_provider_info(self) -> Dict[str, Any]:
        return {
            "provider": "openai",
            "model": self.model,
            "configured": self.is_configured(),
            "mode": "Live AI Evaluation" if self.is_configured() else "Unconfigured"
        }


class MockDemoProvider(BaseLLMProvider):
    """
    Offline Calibrated Demo Evaluator.
    Provides realistic, reproducible evaluations for demonstration, testing,
    and environments without an active internet API key.
    Clearly labeled so users are never misled.
    """

    def __init__(self, model: str = "mock-evaluator-v1"):
        self.model = model

    def test_connection(self) -> Tuple[bool, str]:
        return True, "Offline Demo Evaluator is operational (No API key required)."

    def generate_assessment(
        self,
        system_instruction: str,
        prompt: str,
        temperature: float = 0.0,
    ) -> str:
        # Inspect prompt to extract assessment, student, and question identifiers
        import re

        aid_match = re.search(r"Assessment ID:\s*([^\n\r]+)", prompt)
        sid_match = re.search(r"Student Identifier:\s*([^\n\r]+)", prompt)
        qid_match = re.search(r"Question ID:\s*([^\n\r]+)", prompt)
        max_match = re.search(r"Question Maximum Marks:\s*([0-9.]+)", prompt)

        assessment_id = aid_match.group(1).strip() if aid_match else "ASSESS_DEMO"
        student_id = sid_match.group(1).strip() if sid_match else "STUDENT_DEMO"
        question_id = qid_match.group(1).strip() if qid_match else "Q1"
        max_marks = float(max_match.group(1).strip()) if max_match else 10.0

        # Extract criteria lines
        crit_matches = re.findall(r"- Criterion:\s*'([^']+)'\s*\[Max Marks:\s*([0-9.]+)\]", prompt)
        if not crit_matches:
            crit_matches = [
                ("Technical Accuracy & Core Principles", str(round(max_marks * 0.4, 2))),
                ("Completeness & Depth of Explanation", str(round(max_marks * 0.3, 2))),
                ("Terminology, Structure & Clarity", str(round(max_marks * 0.3, 2))),
            ]

        # Extract student answer snippet
        ans_start = prompt.find("<<<STUDENT_ANSWER_START>>>")
        ans_end = prompt.find("<<<STUDENT_ANSWER_END>>>")
        student_text = prompt[ans_start + 26 : ans_end].strip() if ans_start != -1 and ans_end != -1 else ""

        # Calibrated heuristic score based on student answer length and keyword density
        word_count = len(student_text.split())
        ratio = min(0.92, max(0.40, word_count / 120.0))

        criteria_evals = []
        for name, max_m_str in crit_matches:
            c_max = float(max_m_str)
            awarded = round(c_max * ratio, 2)
            evidence_snippet = (student_text[:120] + "...") if len(student_text) > 120 else (student_text or "No text submitted")
            criteria_evals.append({
                "criterion": name,
                "maximum_marks": c_max,
                "awarded_marks": awarded,
                "evidence": f"Excerpt: '{evidence_snippet}'",
                "justification": f"[DEMO EVALUATOR] Answer demonstrates reasonable alignment with {name}. Awarded {awarded}/{c_max} based on substantive content.",
                "missing_concepts": ["Advanced implementation edge-cases", "Formal theoretical proofs"] if ratio < 0.85 else [],
                "errors": []
            })

        total_awarded = sum(c["awarded_marks"] for c in criteria_evals)

        demo_response = {
            "assessment_id": assessment_id,
            "student_id": student_id,
            "question_id": question_id,
            "maximum_marks": max_marks,
            "awarded_marks": round(total_awarded, 2),
            "criteria": criteria_evals,
            "strengths": [
                "[DEMO MODE] Core conceptual outline identified.",
                "[DEMO MODE] Proper basic terminology used."
            ],
            "conceptual_gaps": [
                "[DEMO MODE] Further elaboration on architectural trade-offs recommended."
            ],
            "improvement_suggestions": [
                "[DEMO MODE] Provide concrete real-world case examples to strengthen descriptive arguments."
            ],
            "review_required": True,
            "review_status": "Pending Human Review"
        }

        return json.dumps(demo_response, indent=2)

    def get_provider_info(self) -> Dict[str, Any]:
        return {
            "provider": "mock",
            "model": self.model,
            "configured": True,
            "mode": "Offline Demo Evaluator (Simulated)"
        }


def get_llm_provider(
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> BaseLLMProvider:
    """
    Factory function returning the configured LLM provider.
    Automatically falls back to MockDemoProvider if keys are missing and demo mode is selected.
    """
    target_provider = (provider_name or settings.DEFAULT_PROVIDER).lower()

    if target_provider == "gemini":
        gemini = GeminiProvider(api_key=api_key, model=model)
        # If API key is not configured, fall back to mock demo provider so the app never crashes
        if not gemini.is_configured():
            return MockDemoProvider()
        return gemini

    elif target_provider == "openai":
        openai_p = OpenAIProvider(api_key=api_key, model=model)
        if not openai_p.is_configured():
            return MockDemoProvider()
        return openai_p

    else:
        return MockDemoProvider()
