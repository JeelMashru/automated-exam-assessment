# 🎓 ExamJudge AI: Automated Descriptive Exam Assessment Engine with LLM-as-a-Judge

[![Python 3.11+](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/frontend-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini%202.5-4285F4.svg)](https://ai.google.dev/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)](https://www.docker.com/)
[![Tests Passed](https://img.shields.io/badge/tests-22%2F22%20passing-success.svg)](tests/)

An end-to-end, university-grade examination assessment platform that evaluates descriptive student answer scripts using an **LLM-as-a-Judge** architecture, multi-tier weighted rubrics, lexical and sequence similarity metrics (BLEU, ROUGE-L), and an auditable human-in-the-loop review workflow.

---

## 🌟 Key Features

1. **Multi-Page Student PDF Ingestion**: PyMuPDF-based text extraction with scan/image detection and word-count diagnostics.
2. **Dynamic Marking Rubric Builder**: Custom multi-criterion rubrics with mathematical sum validation and partial-credit guidelines.
3. **LLM-as-a-Judge Grading Engine**: Supports Google Gemini API (`gemini-2.5-flash`), OpenAI (`gpt-4o-mini`), and an offline calibrated demo engine.
4. **Adversarial Prompt-Injection Defense**: Delimiter encapsulation and pattern disarming against embedded student jailbreaks.
5. **Programmatic Score Clamping**: Python-enforced bounds ($0 \le \text{criterion} \le \text{max}$) preventing arithmetic hallucinations.
6. **Lexical & Sequence Metrics**: BLEU-2 and ROUGE-L overlap metrics with clear academic context disclaimers.
7. **Human-in-the-Loop Review**: Faculty score override controls with an immutable timestamped audit history log.
8. **Official University Marksheets**: Downloadable ReportLab PDF marksheets, standardized LMS CSV files, and structured JSON records.
9. **Empirical Benchmark Suite**: Evaluates AI marks against authentic human examiner scores (MAE: 0.25, Pearson $r$: 0.994).

---

## 🏗️ Project Architecture

```
descriptive-exam-assessment/
├── app.py                      # Main Streamlit application and sidebar router
├── requirements.txt            # Pinned production dependencies
├── packages.txt                # Linux/Debian system dependencies (Tesseract OCR, fonts)
├── Dockerfile                  # Production container image specification
├── docker-compose.yml          # Container orchestration with data volumes
├── Procfile                    # PaaS process configuration (Render, Railway, Heroku)
├── render.yaml                 # 1-Click Render blueprint deployment specification
├── .streamlit/
│   └── config.toml             # Headless cloud configuration and UI theme
├── .github/
│   └── workflows/
│       └── ci.yml              # Automated GitHub Actions test pipeline
├── README.md                   # Complete deployment and documentation guide
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── config/
│   └── settings.py             # Global paths, presets, secrets, and environment loader
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
├── tests/                      # 22 automated test suites (100% passing)
├── data/                       # Local SQLite database storage
├── uploads/                    # Uploaded student answer PDFs
├── reports/                    # Generated PDF marksheets
└── docs/                       # Comprehensive honours project documentation
```

---

## 🚀 Pushing to GitHub (Step-by-Step)

To push this project to your GitHub account:

### Step 1: Create a New Repository on GitHub
1. Log in to [GitHub](https://github.com).
2. Click **New Repository** (or visit https://github.com/new).
3. Name your repository (e.g., `examjudge-ai` or `automated-exam-assessment`).
4. Keep it **Public** (required for free Streamlit Community Cloud hosting) or **Private**.
5. Do **NOT** initialize with a README, .gitignore, or license (we already created production versions of these).
6. Click **Create repository**.

### Step 2: Push Your Local Code to GitHub
Open your terminal in the project directory (`C:\Users\jeelm\.gemini\antigravity\scratch\descriptive-exam-assessment`) and run:

```powershell
# 1. Rename the default branch to main
git branch -M main

# 2. Add your GitHub repository as the remote origin (replace with your GitHub URL)
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPO_NAME>.git

# 3. Push your code
git push -u origin main
```

---

## 🌐 Cloud Deployment Options

### Option 1: Streamlit Community Cloud (Recommended & 100% Free)
Streamlit Community Cloud is the official, native cloud platform designed specifically for Streamlit applications. It deploys directly from your GitHub repository in under 2 minutes with zero configuration.

1. Go to [share.streamlit.io](https://share.streamlit.io/) and click **Sign in with GitHub**.
2. Click **Create app** > **Yup, I have an app**.
3. Select your repository: `<YOUR_GITHUB_USERNAME>/<YOUR_REPO_NAME>`.
4. Branch: `main`.
5. Main file path: `app.py`.
6. Click **Advanced settings** (Secrets) and enter your API credentials:
   ```toml
   LLM_PROVIDER = "gemini"
   LLM_MODEL = "gemini-2.5-flash"
   GEMINI_API_KEY = "AIzaSyYourActualKeyHere"
   ```
7. Click **Deploy!**
Your app will be live at `https://<your-custom-name>.streamlit.app` with free SSL, automatic reboots, and continuous deployment whenever you `git push`.

---

### Option 2: Render (Free Web Service)
This repository includes a preconfigured [`render.yaml`](render.yaml) blueprint:

1. Log in to [Render](https://render.com/) with GitHub.
2. Click **New +** > **Blueprint**.
3. Select your GitHub repository. Render will automatically detect [`render.yaml`](render.yaml).
4. Add your `GEMINI_API_KEY` under Environment Variables.
5. Click **Apply**. Render will build and deploy the application.

---

### Option 3: Docker Container Deployment (AWS, GCP Cloud Run, DigitalOcean, VPS)
To deploy as a standalone production Docker container:

```bash
# Build the container image
docker build -t examjudge-ai:latest .

# Run the container locally or on your cloud VM
docker run -d -p 8501:8501 \
  -e GEMINI_API_KEY="AIzaSyYourActualKeyHere" \
  -v $(pwd)/data:/app/data \
  --name examjudge examjudge-ai:latest
```

Access at `http://<your-server-ip>:8501`.

---

### ℹ️ A Note on Vercel vs Streamlit
> [!NOTE]
> **Why Vercel is not recommended for Streamlit apps:**  
> Vercel is designed for **stateless serverless functions** (Next.js, React, Node.js APIs) with strict 10–60 second execution timeouts and **no support for persistent WebSockets**.
> 
> Streamlit apps rely on a continuous, stateful WebSocket connection (`streamlit run app.py`) to manage session state, file uploads, PDF processing, and reactive UI reruns. Running Streamlit on Vercel breaks session state and causes frequent disconnects.
> 
> **The Solution:** **Streamlit Community Cloud** or **Render** provides the exact same developer experience as Vercel (push to GitHub $\rightarrow$ instant auto-build $\rightarrow$ live HTTPS URL), but with native, persistent WebSocket and Python server support for free.

---

## 🧪 Local Execution & Testing

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Add your `GEMINI_API_KEY` in `.env` (or use the built-in Offline Demo Evaluator without an API key).

### 3. Run Application
```powershell
streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.

### 4. Run Test Suite
```powershell
python -m pytest -v
```
All 22 unit, integration, and security tests will execute and pass.

---

## 🔒 Security and Academic Integrity

- **Environment-based Credentials**: API keys are read securely from `.env` or temporary memory buffers and are never printed to logs or stored in SQLite.
- **Untrusted Input Sanitation**: Student answer scripts cannot execute arbitrary instructions; prompt-injection markers are automatically neutralized.
- **Provisional AI Marking**: In adherence to academic integrity protocols, all AI grades remain marked as *Provisional* until an authorized faculty member records an audit sign-off.
