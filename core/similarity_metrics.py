"""
Lexical and Semantic similarity metrics module.
Computes BLEU and ROUGE-L metrics between student and reference model answers.
Includes standalone pure-python fallbacks to guarantee zero runtime crashes.
"""

from typing import Dict, Any, List
import re
import math
from collections import Counter


class SimilarityMetrics:
    """
    Computes BLEU and ROUGE-L scores for academic evaluation.
    Clearly notes that lexical overlap is supplementary and does not replace semantic scoring.
    """

    @classmethod
    def tokenize(cls, text: str) -> List[str]:
        """Simple whitespace/word tokenizer."""
        return re.findall(r"\w+", text.lower())

    @classmethod
    def compute_bleu(cls, reference: str, candidate: str) -> float:
        """
        Computes sentence-level BLEU score with smoothing.
        Attempts nltk sentence_bleu first, falls back to internal pure-python n-gram BLEU.
        """
        ref_tokens = cls.tokenize(reference)
        cand_tokens = cls.tokenize(candidate)

        if not cand_tokens or not ref_tokens:
            return 0.0

        try:
            from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
            smoother = SmoothingFunction().method1
            score = sentence_bleu([ref_tokens], cand_tokens, weights=(0.5, 0.5), smoothing_function=smoother)
            return round(float(score) * 100, 2)
        except Exception:
            # Standalone Pure-Python smoothed BLEU-2 calculation
            return cls._fallback_bleu(ref_tokens, cand_tokens)

    @classmethod
    def _fallback_bleu(cls, ref_tokens: List[str], cand_tokens: List[str]) -> float:
        """Calculates smoothed unigram and bigram precision with brevity penalty."""
        cand_len = len(cand_tokens)
        ref_len = len(ref_tokens)

        # Brevity penalty
        bp = 1.0 if cand_len >= ref_len else math.exp(1 - ref_len / max(1, cand_len))

        # Unigrams
        ref_unigrams = Counter(ref_tokens)
        cand_unigrams = Counter(cand_tokens)
        unigram_matches = sum(min(count, ref_unigrams[gram]) for gram, count in cand_unigrams.items())
        p1 = (unigram_matches + 1) / (cand_len + 1)

        # Bigrams
        if cand_len > 1 and ref_len > 1:
            ref_bigrams = Counter(zip(ref_tokens[:-1], ref_tokens[1:]))
            cand_bigrams = Counter(zip(cand_tokens[:-1], cand_tokens[1:]))
            bigram_matches = sum(min(count, ref_bigrams[gram]) for gram, count in cand_bigrams.items())
            p2 = (bigram_matches + 1) / (cand_len)
        else:
            p2 = p1

        geom_mean = math.exp(0.5 * math.log(p1) + 0.5 * math.log(p2))
        return round(float(bp * geom_mean * 100), 2)

    @classmethod
    def compute_rouge_l(cls, reference: str, candidate: str) -> float:
        """
        Computes ROUGE-L (Longest Common Subsequence) F1 score.
        Attempts rouge-score library first, falls back to exact LCS implementation.
        """
        if not reference.strip() or not candidate.strip():
            return 0.0

        try:
            from rouge_score import rouge_scorer
            scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=False)
            scores = scorer.score(reference, candidate)
            return round(scores["rougeL"].fmeasure * 100, 2)
        except Exception:
            return cls._fallback_rouge_l(reference, candidate)

    @classmethod
    def _fallback_rouge_l(cls, reference: str, candidate: str) -> float:
        """Dynamic programming LCS for ROUGE-L F1."""
        ref_tokens = cls.tokenize(reference)
        cand_tokens = cls.tokenize(candidate)

        m, n = len(ref_tokens), len(cand_tokens)
        if m == 0 or n == 0:
            return 0.0

        # Space-optimized DP LCS
        prev = [0] * (n + 1)
        for i in range(1, m + 1):
            curr = [0] * (n + 1)
            for j in range(1, n + 1):
                if ref_tokens[i - 1] == cand_tokens[j - 1]:
                    curr[j] = prev[j - 1] + 1
                else:
                    curr[j] = max(prev[j], curr[j - 1])
            prev = curr

        lcs_len = prev[n]
        prec = lcs_len / n
        rec = lcs_len / m
        if (prec + rec) == 0:
            return 0.0
        f1 = (2 * prec * rec) / (prec + rec)
        return round(f1 * 100, 2)

    @classmethod
    def compute_all_metrics(cls, reference: str, candidate: str) -> Dict[str, Any]:
        """Calculates both BLEU and ROUGE-L alongside academic interpretation disclaimer."""
        bleu = cls.compute_bleu(reference, candidate)
        rouge_l = cls.compute_rouge_l(reference, candidate)

        return {
            "bleu_score": bleu,
            "rouge_l_score": rouge_l,
            "semantic_similarity": round((bleu * 0.4 + rouge_l * 0.6), 2),  # Composite lexical proxy
            "disclaimer": (
                "Notice: BLEU and ROUGE-L measure lexical and sequence overlap. "
                "In descriptive academic assessment, high lexical overlap indicates verbatim similarity "
                "to the reference text, while low lexical overlap may still represent conceptually accurate "
                "rephrased student answers."
            )
        }
