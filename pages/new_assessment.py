"""
New Assessment Page: Configures question papers, reference model solutions, and validated multi-tier rubrics.
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
from core.rubric_engine import RubricEngine


def render():
    st.markdown('<div class="academic-header"><h1>Create New Exam & Marking Scheme</h1><p>Set up your exam questions, reference answer key, and criteria for grading</p></div>', unsafe_allow_html=True)

    # Initialize session state for rubric criteria if not present
    if "current_rubric" not in st.session_state:
        st.session_state["current_rubric"] = RubricEngine.create_default_rubric(max_marks=10.0)

    # Assessment Meta Section
    st.subheader("1. Exam & Course Information")
    col1, col2 = st.columns(2)
    with col1:
        assessment_title = st.text_input(
            "Exam or Assignment Title *",
            value="Midterm Assessment 2026",
            help="E.g. Final Semester Examination, Midterm Assessment, Lab Exam"
        )
        subject_name = st.text_input(
            "Course Name *",
            value="Operating Systems & System Software",
            help="E.g. Computer Science CS301, Data Structures"
        )
    with col2:
        course_code = st.text_input(
            "Course Code",
            value="CS301-OS",
            help="E.g. CS-401, IT-204"
        )
        institution = st.text_input(
            "Department / University",
            value="Faculty of Computing & Information Technology",
            help="E.g. Department of Computer Science, University Engineering College"
        )

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Question Details
    st.subheader("2. Question & Reference Solution")
    q_col1, q_col2 = st.columns([3, 1])
    with q_col1:
        question_text = st.text_area(
            "Question Text *",
            value="Explain the concept of Virtual Memory and how Paging is used to implement it.",
            height=90,
            help="Enter the exact descriptive question as given in the examination paper."
        )
    with q_col2:
        max_marks = st.number_input(
            "Total Marks for this Question *",
            min_value=1.0,
            max_value=100.0,
            value=10.0,
            step=1.0,
            help="Total maximum marks allocated to this question."
        )

    model_answer = st.text_area(
        "Reference Answer Key (Model Solution) *",
        value=(
            "Virtual memory is a memory management capability of an OS that creates the illusion to users of a very large main memory. "
            "It allows processes to execute even if they are not completely resident in physical RAM. "
            "Paging is the primary implementation mechanism, dividing virtual address space into fixed-size blocks called pages, and physical RAM into frames. "
            "The Memory Management Unit (MMU) uses a Page Table to translate virtual page numbers to physical frame numbers. "
            "When a requested page is not in RAM, a page fault exception is triggered, causing the OS to fetch the page from secondary storage."
        ),
        height=130,
        help="Provide the reference answer solution that the AI will use to check student answers."
    )

    col_inst1, col_inst2 = st.columns(2)
    with col_inst1:
        eval_instructions = st.text_area(
            "Grading Notes & Special Instructions for AI",
            value="Look for clear explanation of MMU address translation, page tables, and page fault handling. Accept equivalent standard terminology.",
            height=70,
            help="Special notes or exemptions for the AI evaluator."
        )
    with col_inst2:
        expected_keywords_str = st.text_area(
            "Key Concepts or Terms Expected (Comma Separated)",
            value="Virtual Memory, Paging, Frames, MMU, Page Table, Page Fault",
            height=70,
            help="Key domain terms that should ideally be mentioned or explained."
        )

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Rubric Configuration Section
    st.subheader("3. Grading Rubric & Marking Scheme")
    st.caption("Define the specific points you want the AI to evaluate. All criteria marks must add up to the question's total marks.")

    rubric_list = st.session_state["current_rubric"]

    # Action buttons for rubric
    btn_c1, btn_c2, btn_c3 = st.columns([1.8, 2.5, 2])
    with btn_c1:
        if st.button("➕ Add Marking Criterion"):
            rubric_list.append({
                "criterion_name": f"Criterion {len(rubric_list) + 1}",
                "maximum_marks": 2.0,
                "description": "",
                "partial_credit_rules": "Award partial credit for relevant points.",
                "expected_concepts": [],
                "critical_errors": []
            })
            st.rerun()

    with btn_c2:
        if st.button("↺ Use Standard 3-Part Scheme"):
            st.session_state["current_rubric"] = RubricEngine.create_default_rubric(max_marks=max_marks)
            st.rerun()

    # Render criteria inputs
    indices_to_remove = []
    current_sum = 0.0

    for i, crit in enumerate(rubric_list):
        with st.expander(f"Criterion #{i+1}: {crit.get('criterion_name', 'Unnamed')} ({crit.get('maximum_marks', 0)} marks)", expanded=True):
            r_c1, r_c2, r_c3 = st.columns([3, 1.2, 0.8])
            with r_c1:
                crit["criterion_name"] = st.text_input(f"Criterion Title #{i+1}", value=crit.get("criterion_name", ""), key=f"name_{i}")
            with r_c2:
                crit["maximum_marks"] = st.number_input(
                    f"Max Marks #{i+1}",
                    min_value=0.5,
                    max_value=float(max_marks),
                    value=float(crit.get("maximum_marks", 2.0)),
                    step=0.5,
                    key=f"marks_{i}"
                )
                current_sum += crit["maximum_marks"]
            with r_c3:
                st.write("")
                st.write("")
                if st.button("🗑️ Delete", key=f"del_{i}"):
                    indices_to_remove.append(i)

            crit["description"] = st.text_input(
                f"What should the student explain for this point? #{i+1}",
                value=crit.get("description", ""),
                key=f"desc_{i}",
                placeholder="E.g. Clear definition of the core concept and its purpose"
            )

            p_col1, p_col2 = st.columns(2)
            with p_col1:
                crit["partial_credit_rules"] = st.text_input(
                    f"How to award partial marks #{i+1}",
                    value=crit.get("partial_credit_rules", ""),
                    key=f"partial_{i}",
                    placeholder="E.g. Award 50% if definition is correct but mechanism is absent"
                )
            with p_col2:
                concepts_raw = crit.get("expected_concepts", [])
                c_str = ", ".join(concepts_raw) if isinstance(concepts_raw, list) else str(concepts_raw)
                concepts_input = st.text_input(
                    f"Key Points Expected #{i+1}",
                    value=c_str,
                    key=f"concepts_{i}",
                    placeholder="E.g. Address translation, Valid bit"
                )
                crit["expected_concepts"] = [c.strip() for c in concepts_input.split(",") if c.strip()]

    # Process removals
    if indices_to_remove:
        for idx in sorted(indices_to_remove, reverse=True):
            rubric_list.pop(idx)
        st.session_state["current_rubric"] = rubric_list
        st.rerun()

    # Rubric Validation Status Banner
    is_valid, validation_msg = RubricEngine.validate_question_rubric(max_marks, rubric_list)

    st.markdown("<br/>", unsafe_allow_html=True)
    if is_valid:
        st.success(f"✓ **Marking Scheme Valid**: Criteria sum to exactly {current_sum:.2f} / {max_marks:.2f} marks.")
    else:
        st.error(f"⚠️ **Marks Total Discrepancy**: {validation_msg}")

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Final Submission Button
    sub_col1, sub_col2 = st.columns([1.5, 3.5])
    with sub_col1:
        submit_btn = st.button("💾 Save Exam & Marking Scheme", type="primary", use_container_width=True, disabled=not is_valid)

    if submit_btn:
        if not assessment_title.strip() or not subject_name.strip() or not question_text.strip() or not model_answer.strip():
            st.error("Please fill in all required fields (Title, Course, Question, and Reference Answer).")
            return

        keywords_list = [k.strip() for k in expected_keywords_str.split(",") if k.strip()]

        question_payload = [{
            "question_text": question_text.strip(),
            "maximum_marks": max_marks,
            "model_answer": model_answer.strip(),
            "evaluation_instructions": eval_instructions.strip(),
            "expected_keywords": keywords_list,
            "rubric": rubric_list
        }]

        try:
            created_assessment = AssessmentRepository.create_assessment(
                title=assessment_title.strip(),
                subject=subject_name.strip(),
                course_code=course_code.strip() if course_code else None,
                institution=institution.strip() if institution else None,
                questions_data=question_payload
            )
            st.success(f"Exam '{created_assessment.title}' successfully saved with {len(rubric_list)} grading criteria!")
            st.balloons()
        except Exception as e:
            st.error(f"Failed to save exam to database: {str(e)}")


if __name__ == "__main__":
    try:
        st.set_page_config(page_title="Create Examination Assessment - ExamJudge AI", page_icon="🎓", layout="wide")
    except Exception:
        pass
    from config.settings import ASSETS_DIR
    css_file = ASSETS_DIR / "styles.css"
    if css_file.exists():
        with open(css_file, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    render()
