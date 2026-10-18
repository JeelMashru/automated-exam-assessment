"""
Reports and Exports Page: Marksheet compilation, CSV/JSON batch exports, and cohort analytics.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import json
import os
from database.repository import AssessmentRepository
from database.db import get_db
from database.models import Assessment, Evaluation
from core.report_generator import ReportGenerator
from config.settings import REPORTS_DIR


def render():
    st.markdown('<div class="academic-header"><h1>Reports & Analytical Exports</h1><p>Export Official PDF Marksheets, Standardized CSV Records, and Class Diagnostics</p></div>', unsafe_allow_html=True)

    assessments = AssessmentRepository.get_all_assessments()
    if not assessments:
        st.warning("No assessments found. Please create an assessment first.")
        return

    as_options = {a["title"]: a["id"] for a in assessments}
    sel_as_title = st.selectbox("Select Target Examination", list(as_options.keys()))
    sel_as_id = as_options[sel_as_title]

    evaluations = AssessmentRepository.get_evaluations_for_assessment(sel_as_id)
    if not evaluations:
        st.info("No evaluated answer scripts available for this assessment yet.")
        return

    st.subheader(f"Cohort Evaluation Summary ({len(evaluations)} Students)")

    # Dataframe overview
    df_rows = []
    for ev in evaluations:
        pct = (ev["final_awarded_marks"] / max(1.0, ev["maximum_marks"])) * 100
        df_rows.append({
            "Student Identifier": ev["student_identifier"],
            "Awarded Marks": f"{ev['final_awarded_marks']:.2f}",
            "Max Marks": f"{ev['maximum_marks']:.1f}",
            "Percentage (%)": f"{pct:.1f}%",
            "BLEU (%)": f"{ev['bleu_score']:.1f}%" if ev['bleu_score'] is not None else "-",
            "ROUGE-L (%)": f"{ev['rouge_l_score']:.1f}%" if ev['rouge_l_score'] is not None else "-",
            "Review Status": ev["review_status"],
            "Evaluator": ev["reviewed_by"] or "Pending"
        })
    df = pd.DataFrame(df_rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Export Action Buttons
    st.subheader("Official Academic Export Formats")
    exp_c1, exp_c2, exp_c3 = st.columns(3)

    with exp_c1:
        st.markdown("##### 📊 Standardized CSV Export")
        st.caption("Compatible with university LMS grading portals (Canvas, Moodle, Blackboard).")
        csv_data = ReportGenerator.export_batch_csv(evaluations)
        st.download_button(
            label="⬇️ Download Batch CSV",
            data=csv_data,
            file_name=f"Assessment_{sel_as_title.replace(' ', '_')}_Marks.csv",
            mime="text/csv",
            type="primary"
        )

    with exp_c2:
        st.markdown("##### 📁 Complete JSON Export")
        st.caption("Full structured diagnostic evaluation outputs and criteria logs.")
        json_data = ReportGenerator.export_batch_json(evaluations)
        st.download_button(
            label="⬇️ Download Structured JSON",
            data=json_data,
            file_name=f"Assessment_{sel_as_title.replace(' ', '_')}_Full.json",
            mime="application/json"
        )

    with exp_c3:
        st.markdown("##### 📄 PDF Marksheets")
        st.caption("Generate official PDF marksheets with faculty review sign-offs.")
        if st.button("Generate Marksheets for All Students"):
            with st.spinner("Generating individual student PDF marksheets..."):
                for ev in evaluations:
                    ReportGenerator.generate_student_pdf_marksheet(
                        assessment_title=sel_as_title,
                        subject="Examination Module",
                        student_id=ev["student_identifier"],
                        question_text="Examination Question",
                        max_marks=ev["maximum_marks"],
                        final_marks=ev["final_awarded_marks"],
                        ai_marks=ev["ai_awarded_marks"],
                        review_status=ev["review_status"],
                        criteria_breakdown=ev.get("criteria", []),
                        strengths=ev.get("strengths", []),
                        gaps=ev.get("gaps", []),
                        suggestions=ev.get("suggestions", []),
                        bleu_score=ev.get("bleu_score"),
                        rouge_l_score=ev.get("rouge_l_score"),
                        human_feedback=ev.get("human_feedback"),
                        reviewed_by=ev.get("reviewed_by")
                    )
                st.success(f"All marksheets generated in '{REPORTS_DIR}' folder.")

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Criterion Performance Diagnostics Chart
    st.subheader("Rubric Criterion Cohort Performance")
    crit_performance = {}
    for ev in evaluations:
        for c in ev.get("criteria", []):
            name = c.get("criterion", "Criterion")
            max_m = float(c.get("maximum_marks", 1.0))
            awarded = float(c.get("awarded_marks", 0.0))
            ratio = (awarded / max_m) * 100 if max_m > 0 else 0

            if name not in crit_performance:
                crit_performance[name] = []
            crit_performance[name].append(ratio)

    if crit_performance:
        avg_crit_pct = {k: np.mean(v) for k, v in crit_performance.items()}
        fig, ax = plt.subplots(figsize=(8, 3.2))
        fig.patch.set_facecolor('#f8fafc')
        ax.set_facecolor('#ffffff')

        names = list(avg_crit_pct.keys())
        # Shorten names for labels
        short_names = [n[:28] + "..." if len(n) > 28 else n for n in names]
        values = list(avg_crit_pct.values())

        bars = ax.barh(short_names, values, color='#1e3a8a', height=0.5)
        ax.set_xlim(0, 100)
        ax.set_xlabel("Cohort Mastery Percentage (%)", fontsize=9, fontweight='bold', color='#1e293b')
        ax.set_title("Average Student Performance by Marking Rubric Criterion", fontsize=10, fontweight='bold', color='#0f172a')
        ax.grid(axis='x', linestyle=':', alpha=0.5)

        for bar in bars:
            width = bar.get_width()
            ax.text(width + 1.5, bar.get_y() + bar.get_height() / 2, f"{width:.1f}%",
                    va='center', ha='left', fontsize=8, fontweight='bold', color='#1e293b')

        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.info("Criterion analytics will populate once submissions are evaluated.")
