"""
Batch Evaluation Page: Multi-PDF upload, text extraction, review, and AI evaluation pipeline.
"""

import streamlit as st
import os
import uuid
from pathlib import Path
from database.repository import AssessmentRepository
from database.db import get_db
from database.models import Assessment, Question
from core.pdf_processor import PDFProcessor
from core.evaluator import ExamEvaluator
from core.llm_client import get_llm_provider
from config.settings import UPLOADS_DIR


def render():
    st.markdown('<div class="academic-header"><h1>Batch Answer Evaluation</h1><p>Ingest Student Answer PDFs, Extract Text, and Execute LLM-as-a-Judge Grading</p></div>', unsafe_allow_html=True)

    assessments = AssessmentRepository.get_all_assessments()
    if not assessments:
        st.warning("No assessments found. Please create an assessment first.")
        return

    # Assessment & Question Selector
    col_a, col_q = st.columns(2)
    with col_a:
        as_options = {a["title"]: a["id"] for a in assessments}
        sel_as_title = st.selectbox("Select Target Assessment", list(as_options.keys()))
        sel_as_id = as_options[sel_as_title]

    with col_q:
        with get_db() as db:
            assessment_obj = db.query(Assessment).filter(Assessment.id == sel_as_id).first()
            questions = assessment_obj.questions if assessment_obj else []

        if not questions:
            st.error("No questions found for this assessment.")
            return

        q_map = {f"Q{q.question_number}: {q.question_text[:60]}... ({q.maximum_marks} marks)": q for q in questions}
        sel_q_label = st.selectbox("Select Question to Evaluate", list(q_map.keys()))
        selected_question = q_map[sel_q_label]

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Ingestion Method Tabs: File Upload vs Direct Text
    tab_pdf, tab_manual = st.tabs(["📁 Batch PDF Upload", "✍️ Manual Text / Sample Submission"])

    extracted_submissions = []

    with tab_pdf:
        st.subheader("Upload Student Answer Scripts (PDF)")
        st.caption("Upload one or multiple PDF files. Hand-written or scanned PDFs will be detected.")
        uploaded_files = st.file_uploader(
            "Select Student PDF Files",
            type=["pdf"],
            accept_multiple_files=True,
            help="Upload student answer papers in PDF format."
        )

        if uploaded_files:
            st.markdown(f"**{len(uploaded_files)} file(s) selected.** Processing text extraction...")
            for idx, file_obj in enumerate(uploaded_files, start=1):
                # Save file locally to uploads directory
                safe_name = f"{uuid.uuid4().hex[:8]}_{file_obj.name}"
                saved_path = UPLOADS_DIR / safe_name
                with open(saved_path, "wb") as f:
                    f.write(file_obj.getbuffer())

                # Extract text
                extraction = PDFProcessor.extract_text_from_pdf(str(saved_path))
                student_id = f"STUDENT_{file_obj.name.split('.')[0].upper()[:12]}"

                extracted_submissions.append({
                    "student_id": student_id,
                    "filename": file_obj.name,
                    "file_path": str(saved_path),
                    "text": extraction["text"],
                    "page_count": extraction["page_count"],
                    "word_count": extraction["word_count"],
                    "status": "SUCCESS" if extraction["success"] and not extraction["is_scanned"] else ("SCANNED_WARNING" if extraction["is_scanned"] else "FAILED"),
                    "error": extraction.get("error")
                })

    with tab_manual:
        st.subheader("Direct Text Ingestion (Quick Demo / Copy-Paste)")
        c_m1, c_m2 = st.columns([1, 2])
        with c_m1:
            manual_student_id = st.text_input("Candidate Identifier", value="DEMO-STUDENT-99")
        with c_m2:
            st.write("")

        manual_text = st.text_area(
            "Student Answer Submission Text",
            value=(
                "Virtual memory provides an illusion of a large memory space by combining RAM with disk storage. "
                "Paging divides logical memory into pages and physical memory into frames. "
                "The page table maps pages to frames, and if a page isn't in memory, a page fault brings it in."
            ),
            height=120
        )

        if st.button("➕ Stage Manual Submission for Evaluation"):
            extracted_submissions.append({
                "student_id": manual_student_id,
                "filename": "Direct_Input.txt",
                "file_path": "",
                "text": manual_text,
                "page_count": 1,
                "word_count": len(manual_text.split()),
                "status": "SUCCESS",
                "error": None
            })
            st.success(f"Candidate {manual_student_id} staged for evaluation.")

    # Review Extracted Submissions
    if extracted_submissions:
        st.markdown("<hr/>", unsafe_allow_html=True)
        st.subheader(f"Extracted Submissions ({len(extracted_submissions)} Staged)")

        # Summary preview table
        table_rows = []
        for s in extracted_submissions:
            table_rows.append({
                "Candidate ID": s["student_id"],
                "File": s["filename"],
                "Pages": s["page_count"],
                "Word Count": s["word_count"],
                "Status": s["status"],
                "Details / Warning": s["error"] or "Text successfully parsed."
            })
        st.dataframe(table_rows, use_container_width=True, hide_index=True)

        # Allow faculty to inspect and edit extracted text prior to running LLM
        with st.expander("🔍 Review / Edit Extracted Answer Text Prior to Grading"):
            for i, sub_item in enumerate(extracted_submissions):
                st.markdown(f"**Candidate: {sub_item['student_id']} ({sub_item['filename']})**")
                sub_item["text"] = st.text_area(
                    f"Edit Text for {sub_item['student_id']}",
                    value=sub_item["text"],
                    height=100,
                    key=f"text_edit_{i}"
                )

        st.markdown("<br/>", unsafe_allow_html=True)

        # Execution Controls
        col_exec, col_mode = st.columns([2, 2])
        provider = get_llm_provider()
        prov_info = provider.get_provider_info()

        with col_mode:
            st.info(f"Active Evaluator Mode: **{prov_info['mode']}** (Model: `{prov_info['model']}`)")

        with col_exec:
            start_eval_btn = st.button("🚀 Start AI Evaluation Pipeline", type="primary", use_container_width=True)

        if start_eval_btn:
            progress_bar = st.progress(0)
            status_text = st.empty()

            rubric_dict_list = [
                {
                    "criterion_name": c.criterion_name,
                    "maximum_marks": c.maximum_marks,
                    "description": c.description,
                    "partial_credit_rules": c.partial_credit_rules,
                    "expected_concepts": c.expected_concepts,
                    "critical_errors": c.critical_errors,
                }
                for c in selected_question.rubric_criteria
            ]

            evaluator = ExamEvaluator(provider=provider)
            eval_results = []

            for i, sub_item in enumerate(extracted_submissions):
                status_text.text(f"Evaluating submission {i+1} of {len(extracted_submissions)}: {sub_item['student_id']}...")

                # 1. Save submission record to DB
                sub_record = AssessmentRepository.add_submission(
                    assessment_id=sel_as_id,
                    student_identifier=sub_item["student_id"],
                    original_filename=sub_item["filename"],
                    file_path=sub_item["file_path"],
                    extracted_text=sub_item["text"],
                    page_count=sub_item["page_count"],
                    word_count=sub_item["word_count"],
                    extraction_status=sub_item["status"]
                )

                # 2. Evaluate using LLM-as-a-Judge engine
                res = evaluator.evaluate_submission(
                    assessment_id=sel_as_id,
                    student_id=sub_item["student_id"],
                    question_id=selected_question.id,
                    question_text=selected_question.question_text,
                    maximum_marks=selected_question.maximum_marks,
                    model_answer=selected_question.model_answer,
                    rubric_criteria=rubric_dict_list,
                    student_answer=sub_item["text"],
                    instructions=selected_question.evaluation_instructions,
                )

                if res["success"]:
                    data = res["data"]
                    # 3. Persist evaluation record
                    AssessmentRepository.save_evaluation(
                        submission_id=sub_record.id,
                        question_id=selected_question.id,
                        maximum_marks=selected_question.maximum_marks,
                        ai_awarded_marks=data["awarded_marks"],
                        criteria_scores=data["criteria"],
                        strengths=data["strengths"],
                        conceptual_gaps=data["conceptual_gaps"],
                        improvement_suggestions=data["improvement_suggestions"],
                        bleu_score=data["bleu_score"],
                        rouge_l_score=data["rouge_l_score"],
                        semantic_similarity=data["semantic_similarity"],
                        review_status="Pending Human Review"
                    )
                    eval_results.append({
                        "Candidate": sub_item["student_id"],
                        "Awarded Marks": f"{data['awarded_marks']:.2f} / {selected_question.maximum_marks:.1f}",
                        "BLEU (%)": f"{data['bleu_score']:.1f}%",
                        "ROUGE-L (%)": f"{data['rouge_l_score']:.1f}%",
                        "Status": "✅ Evaluated (Pending Review)"
                    })
                else:
                    eval_results.append({
                        "Candidate": sub_item["student_id"],
                        "Awarded Marks": "Error",
                        "BLEU (%)": "-",
                        "ROUGE-L (%)": "-",
                        "Status": f"❌ Failed: {res['error']}"
                    })

                progress_bar.progress((i + 1) / len(extracted_submissions))

            status_text.text("Batch Evaluation Completed!")
            st.success("All candidate submissions processed successfully!")
            st.dataframe(eval_results, use_container_width=True, hide_index=True)
            st.info("Navigate to **Assessment Results** to inspect individual criterion evidence, review justifications, and ratify scores.")
