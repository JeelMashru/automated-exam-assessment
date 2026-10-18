"""
Repository layer for database operations with safe error handling and transaction integrity.
"""

from datetime import datetime, timezone
import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from database.models import (
    Assessment,
    Question,
    RubricCriterion,
    Submission,
    Evaluation,
    AuditLog,
    BenchmarkObservation,
)
from database.db import get_db


class AssessmentRepository:

    @staticmethod
    def create_assessment(
        title: str,
        subject: str,
        course_code: Optional[str] = None,
        institution: Optional[str] = None,
        questions_data: Optional[List[Dict[str, Any]]] = None,
    ) -> Assessment:
        """Create a complete assessment with questions and rubrics atomically."""
        with get_db() as db:
            assessment = Assessment(
                title=title,
                subject=subject,
                course_code=course_code,
                institution=institution,
            )
            db.add(assessment)
            db.flush()

            if questions_data:
                for idx, q_data in enumerate(questions_data, start=1):
                    question = Question(
                        assessment_id=assessment.id,
                        question_number=idx,
                        question_text=q_data["question_text"],
                        maximum_marks=float(q_data["maximum_marks"]),
                        model_answer=q_data["model_answer"],
                        evaluation_instructions=q_data.get("evaluation_instructions", ""),
                        expected_keywords=json.dumps(q_data.get("expected_keywords", [])),
                    )
                    db.add(question)
                    db.flush()

                    for crit in q_data.get("rubric", []):
                        criterion = RubricCriterion(
                            question_id=question.id,
                            criterion_name=crit["criterion_name"],
                            maximum_marks=float(crit["maximum_marks"]),
                            description=crit.get("description", ""),
                            partial_credit_rules=crit.get("partial_credit_rules", ""),
                            expected_concepts=json.dumps(crit.get("expected_concepts", [])),
                            critical_errors=json.dumps(crit.get("critical_errors", [])),
                        )
                        db.add(criterion)

            db.commit()
            db.refresh(assessment)
            return assessment

    @staticmethod
    def get_all_assessments() -> List[Dict[str, Any]]:
        with get_db() as db:
            assessments = db.query(Assessment).order_by(Assessment.created_at.desc()).all()
            results = []
            for a in assessments:
                results.append({
                    "id": a.id,
                    "title": a.title,
                    "subject": a.subject,
                    "course_code": a.course_code,
                    "institution": a.institution,
                    "created_at": a.created_at,
                    "question_count": len(a.questions),
                    "submission_count": len(a.submissions),
                })
            return results

    @staticmethod
    def get_assessment(assessment_id: str) -> Optional[Assessment]:
        with get_db() as db:
            return db.query(Assessment).filter(Assessment.id == assessment_id).first()

    @staticmethod
    def delete_assessment(assessment_id: str) -> bool:
        with get_db() as db:
            assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
            if assessment:
                db.delete(assessment)
                db.commit()
                return True
            return False

    @staticmethod
    def add_submission(
        assessment_id: str,
        student_identifier: str,
        original_filename: str,
        file_path: str,
        extracted_text: str,
        page_count: int = 1,
        word_count: int = 0,
        extraction_status: str = "SUCCESS",
    ) -> Submission:
        with get_db() as db:
            sub = Submission(
                assessment_id=assessment_id,
                student_identifier=student_identifier,
                original_filename=original_filename,
                file_path=file_path,
                extracted_text=extracted_text,
                page_count=page_count,
                word_count=word_count,
                extraction_status=extraction_status,
            )
            db.add(sub)
            db.commit()
            db.refresh(sub)
            return sub

    @staticmethod
    def save_evaluation(
        submission_id: str,
        question_id: str,
        maximum_marks: float,
        ai_awarded_marks: float,
        criteria_scores: list,
        strengths: list,
        conceptual_gaps: list,
        improvement_suggestions: list,
        bleu_score: Optional[float] = None,
        rouge_l_score: Optional[float] = None,
        semantic_similarity: Optional[float] = None,
        review_status: str = "Pending Human Review",
    ) -> Evaluation:
        with get_db() as db:
            # Check if evaluation already exists
            eval_record = db.query(Evaluation).filter(
                Evaluation.submission_id == submission_id,
                Evaluation.question_id == question_id
            ).first()

            if not eval_record:
                eval_record = Evaluation(
                    submission_id=submission_id,
                    question_id=question_id,
                )
                db.add(eval_record)

            eval_record.maximum_marks = maximum_marks
            eval_record.ai_awarded_marks = ai_awarded_marks
            eval_record.final_awarded_marks = ai_awarded_marks
            eval_record.criteria_scores_json = json.dumps(criteria_scores)
            eval_record.strengths_json = json.dumps(strengths)
            eval_record.conceptual_gaps_json = json.dumps(conceptual_gaps)
            eval_record.improvement_suggestions_json = json.dumps(improvement_suggestions)
            eval_record.bleu_score = bleu_score
            eval_record.rouge_l_score = rouge_l_score
            eval_record.semantic_similarity = semantic_similarity
            eval_record.review_status = review_status
            eval_record.evaluated_at = datetime.now(timezone.utc)

            db.commit()
            db.refresh(eval_record)
            return eval_record

    @staticmethod
    def override_evaluation(
        evaluation_id: str,
        new_score: float,
        comments: str,
        reviewer_name: str = "Faculty Evaluator",
        status: str = "Approved",
    ) -> Optional[Evaluation]:
        with get_db() as db:
            evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
            if not evaluation:
                return None

            prev_score = evaluation.final_awarded_marks
            evaluation.final_awarded_marks = new_score
            evaluation.review_status = status
            evaluation.human_feedback = comments
            evaluation.reviewed_at = datetime.now(timezone.utc)
            evaluation.reviewed_by = reviewer_name

            # Add Audit Log entry
            audit = AuditLog(
                evaluation_id=evaluation.id,
                action="SCORE_OVERRIDE" if prev_score != new_score else "STATUS_CHANGE",
                previous_score=prev_score,
                new_score=new_score,
                changed_by=reviewer_name,
                comments=comments,
            )
            db.add(audit)
            db.commit()
            db.refresh(evaluation)
            return evaluation

    @staticmethod
    def get_evaluations_for_assessment(assessment_id: str) -> List[Dict[str, Any]]:
        with get_db() as db:
            submissions = db.query(Submission).filter(Submission.assessment_id == assessment_id).all()
            results = []
            for sub in submissions:
                for ev in sub.evaluations:
                    results.append({
                        "evaluation_id": ev.id,
                        "submission_id": sub.id,
                        "student_identifier": sub.student_identifier,
                        "filename": sub.original_filename,
                        "question_id": ev.question_id,
                        "question_number": ev.question.question_number if ev.question else 1,
                        "maximum_marks": ev.maximum_marks,
                        "ai_awarded_marks": ev.ai_awarded_marks,
                        "final_awarded_marks": ev.final_awarded_marks,
                        "bleu_score": ev.bleu_score,
                        "rouge_l_score": ev.rouge_l_score,
                        "semantic_similarity": ev.semantic_similarity,
                        "review_status": ev.review_status,
                        "evaluated_at": ev.evaluated_at,
                        "criteria": json.loads(ev.criteria_scores_json or "[]"),
                        "strengths": json.loads(ev.strengths_json or "[]"),
                        "gaps": json.loads(ev.conceptual_gaps_json or "[]"),
                        "suggestions": json.loads(ev.improvement_suggestions_json or "[]"),
                        "human_feedback": ev.human_feedback,
                        "reviewed_by": ev.reviewed_by,
                        "extracted_text": sub.extracted_text,
                    })
            return results

    @staticmethod
    def get_audit_trail(evaluation_id: str) -> List[Dict[str, Any]]:
        with get_db() as db:
            logs = db.query(AuditLog).filter(AuditLog.evaluation_id == evaluation_id).order_by(AuditLog.timestamp.desc()).all()
            return [
                {
                    "action": log.action,
                    "previous_score": log.previous_score,
                    "new_score": log.new_score,
                    "changed_by": log.changed_by,
                    "comments": log.comments,
                    "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "",
                }
                for log in logs
            ]

    @staticmethod
    def save_benchmark_observation(
        benchmark_suite: str,
        case_identifier: str,
        question_text: str,
        model_answer: str,
        student_answer: str,
        human_score: float,
        ai_score: float,
        maximum_marks: float,
        bleu_score: Optional[float] = None,
        rouge_l_score: Optional[float] = None,
        notes: str = "",
    ) -> BenchmarkObservation:
        with get_db() as db:
            abs_err = abs(human_score - ai_score)
            obs = BenchmarkObservation(
                benchmark_suite=benchmark_suite,
                case_identifier=case_identifier,
                question_text=question_text,
                model_answer=model_answer,
                student_answer=student_answer,
                human_score=human_score,
                ai_score=ai_score,
                maximum_marks=maximum_marks,
                absolute_error=abs_err,
                bleu_score=bleu_score,
                rouge_l_score=rouge_l_score,
                notes=notes,
            )
            db.add(obs)
            db.commit()
            db.refresh(obs)
            return obs

    @staticmethod
    def get_benchmark_observations(suite_name: Optional[str] = None) -> List[Dict[str, Any]]:
        with get_db() as db:
            query = db.query(BenchmarkObservation)
            if suite_name:
                query = query.filter(BenchmarkObservation.benchmark_suite == suite_name)
            observations = query.order_by(BenchmarkObservation.created_at.desc()).all()
            return [
                {
                    "id": o.id,
                    "suite": o.benchmark_suite,
                    "case_id": o.case_identifier,
                    "question": o.question_text,
                    "human_score": o.human_score,
                    "ai_score": o.ai_score,
                    "max_marks": o.maximum_marks,
                    "absolute_error": o.absolute_error,
                    "bleu_score": o.bleu_score,
                    "rouge_l_score": o.rouge_l_score,
                    "notes": o.notes,
                    "created_at": o.created_at,
                }
                for o in observations
            ]
