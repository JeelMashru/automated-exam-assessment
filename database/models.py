"""
SQLAlchemy models for the Automated Descriptive Exam Assessment Engine.
Configured with selectin eager loading to avoid detached lazy load issues.
"""

from datetime import datetime, timezone
import json
import uuid
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    Boolean,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


def utc_now():
    return datetime.now(timezone.utc)


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    course_code = Column(String(100), nullable=True)
    institution = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships with eager selectin loading
    questions = relationship("Question", back_populates="assessment", cascade="all, delete-orphan", lazy="selectin")
    submissions = relationship("Submission", back_populates="assessment", cascade="all, delete-orphan", lazy="selectin")


class Question(Base):
    __tablename__ = "questions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    question_number = Column(Integer, default=1)
    question_text = Column(Text, nullable=False)
    maximum_marks = Column(Float, nullable=False)
    model_answer = Column(Text, nullable=False)
    evaluation_instructions = Column(Text, nullable=True)
    expected_keywords = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    assessment = relationship("Assessment", back_populates="questions", lazy="selectin")
    rubric_criteria = relationship("RubricCriterion", back_populates="question", cascade="all, delete-orphan", lazy="selectin")
    evaluations = relationship("Evaluation", back_populates="question", cascade="all, delete-orphan", lazy="selectin")


class RubricCriterion(Base):
    __tablename__ = "rubric_criteria"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    question_id = Column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    criterion_name = Column(String(255), nullable=False)
    maximum_marks = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    partial_credit_rules = Column(Text, nullable=True)
    expected_concepts = Column(Text, nullable=True)
    critical_errors = Column(Text, nullable=True)

    # Relationships
    question = relationship("Question", back_populates="rubric_criteria", lazy="selectin")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    student_identifier = Column(String(100), nullable=False)
    original_filename = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=True)
    extracted_text = Column(Text, nullable=True)
    page_count = Column(Integer, default=1)
    word_count = Column(Integer, default=0)
    extraction_status = Column(String(50), default="SUCCESS")
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    assessment = relationship("Assessment", back_populates="submissions", lazy="selectin")
    evaluations = relationship("Evaluation", back_populates="submission", cascade="all, delete-orphan", lazy="selectin")


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    
    # Marks
    maximum_marks = Column(Float, nullable=False)
    ai_awarded_marks = Column(Float, nullable=False)
    final_awarded_marks = Column(Float, nullable=False)
    
    # Detailed AI JSON Output
    criteria_scores_json = Column(Text, nullable=False)
    strengths_json = Column(Text, nullable=True)
    conceptual_gaps_json = Column(Text, nullable=True)
    improvement_suggestions_json = Column(Text, nullable=True)
    
    # Similarity Metrics
    bleu_score = Column(Float, nullable=True)
    rouge_l_score = Column(Float, nullable=True)
    semantic_similarity = Column(Float, nullable=True)
    
    # Review & Audit
    review_status = Column(String(50), default="Pending Human Review")
    human_feedback = Column(Text, nullable=True)
    evaluated_at = Column(DateTime, default=utc_now)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String(100), nullable=True)

    # Relationships
    submission = relationship("Submission", back_populates="evaluations", lazy="selectin")
    question = relationship("Question", back_populates="evaluations", lazy="selectin")
    audit_logs = relationship("AuditLog", back_populates="evaluation", cascade="all, delete-orphan", lazy="selectin")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    evaluation_id = Column(String(36), ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(100), nullable=False)
    previous_score = Column(Float, nullable=True)
    new_score = Column(Float, nullable=True)
    changed_by = Column(String(100), default="Instructor")
    comments = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=utc_now)

    # Relationships
    evaluation = relationship("Evaluation", back_populates="audit_logs", lazy="selectin")


class BenchmarkObservation(Base):
    __tablename__ = "benchmark_observations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    benchmark_suite = Column(String(100), nullable=False)
    case_identifier = Column(String(100), nullable=False)
    question_text = Column(Text, nullable=False)
    model_answer = Column(Text, nullable=False)
    student_answer = Column(Text, nullable=False)
    human_score = Column(Float, nullable=False)
    ai_score = Column(Float, nullable=False)
    maximum_marks = Column(Float, nullable=False)
    absolute_error = Column(Float, nullable=False)
    bleu_score = Column(Float, nullable=True)
    rouge_l_score = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
