# Automated Descriptive Exam Assessment Engine with LLM-as-a-Judge
# Project Configuration

import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env if present
load_dotenv(BASE_DIR / ".env")

# Storage directories
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = BASE_DIR / "uploads"
REPORTS_DIR = BASE_DIR / "reports"
ASSETS_DIR = BASE_DIR / "assets"

for directory in [DATA_DIR, UPLOADS_DIR, REPORTS_DIR, ASSETS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'assessment.db'}")

# LLM Providers Configuration
DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  # 'gemini', 'openai', 'mock'
DEFAULT_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")

# API Keys (read from environment, NEVER hardcoded)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or ""

# LLM Parameters
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.0"))
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT", "60"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))

# Metrics Settings
ENABLE_EMBEDDINGS = os.getenv("ENABLE_EMBEDDINGS", "False").lower() in ("true", "1", "yes")

# Evaluation strictness calibration presets
CALIBRATION_PRESETS = {
    "balanced": {
        "name": "Standard Academic (Balanced)",
        "description": "Standard university marking standard awarding partial credit for logically sound explanations and conceptual alignment.",
        "strictness_factor": 1.0,
        "partial_credit_generosity": "moderate",
    },
    "lenient": {
        "name": "Formative / Exploratory (Lenient)",
        "description": "Encourages conceptual grasp and rewards valid informal descriptions and approximations.",
        "strictness_factor": 0.8,
        "partial_credit_generosity": "high",
    },
    "strict": {
        "name": "Rigorous / Professional (Strict)",
        "description": "Requires precise terminology, formal definitions, and penalizes omitted required elements.",
        "strictness_factor": 1.2,
        "partial_credit_generosity": "conservative",
    }
}
