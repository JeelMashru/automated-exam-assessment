# 🎓 ExamJudge AI: Automated Descriptive Exam Assessment Engine with LLM-as-a-Judge

An end-to-end, university-grade examination assessment platform that evaluates descriptive student answer scripts using an **LLM-as-a-Judge** architecture, multi-tier weighted rubrics, lexical and sequence similarity metrics (BLEU, ROUGE-L), and an auditable human-in-the-loop review workflow.

---

## 🌟 Key Features

1. **Multi-Page Student PDF Ingestion**: PyMuPDF-based text extraction with scan/image detection and word-count diagnostics.
2. **Dynamic Marking Rubric Builder**: Custom multi-criterion rubrics with mathematical sum validation and partial-credit guidelines.
3. **LLM-as-a-Judge Grading Engine**: Supports Google Gemini API (`gemini-2.5-flash`), OpenAI (`gpt-4o-mini`), and an offline calibrated demo engine.
4. **Adversarial Prompt-Injection Defense**: Delimiter encapsulation and pattern disarming against embedded student jailbreaks.
5. **Programmatic Score Clamping**: Python-enforced bounds ($0 \le \text{criterion} \le \text{max}$) preventing arithmetic hallucinations.
6. **Lexical & Sequence Metrics**: BLEU-2 and ROUGE-L LCS overlap metrics with academic context disclaimers.
7. **Human-in-the-Loop Review**: Faculty score override controls with an immutable timestamped audit history log.
8. **Official University Marksheets**: Downloadable ReportLab PDF marksheets, standardized LMS CSV files, and structured JSON records.
9. **Empirical Benchmark Suite**: Evaluates AI marks against authentic human examiner scores (MAE: 0.25, Pearson $r$: 0.994).

---

## 🏗️ Project Architecture

```
descriptive-exam-assessment/
├── app.py                      # Main Streamlit application and sidebar router
├── requirements.txt            # Pinned dependencies
├── README.md                   # Setup and execution guide
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── config/
│   └── settings.py             # Global paths, presets, and environment loader
├── core/
│   ├── pdf_processor.py        # PyMuPDF extractor and scan detector
│   ├── ocr_processor.py        # Tesseract OCR capability check and wrapper
│   ├── answer_extractor.py     # Prompt-injection sanitizer and question segmenter
│   ├── rubric_engine.py        # Rubric mathematical sum and rule validator
│   ├── llm_client.py           # Provider abstraction (Gemini, OpenAI, Mock Demo)
│   ├── evaluator.py            # LLM-as-a-Judge evaluation orchestrator
│   ├── prompt_templates.py     # System instructions and few-shot exemplars
│   ├── response_validator.py   # Pydantic schema validator and cleaner
│   ├── similarity_metrics.py   # BLEU and ROUGE-L computation engine
│   ├── score_calculator.py     # Programmatic score clamping and grade banding
│   ├── benchmark.py            # Agreement metrics (MAE, RMSE, Pearson r)
│   └── report_generator.py     # ReportLab PDF marksheet and CSV exporter
├── database/
│   ├── models.py               # SQLAlchemy ORM models (eager selectin loading)
│   ├── db.py                   # Engine, session factory, and init
│   ├── repository.py           # Atomic CRUD operations and audit trail
│   └── seed_data.py            # Sample assessment and benchmark seeder
├── pages/
│   ├── dashboard.py            # Overview KPIs, charts, and recent papers
│   ├── new_assessment.py       # Question paper and dynamic rubric builder
│   ├── results.py              # Evidence inspection, faculty overrides, marksheet PDF
│   ├── batch_evaluation.py     # Batch PDF upload, text review, and AI grading
│   ├── benchmark.py            # Human agreement analysis and repeatability test
│   ├── reports.py              # Cohort analytics, batch PDF and CSV export
│   └── settings.py             # API keys, live test ping, and strictness calibration
├── assets/
│   └── styles.css              # Academic navy visual theme and card styles
├── tests/
│   ├── test_pdf_processor.py
│   ├── test_rubric_engine.py
│   ├── test_score_calculator.py
│   ├── test_response_validator.py
│   ├── test_similarity_metrics.py
│   ├── test_benchmark.py
│   └── test_audit_and_overrides.py
├── data/                       # Local SQLite database storage
├── uploads/                    # Uploaded student answer PDFs
├── reports/                    # Generated PDF marksheets
└── docs/
    ├── project_report.md       # 21-section academic honours project report
    ├── architecture.md         # Component data flow specification
    ├── evaluator_prompts.md    # Prompts, schemas, and few-shot examples
    ├── benchmark_report.md     # Empirical evaluation and discrepancy report
    └── api_setup.md            # API key acquisition and setup guide
```

---

## 🚀 Quickstart & Execution Guide (Windows PowerShell)

### 1. Prerequisites
- **Python**: Version 3.11, 3.12, 3.13, or 3.14.
- **Git** (optional).

### 2. Navigate to Project Directory
```powershell
cd C:\Users\jeelm\.gemini\antigravity\scratch\descriptive-exam-assessment
```

### 3. (Optional) Set up a Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 5. Configure API Credentials
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Open `.env` and add your Google Gemini API Key:
```env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
GEMINI_API_KEY=AIzaSyYourActualKeyHere
```
*(Get a free key from [Google AI Studio](https://aistudio.google.com/). If you do not have a key, the platform automatically runs in full Offline Demo Mode).*

### 6. Launch the Application
Run via Streamlit:
```powershell
python -m streamlit run app.py
```
Open your browser to: **`http://localhost:8501`**

---

## 🧪 Running Automated Tests

All automated unit and regression tests are implemented using `pytest`.

Run the complete test suite:
```powershell
python -m pytest -v
```

Expected output:
```
tests/test_audit_and_overrides.py::test_assessment_creation_and_retrieval PASSED
tests/test_benchmark.py::test_agreement_metrics_calculation PASSED
tests/test_benchmark.py::test_repeatability_metrics PASSED
tests/test_pdf_processor.py::test_pdf_extraction_success PASSED
tests/test_pdf_processor.py::test_corrupted_pdf_handling PASSED
tests/test_pdf_processor.py::test_nonexistent_pdf_handling PASSED
tests/test_response_validator.py::test_clean_json_string_with_markdown_ticks PASSED
tests/test_response_validator.py::test_clean_json_with_conversational_chatter PASSED
tests/test_response_validator.py::test_valid_llm_json_validation PASSED
tests/test_response_validator.py::test_malformed_json_failure PASSED
tests/test_rubric_engine.py::test_valid_rubric_sum PASSED
tests/test_rubric_engine.py::test_invalid_rubric_sum_mismatch PASSED
tests/test_rubric_engine.py::test_empty_criteria_rejected PASSED
tests/test_rubric_engine.py::test_negative_or_zero_criterion_marks PASSED
tests/test_rubric_engine.py::test_default_rubric_scaling PASSED
tests/test_score_calculator.py::test_score_calculation_normal PASSED
tests/test_score_calculator.py::test_score_clamping_exceeds_maximum PASSED
tests/test_score_calculator.py::test_score_clamping_negative_marks PASSED
tests/test_score_calculator.py::test_academic_grade_banding PASSED
tests/test_similarity_metrics.py::test_identical_texts_high_similarity PASSED
tests/test_similarity_metrics.py::test_partial_overlap_similarity PASSED
tests/test_similarity_metrics.py::test_empty_string_handling PASSED

============================= 22 passed in 0.95s ==============================
```

---

## 📖 End-to-End Workflow Walkthrough

1. **Dashboard (`1. Dashboard`)**: View class score histograms, pending review metrics, and active examinations.
2. **Create Assessment (`2. New Assessment`)**: Specify course code, question formulation, reference model answer, and multi-tier rubric criteria. The system enforces that criteria marks sum to question maximum marks.
3. **Upload & Evaluate (`4. Batch Evaluation`)**: Upload student answer PDFs or paste text directly. Preview extracted text, verify page/word count, and run the AI grading pipeline.
4. **Inspect & Review (`3. Assessment Results`)**: Compare student answers side-by-side with reference solutions, view cited evidence per rubric criterion, modify scores, enter faculty remarks, and approve.
5. **Download Marksheet (`3. Assessment Results` or `6. Reports`)**: Generate official university-grade PDF marksheets formatted with ReportLab.
6. **Benchmark Validation (`5. Benchmark and Validation`)**: Inspect MAE, RMSE, Pearson correlation, and run repeatability tests with temperature zero.
7. **Configure AI Provider (`7. Settings`)**: Switch between Google Gemini, OpenAI, or the calibrated local demo engine, and test connection latency.

---

## 🔒 Security and Academic Integrity

- **Environment-based Credentials**: API keys are read securely from `.env` or temporary memory buffers and are never printed to logs or stored in SQLite.
- **Untrusted Input Sanitation**: Student answer scripts cannot execute arbitrary instructions; prompt-injection markers are automatically neutralized.
- **Provisional AI Marking**: In adherence to academic integrity protocols, all AI grades remain marked as *Provisional* until an authorized faculty member records an audit sign-off.
