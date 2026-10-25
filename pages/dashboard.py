"""
Dashboard Page: Executive overview, key metrics, charts, and recent evaluations.
"""

import streamlit as st
import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from database.repository import AssessmentRepository
from database.db import get_db
from database.models import Assessment, Submission, Evaluation


def render():
    st.markdown('<div class="academic-header"><h1>Exam Grading & Assessment Hub</h1><p>Manage your question papers, review student answers, and verify grades with AI assistance</p></div>', unsafe_allow_html=True)

    # Fetch high-level statistics
    assessments = AssessmentRepository.get_all_assessments()

    with get_db() as db:
        total_assessments = len(assessments)
        total_submissions = db.query(Submission).count()
        evaluations = db.query(Evaluation).all()
        total_evaluations = len(evaluations)
        pending_reviews = sum(1 for e in evaluations if "Pending" in (e.review_status or ""))
        approved_count = sum(1 for e in evaluations if "Approved" in (e.review_status or ""))

        avg_score_pct = 0.0
        if evaluations:
            scores_pct = [(e.final_awarded_marks / max(1.0, e.maximum_marks)) * 100 for e in evaluations]
            avg_score_pct = float(np.mean(scores_pct))

    # Top Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Active Exams</div>
            <div class="stat-value">{total_assessments}</div>
            <div class="stat-subtext">Question papers configured</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Student Papers</div>
            <div class="stat-value">{total_submissions}</div>
            <div class="stat-subtext">{total_evaluations} papers graded</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Awaiting Your Review</div>
            <div class="stat-value" style="color: #d97706;">{pending_reviews}</div>
            <div class="stat-subtext">Papers ready for teacher sign-off</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Class Average Score</div>
            <div class="stat-value" style="color: #1e3a8a;">{avg_score_pct:.1f}%</div>
            <div class="stat-subtext">Across all graded papers</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Active Assessment Quick Filter
    if not assessments:
        st.info("No exam question papers found. Navigate to **Create New Exam** in the sidebar to configure your first paper.")
        return

    st.subheader("Your Active Exams & Question Papers")
    as_df = pd.DataFrame(assessments)
    as_df = as_df.rename(columns={
        "title": "Exam Title",
        "subject": "Course Name",
        "course_code": "Course Code",
        "question_count": "Questions",
        "submission_count": "Submissions",
        "created_at": "Created Date"
    })
    st.dataframe(as_df[["Exam Title", "Course Name", "Course Code", "Questions", "Submissions", "Created Date"]], use_container_width=True, hide_index=True)

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Score Distribution & Review Status Charts
    col_chart1, col_chart2 = st.columns([3, 2])

    with col_chart1:
        st.subheader("Class Score Distribution")
        if evaluations:
            scores = [e.final_awarded_marks for e in evaluations]
            fig, ax = plt.subplots(figsize=(6, 3.2))
            fig.patch.set_facecolor('#f8fafc')
            ax.set_facecolor('#ffffff')

            bins = np.linspace(0, 10, 11)
            ax.hist(scores, bins=bins, color='#1e3a8a', edgecolor='#ffffff', alpha=0.9, rwidth=0.85)
            ax.set_xlabel("Marks Awarded (Scale 0 - 10)", fontsize=9, fontweight='bold', color='#1e293b')
            ax.set_ylabel("Number of Students", fontsize=9, fontweight='bold', color='#1e293b')
            ax.set_title("How the Class Performed", fontsize=10, fontweight='bold', color='#0f172a')
            ax.grid(axis='y', linestyle='--', alpha=0.3)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.info("Score distribution will appear here once student papers are evaluated.")

    with col_chart2:
        st.subheader("Teacher Review Progress")
        if evaluations:
            review_counts = {
                "Approved": approved_count,
                "Awaiting Review": pending_reviews,
                "Score Adjusted": sum(1 for e in evaluations if "Overridden" in (e.review_status or ""))
            }
            labels = [k for k, v in review_counts.items() if v > 0]
            sizes = [v for v in review_counts.values() if v > 0]
            colors_map = {'Approved': '#059669', 'Awaiting Review': '#f59e0b', 'Score Adjusted': '#3b82f6'}
            pie_colors = [colors_map.get(l, '#94a3b8') for l in labels]

            fig2, ax2 = plt.subplots(figsize=(4.5, 3.2))
            fig2.patch.set_facecolor('#f8fafc')
            if sizes:
                ax2.pie(sizes, labels=labels, autopct='%1.0f%%', startangle=140, colors=pie_colors,
                        textprops={'fontsize': 8, 'weight': 'bold'})
                ax2.axis('equal')
            ax2.set_title("Papers Reviewed vs Awaiting Review", fontsize=10, fontweight='bold', color='#0f172a')
            plt.tight_layout()
            st.pyplot(fig2)
        else:
            st.info("Review progress will appear here.")

    # Recent Evaluations
    st.subheader("Recently Graded Student Papers")
    if evaluations:
        recent_records = []
        for e in sorted(evaluations, key=lambda x: x.evaluated_at or 0, reverse=True)[:6]:
            sub = e.submission
            recent_records.append({
                "Student ID": sub.student_identifier if sub else "Unknown",
                "Marks Awarded": f"{e.final_awarded_marks:.2f} / {e.maximum_marks:.1f}",
                "AI Suggested": f"{e.ai_awarded_marks:.2f}",
                "Answer Match (BLEU)": f"{e.bleu_score:.1f}%" if e.bleu_score is not None else "-",
                "Phrasing (ROUGE)": f"{e.rouge_l_score:.1f}%" if e.rouge_l_score is not None else "-",
                "Status": e.review_status,
                "Reviewed By": e.reviewed_by or "Pending"
            })
        st.dataframe(pd.DataFrame(recent_records), use_container_width=True, hide_index=True)
    else:
        st.info("No evaluated papers recorded yet.")

    # Academic Disclaimer footer
    st.markdown("""
    <div class="academic-disclaimer">
        <b>Teacher's Note:</b> AI-suggested marks are recommendations designed to save you grading time.
        You always have full control to review, adjust, and approve final grades before publishing.
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    try:
        st.set_page_config(page_title="Faculty Assessment Dashboard - ExamJudge AI", page_icon="🎓", layout="wide")
    except Exception:
        pass
    from config.settings import ASSETS_DIR
    css_file = ASSETS_DIR / "styles.css"
    if css_file.exists():
        with open(css_file, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    render()
