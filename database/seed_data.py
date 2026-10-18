"""
Database Seeding Script.
Populates initial sample assessments, authentic rubric, and benchmark observations.
"""

import os
import sys
from pathlib import Path

# Ensure project root is in path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from database.db import init_db, get_db
from database.models import Assessment, BenchmarkObservation
from database.repository import AssessmentRepository
from core.benchmark import SAMPLE_BENCHMARK_DATA
from core.similarity_metrics import SimilarityMetrics


def seed_database_if_empty(force: bool = False):
    """Initializes schema and populates sample assessment if not present."""
    init_db()

    with get_db() as db:
        existing = db.query(Assessment).filter(Assessment.title == "Midterm Examination 2026 - Systems Architecture").first()
        if existing and not force:
            return  # Sample assessment already seeded

    print("Seeding initial assessment and benchmark cases...")

    # 1. Create Sample Assessment
    q_data = {
        "question_text": "Explain the concept of Virtual Memory and how Paging is used to implement it.",
        "maximum_marks": 10.0,
        "model_answer": (
            "Virtual memory is a memory management capability of an OS that creates the illusion to users of a very large main memory. "
            "It allows processes to execute even if they are not completely resident in physical RAM. "
            "Paging is the primary implementation mechanism, dividing virtual address space into fixed-size blocks called pages, and physical RAM into frames. "
            "The Memory Management Unit (MMU) uses a Page Table to translate virtual page numbers to physical frame numbers. "
            "When a requested page is not in RAM, a page fault exception is triggered, causing the OS to fetch the page from secondary storage (swap/paging file)."
        ),
        "evaluation_instructions": "Check for accurate definitions of virtual vs physical address spaces, page vs frame distinction, MMU role, and page fault handling. Accept equivalent standard terminology.",
        "expected_keywords": ["Virtual Memory", "Paging", "Frames", "MMU", "Page Table", "Page Fault"],
        "rubric": [
            {
                "criterion_name": "Technical Accuracy & Core Principles",
                "maximum_marks": 4.0,
                "description": "Factual correctness of virtual memory abstraction, address space separation, and RAM offloading.",
                "partial_credit_rules": "Award 4.0 for comprehensive correctness; 2.0-3.0 for minor omissions; deduct for conceptual confusion.",
                "expected_concepts": ["Illusion of large memory", "Separation of logical and physical addresses"],
                "critical_errors": ["Confusing virtual memory with cloud storage", "Stating RAM size increases physically"]
            },
            {
                "criterion_name": "Completeness & Mechanism Coverage",
                "maximum_marks": 3.5,
                "description": "Explanation of Paging mechanics: pages, frames, page tables, MMU, and page faults.",
                "partial_credit_rules": "Proportional credit based on coverage of the 4 key components (pages/frames, page table, MMU, page fault).",
                "expected_concepts": ["Fixed-size chunks (pages & frames)", "Page Table translation", "Page fault interrupt handling"],
                "critical_errors": ["Omitting Page Table or MMU completely"]
            },
            {
                "criterion_name": "Terminology & Structure",
                "maximum_marks": 2.5,
                "description": "Appropriate OS terminology, logical coherence, and structured exposition.",
                "partial_credit_rules": "Full credit for standard terminology; accept standard synonyms.",
                "expected_concepts": ["Accurate OS nomenclature", "Clear paragraph or step structure"],
                "critical_errors": ["Excessively vague colloquialisms replacing standard technical terms"]
            }
        ]
    }

    assessment = AssessmentRepository.create_assessment(
        title="Midterm Examination 2026 - Systems Architecture",
        subject="Computer Science & Engineering (CS401)",
        course_code="CS401-OS",
        institution="Faculty of Engineering & Technology",
        questions_data=[q_data]
    )

    # 2. Add an initial evaluated sample submission (Student 101)
    q = assessment.questions[0]
    sample_answer = (
        "Virtual memory is an OS memory abstraction technique that gives each running process the illusion of having a contiguous and vast address space, "
        "often significantly larger than physical RAM. "
        "In paging, memory is segmented into fixed-size chunks: virtual memory into 'pages' and physical memory into 'frames' of equal size. "
        "The hardware MMU translates virtual addresses to physical addresses using a per-process Page Table containing valid/invalid bits. "
        "If an accessed page is not currently in physical memory, a Page Fault interrupt occurs, bringing the missing page from disk swap space into an available frame."
    )

    sub = AssessmentRepository.add_submission(
        assessment_id=assessment.id,
        student_identifier="STU-2026-0814",
        original_filename="STU_0814_OS_Exam.pdf",
        file_path="uploads/STU_0814_OS_Exam.pdf",
        extracted_text=sample_answer,
        page_count=1,
        word_count=len(sample_answer.split()),
        extraction_status="SUCCESS"
    )

    # Calculate metrics
    metrics = SimilarityMetrics.compute_all_metrics(q.model_answer, sample_answer)

    AssessmentRepository.save_evaluation(
        submission_id=sub.id,
        question_id=q.id,
        maximum_marks=10.0,
        ai_awarded_marks=9.0,
        criteria_scores=[
            {
                "criterion": "Technical Accuracy & Core Principles",
                "maximum_marks": 4.0,
                "awarded_marks": 4.0,
                "evidence": "gives each running process the illusion of having a contiguous and vast address space",
                "justification": "Flawless articulation of the virtual memory abstraction principle."
            },
            {
                "criterion": "Completeness & Mechanism Coverage",
                "maximum_marks": 3.5,
                "awarded_marks": 3.25,
                "evidence": "hardware MMU translates virtual addresses to physical addresses using a per-process Page Table... Page Fault interrupt occurs",
                "justification": "Covers pages, frames, MMU translation, and page fault handling. Minor omission of frame replacement algorithms."
            },
            {
                "criterion": "Terminology & Structure",
                "maximum_marks": 2.5,
                "awarded_marks": 2.5,
                "evidence": "Accurate technical phrasing throughout.",
                "justification": "Professional academic prose with correct terminology."
            }
        ],
        strengths=["Clear explanation of MMU role", "Accurate definition of page fault handling"],
        conceptual_gaps=["Could mention page replacement policies (e.g. LRU) for completeness"],
        improvement_suggestions=["Illustrate with an address translation diagram for full marks"],
        bleu_score=metrics["bleu_score"],
        rouge_l_score=metrics["rouge_l_score"],
        semantic_similarity=metrics["semantic_similarity"],
        review_status="Approved"
    )

    # 3. Seed Benchmark observations
    for case in SAMPLE_BENCHMARK_DATA:
        b_metrics = SimilarityMetrics.compute_all_metrics(case["model_answer"], case["student_answer"])
        # Illustrative calibrated AI score
        ai_sim_score = round(case["human_score"] + (0.5 if "02" in case["case_id"] else (-0.25 if "01" in case["case_id"] else 0.0)), 2)
        AssessmentRepository.save_benchmark_observation(
            benchmark_suite="Operating Systems Core (CS401)",
            case_identifier=case["case_id"],
            question_text=case["question_text"],
            model_answer=case["model_answer"],
            student_answer=case["student_answer"],
            human_score=case["human_score"],
            ai_score=ai_sim_score,
            maximum_marks=case["maximum_marks"],
            bleu_score=b_metrics["bleu_score"],
            rouge_l_score=b_metrics["rouge_l_score"],
            notes=case["notes"]
        )

    print("Seeding completed successfully.")


if __name__ == "__main__":
    seed_database_if_empty()
