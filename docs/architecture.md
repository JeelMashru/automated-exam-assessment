# System Architecture & Technical Specifications

**ExamJudge AI: Automated Descriptive Exam Assessment Engine**

---

## 1. High-Level Modular Architecture

The platform follows a layered, decoupled service architecture ensuring clean separation between interface, business logic, persistence, and external AI providers:

```
┌────────────────────────────────────────────────────────┐
│                   STREAMLIT FRONTEND                   │
│ (Dashboard, New Assessment, Results, Batch, Reports)   │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                    CORE LOGIC LAYER                    │
│                                                        │
│  ┌──────────────────┐  ┌────────────────────────────┐  │
│  │  PDFProcessor    │  │     SimilarityMetrics      │  │
│  │ (PyMuPDF / OCR)  │  │   (BLEU / ROUGE-L F1)      │  │
│  └─────────┬────────┘  └─────────────┬──────────────┘  │
│            │                         │                 │
│  ┌─────────▼────────┐  ┌─────────────▼──────────────┐  │
│  │ AnswerExtractor  │  │      ExamEvaluator         │  │
│  │(Injection Shield)│  │ (LLM-as-a-Judge Orchestr.) │  │
│  └─────────┬────────┘  └─────────────┬──────────────┘  │
│            │                         │                 │
│  ┌─────────▼────────┐  ┌─────────────▼──────────────┐  │
│  │   RubricEngine   │  │   ResponseValidator        │  │
│  │  (Sum Validator) │  │ (Pydantic / Clamp Logic)   │  │
│  └──────────────────┘  └────────────────────────────┘  │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                  PERSISTENCE LAYER                     │
│  SQLAlchemy ORM (SQLite / PostgreSQL ready)            │
│  Models: Assessments, Questions, Rubrics, Submissions, │
│          Evaluations, AuditLogs, Benchmarks            │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                 EXTERNAL PROVIDER APIS                 │
│  - Google Gemini API (`google-genai` SDK)              │
│  - OpenAI API (`gpt-4o-mini` / `gpt-4o`)               │
│  - Offline Calibrated Mock Evaluator                   │
└────────────────────────────────────────────────────────┘
```

---

## 2. Component Breakdown

### 2.1 PDF Ingestion & OCR (`core/pdf_processor.py`, `core/ocr_processor.py`)
- Reads multi-page student exam PDFs using PyMuPDF (`fitz`).
- Calculates word counts per page and flags scanned/image-based documents.
- Checks system capability for Tesseract OCR without crashing if binary is missing.

### 2.2 Security & Injection Shield (`core/answer_extractor.py`)
- Neutralizes prompt delimiters and markdown codeblocks.
- Disarms malicious jailbreak directives embedded in student answers.
- Segments multi-question answer papers based on question number patterns.

### 2.3 LLM Client Abstraction (`core/llm_client.py`)
- Implements `BaseLLMProvider` interface.
- Standardizes temperature to 0.0, JSON MIME typing, and retry loops with exponential backoff.
- Features `MockDemoProvider` for offline faculty demonstration without requiring API keys.

### 2.4 Programmatic Score Calculator (`core/score_calculator.py`)
- Eliminates LLM arithmetic errors.
- Enforces $0 \le \text{criterion\_awarded} \le \text{criterion\_max}$.
- Sums criteria programmatically and maps percentage to academic honors classifications.

### 2.5 Report Generator (`core/report_generator.py`)
- Produces university-standard marksheets using ReportLab.
- Exports standardized CSV files for LMS import and complete JSON diagnostics.
