"""
Assessment Results and Faculty Human-in-the-Loop Review Page.
Enables detailed evidence inspection, score overrides, and audit trails.
"""

import streamlit as st
import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import json
from database.repository import AssessmentRepository
from database.db import get_db
from database.models import Assessment, Evaluation, Submission
from core.score_calculator import ScoreCalculator
from core.report_generator import ReportGenerator


def render():
    st.markdown('<div class="academic-header"><h1>Student Results & Teacher Review</h1><p>Review student answers, inspect AI grading recommendations, and confirm or adjust marks</p></div>', unsafe_allow_html=True)

    assessments = AssessmentRepository.get_all_assessments()
    if not assessments:
        st.info("No exams or assignments currently available. Create one first.")
        return

    # Assessment Selector
    as_options = {a["title"]: a["id"] for a in assessments}
    sel_as_title = st.selectbox("Select Exam or Assignment", list(as_options.keys()))
    sel_as_id = as_options[sel_as_title]

    # Load evaluations for selected assessment
    evaluations = AssessmentRepository.get_evaluations_for_assessment(sel_as_id)
    if not evaluations:
        st.warning(f"No student papers have been graded for '{sel_as_title}' yet. Go to **📁 Grade Papers (Batch Upload)** to grade student answer papers.")
        return

    # Student Selector
    student_opts = {
        f"{e['student_identifier']} ({e['filename'] or 'Direct Text'}) — Final Marks: {e['final_awarded_marks']:.1f}/{e['maximum_marks']:.1f} [{e['review_status']}]": e
        for e in evaluations
    }
    sel_student_label = st.selectbox("Select Student Paper to Inspect", list(student_opts.keys()))
    current_eval = student_opts[sel_student_label]

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Top KPI Metrics for this submission
    m1, m2, m3, m4 = st.columns(4)
    pct = (current_eval["final_awarded_marks"] / max(1.0, current_eval["maximum_marks"])) * 100
    grade_band, grade_desc = ScoreCalculator.get_academic_grade_band(pct)

    with m1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Final Marks Awarded</div>
            <div class="stat-value">{current_eval['final_awarded_marks']:.2f} / {current_eval['maximum_marks']:.1f}</div>
            <div class="stat-subtext">Original AI Recommendation: {current_eval['ai_awarded_marks']:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Percentage & Grade</div>
            <div class="stat-value" style="color: #2563eb;">{pct:.1f}%</div>
            <div class="stat-subtext">{grade_band[:24]}</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        b_val = f"{current_eval['bleu_score']:.1f}%" if current_eval['bleu_score'] is not None else "N/A"
        r_val = f"{current_eval['rouge_l_score']:.1f}%" if current_eval['rouge_l_score'] is not None else "N/A"
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Answer Match with Key</div>
            <div class="stat-value" style="font-size: 1.35rem;">Words: {b_val}</div>
            <div class="stat-subtext">Phrasing (ROUGE-L): {r_val}</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        status_color = "#059669" if "Approv" in current_eval["review_status"] else "#d97706"
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Teacher Review Status</div>
            <div class="stat-value" style="color: {status_color}; font-size: 1.35rem;">{current_eval['review_status']}</div>
            <div class="stat-subtext">{current_eval.get('reviewed_by') or 'Awaiting Teacher Sign-off'}</div>
        </div>
        """, unsafe_allow_html=True)

    # Academic Notice regarding BLEU/ROUGE-L
    st.markdown("""
    <div class="academic-disclaimer">
        <b>💡 Teacher's Note on Word Matching (BLEU & ROUGE-L):</b> These metrics show how closely the student's phrasing matches your reference answer key.
        In descriptive exams, students who explain concepts accurately in their own words are given full marks, even if their word-for-word overlap is lower.
    </div>
    """, unsafe_allow_html=True)

    # Side-by-Side Reference Solution vs Student Submission
    st.subheader("Compare Student Answer with Reference Solution")
    tab_comp, tab_text = st.tabs(["Side-by-Side Comparison", "Full Student Answer"])
    
    with tab_comp:
        col_ans1, col_ans2 = st.columns(2)
        with col_ans1:
            st.markdown("##### 📘 Official Reference Answer Key")
            with get_db() as db:
                eval_obj = db.query(Evaluation).filter(Evaluation.id == current_eval["evaluation_id"]).first()
                q_text = eval_obj.question.question_text if eval_obj and eval_obj.question else "N/A"
                m_answer = eval_obj.question.model_answer if eval_obj and eval_obj.question else "N/A"
            st.info(f"**Question:** {q_text}")
            st.text_area("Model Answer", value=m_answer, height=180, disabled=True, label_visibility="collapsed")
        with col_ans2:
            st.markdown("##### ✍️ Student's Written Answer")
            student_raw = current_eval.get("extracted_text", "")
            w_count = len(student_raw.split())
            st.caption(f"Student ID: **{current_eval['student_identifier']}** | Word Count: **{w_count} words**")
            st.text_area("Student Text", value=student_raw, height=210, disabled=True, label_visibility="collapsed")

    with tab_text:
        st.code(current_eval.get("extracted_text", "No text found"), language="markdown")

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Detailed Criterion Breakdown Table
    st.subheader("Marking Breakdown & Specific Feedback")
    criteria = current_eval.get("criteria", [])
    if criteria:
        for idx, crit in enumerate(criteria, start=1):
            with st.expander(f"Criterion #{idx}: {crit.get('criterion', 'Criterion')} — Marks: {crit.get('awarded_marks', 0)} / {crit.get('maximum_marks', 0)}", expanded=True):
                c_col1, c_col2 = st.columns([2, 1])
                with c_col1:
                    st.markdown(f"**Teacher Explanation:** {crit.get('justification', 'No justification provided.')}")
                    st.markdown(f"**Quote from Student's Answer:** *\"{crit.get('evidence', 'No direct quote cited.')}\"*")
                with c_col2:
                    missing = crit.get("missing_concepts", [])
                    errors = crit.get("errors", [])
                    if missing:
                        st.markdown("**Points Missed or Incomplete:**")
                        for m in missing:
                            st.markdown(f"- ⚠️ {m}")
                    if errors:
                        st.markdown("**Misconceptions or Errors:**")
                        for err in errors:
                            st.markdown(f"- ❌ {err}")
                    if not missing and not errors:
                        st.markdown("✅ *Student satisfied all key requirements for this criterion.*")

    # Qualitative Diagnostics
    st.subheader("Student Strengths & Improvement Areas")
    d1, d2, d3 = st.columns(3)
    with d1:
        st.markdown("##### 🟢 What the Student Did Well")
        strengths = current_eval.get("strengths", [])
        if strengths:
            for s in strengths:
                st.markdown(f"- {s}")
        else:
            st.caption("No specific strengths noted.")
    with d2:
        st.markdown("##### 🟡 Concepts Missed or Incomplete")
        gaps = current_eval.get("gaps", [])
        if gaps:
            for g in gaps:
                st.markdown(f"- {g}")
        else:
            st.caption("No major conceptual gaps identified.")
    with d3:
        st.markdown("##### 💡 Constructive Tips for the Student")
        suggs = current_eval.get("suggestions", [])
        if suggs:
            for sg in suggs:
                st.markdown(f"- {sg}")
        else:
            st.caption("No specific suggestions recorded.")

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Human-in-the-Loop Review Panel
    st.subheader("Teacher Review & Score Adjustment")
    st.caption("Confirm the AI's grading recommendation or adjust the score with your own remarks.")

    rev_col1, rev_col2 = st.columns([2, 3])
    with rev_col1:
        override_score = st.number_input(
            "Final Marks (Adjust or Confirm)",
            min_value=0.0,
            max_value=float(current_eval["maximum_marks"]),
            value=float(current_eval["final_awarded_marks"]),
            step=0.25,
            help="You can adjust the marks here if you feel the answer deserved more or fewer points."
        )
        faculty_name = st.text_input("Teacher Name / Evaluator ID", value=current_eval.get("reviewed_by") or "Prof. Academic Evaluator")

    with rev_col2:
        faculty_remarks = st.text_area(
            "Teacher Remarks / Notes for Student",
            value=current_eval.get("human_feedback") or "Verified against rubric. Conceptual explanations are sound.",
            height=95,
            help="Add notes explaining any mark adjustments or encouraging comments for the student."
        )

    act_col1, act_col2, act_col3 = st.columns([1.8, 1.8, 2.4])
    with act_col1:
        if st.button("✅ Approve & Confirm Marks", type="primary", use_container_width=True):
            AssessmentRepository.override_evaluation(
                evaluation_id=current_eval["evaluation_id"],
                new_score=override_score,
                comments=faculty_remarks,
                reviewer_name=faculty_name,
                status="Approved by Teacher"
            )
            st.success("Marks approved and saved to the student record!")
            st.rerun()

    with act_col2:
        if st.button("✏️ Save Adjusted Marks", use_container_width=True):
            AssessmentRepository.override_evaluation(
                evaluation_id=current_eval["evaluation_id"],
                new_score=override_score,
                comments=faculty_remarks,
                reviewer_name=faculty_name,
                status="Adjusted by Teacher"
            )
            st.info("Score adjustment recorded with your teacher remarks.")
            st.rerun()

    # Audit Trail History
    audit_logs = AssessmentRepository.get_audit_trail(current_eval["evaluation_id"])
    if audit_logs:
        st.markdown("##### 📜 Review History & Changes")
        st.dataframe(audit_logs, use_container_width=True, hide_index=True)

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Marksheet PDF & Exports
    st.subheader("Download Student Grade Sheet")
    pdf_col, json_col = st.columns([2, 2])

    with pdf_col:
        if st.button("📄 Generate Student Grade Sheet (PDF)", type="primary"):
            with st.spinner("Generating PDF grade sheet..."):
                pdf_path = ReportGenerator.generate_student_pdf_marksheet(
                    assessment_title=sel_as_title,
                    subject="Examination Module",
                    student_id=current_eval["student_identifier"],
                    question_text=q_text,
                    max_marks=current_eval["maximum_marks"],
                    final_marks=current_eval["final_awarded_marks"],
                    ai_marks=current_eval["ai_awarded_marks"],
                    review_status=current_eval["review_status"],
                    criteria_breakdown=current_eval.get("criteria", []),
                    strengths=current_eval.get("strengths", []),
                    gaps=current_eval.get("gaps", []),
                    suggestions=current_eval.get("suggestions", []),
                    bleu_score=current_eval.get("bleu_score"),
                    rouge_l_score=current_eval.get("rouge_l_score"),
                    human_feedback=current_eval.get("human_feedback"),
                    reviewed_by=current_eval.get("reviewed_by")
                )
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                st.download_button(
                    label="⬇️ Download Grade Sheet (PDF)",
                    data=pdf_bytes,
                    file_name=os.path.basename(pdf_path),
                    mime="application/pdf"
                )

    with json_col:
        json_dump = json.dumps(current_eval, indent=2, default=str)
        st.download_button(
            label="📁 Download Evaluation Data (JSON)",
            data=json_dump,
            file_name=f"eval_{current_eval['student_identifier']}.json",
            mime="application/json"
        )


if __name__ == "__main__":
    try:
        st.set_page_config(page_title="Assessment Results - ExamJudge AI", page_icon="🎓", layout="wide")
    except Exception:
        pass
    from config.settings import ASSETS_DIR
    css_file = ASSETS_DIR / "styles.css"
    if css_file.exists():
        with open(css_file, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    render()
