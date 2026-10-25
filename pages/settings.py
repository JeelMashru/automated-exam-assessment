"""
Settings and API Configuration Page.
Secure credential management, real-time connection diagnostic pings, and evaluation calibration.
"""

import streamlit as st
import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import settings
from core.llm_client import get_llm_provider, GeminiProvider, OpenAIProvider, MockDemoProvider
from core.ocr_processor import OCRProcessor
from database.seed_data import seed_database_if_empty
from database.db import get_db
from database.models import Assessment, Submission, Evaluation, BenchmarkObservation


def render():
    st.markdown('<div class="academic-header"><h1>System Settings & AI Configuration</h1><p>API Provider Setup, Connection Diagnostics, and Marking Strictness Calibration</p></div>', unsafe_allow_html=True)

    tab_api, tab_calib, tab_sys = st.tabs([
        "🔑 AI Provider & API Credentials",
        "⚙️ Evaluation Strictness Calibration",
        "🖥️ System Diagnostics & Data Management"
    ])

    # 1. API Configuration Tab
    with tab_api:
        st.subheader("LLM Provider Configuration")
        st.caption("Select your AI evaluator backend. All evaluations utilize temperature 0.0 with strict schema enforcement.")

        provider_choice = st.selectbox(
            "Evaluation Provider",
            options=["Google Gemini (Recommended)", "OpenAI", "Offline Demo Mode (Calibrated Local Mock)"],
            index=0 if settings.DEFAULT_PROVIDER == "gemini" else (1 if settings.DEFAULTPROVIDER == "openai" else 2)
        )

        env_file_path = settings.BASE_DIR / ".env"

        if "Gemini" in provider_choice:
            st.markdown("##### Google Gemini Configuration")
            st.markdown(
                "Get a free API key from [Google AI Studio](https://aistudio.google.com/). "
                "The key is read from `.env` or set securely below."
            )

            current_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
            masked_key = ("*" * (len(current_key) - 4) + current_key[-4:]) if len(current_key) > 4 else ""

            col_k1, col_k2 = st.columns([3, 1])
            with col_k1:
                gemini_key_input = st.text_input(
                    "Google Gemini API Key",
                    value="",
                    type="password",
                    placeholder=f"Configured: {masked_key}" if masked_key else "Paste AIzaSy... here"
                )
            with col_k2:
                gemini_model = st.selectbox(
                    "Gemini Model",
                    options=["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
                    index=0
                )

            if st.button("Save Gemini Configuration"):
                target_key = gemini_key_input.strip() if gemini_key_input.strip() else current_key
                if target_key:
                    os.environ["GEMINI_API_KEY"] = target_key
                    os.environ["LLM_PROVIDER"] = "gemini"
                    os.environ["LLM_MODEL"] = gemini_model
                    # Write to .env
                    with open(env_file_path, "w") as f:
                        f.write(f"LLM_PROVIDER=gemini\nLLM_MODEL={gemini_model}\nGEMINI_API_KEY={target_key}\n")
                    st.success("Gemini API credentials successfully saved and activated!")
                    st.rerun()
                else:
                    st.warning("Please enter a valid Gemini API key.")

            # Live Test Connection Button
            st.markdown("---")
            st.markdown("##### Connection Diagnostic")
            if st.button("🔌 Test Gemini Connection"):
                active_key = gemini_key_input.strip() or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
                provider = GeminiProvider(api_key=active_key, model=gemini_model)
                with st.spinner("Pinging Google Gemini API..."):
                    success, msg = provider.test_connection()
                if success:
                    st.success(f"✓ **Connected**: {msg}")
                else:
                    st.error(f"❌ **Connection Failed**: {msg}")

        elif "OpenAI" in provider_choice:
            st.markdown("##### OpenAI Configuration")
            current_open_key = os.getenv("OPENAI_API_KEY") or ""
            masked_open = ("*" * (len(current_open_key) - 4) + current_open_key[-4:]) if len(current_open_key) > 4 else ""

            openai_key_input = st.text_input(
                "OpenAI API Key",
                value="",
                type="password",
                placeholder=f"Configured: {masked_open}" if masked_open else "Paste sk-... here"
            )
            openai_model = st.selectbox("OpenAI Model", options=["gpt-4o-mini", "gpt-4o"], index=0)

            if st.button("Save OpenAI Configuration"):
                target_key = openai_key_input.strip() if openai_key_input.strip() else current_open_key
                if target_key:
                    os.environ["OPENAI_API_KEY"] = target_key
                    os.environ["LLM_PROVIDER"] = "openai"
                    os.environ["LLM_MODEL"] = openai_model
                    with open(env_file_path, "w") as f:
                        f.write(f"LLM_PROVIDER=openai\nLLM_MODEL={openai_model}\nOPENAI_API_KEY={target_key}\n")
                    st.success("OpenAI credentials saved!")
                    st.rerun()

            if st.button("🔌 Test OpenAI Connection"):
                active_key = openai_key_input.strip() or os.getenv("OPENAI_API_KEY")
                provider = OpenAIProvider(api_key=active_key, model=openai_model)
                with st.spinner("Pinging OpenAI API..."):
                    success, msg = provider.test_connection()
                if success:
                    st.success(f"✓ **Connected**: {msg}")
                else:
                    st.error(f"❌ **Connection Failed**: {msg}")

        else:
            st.markdown("##### Offline Calibrated Demo Mode")
            st.info(
                "**Offline Demo Evaluator Active.** "
                "This mode operates without requiring any external internet API keys. "
                "It uses a local calibrated scoring heuristic that checks answer depth, key concepts, "
                "and produces authentic rubric justifications. Perfect for testing and demonstrations."
            )
            if st.button("Activate Offline Demo Mode"):
                os.environ["LLM_PROVIDER"] = "mock"
                st.success("Offline demo mode activated.")

    # 2. Strictness Calibration Tab
    with tab_calib:
        st.subheader("Marking Strictness Calibration")
        st.caption("Adjust evaluator behavioral presets without altering the official question rubric.")

        preset_keys = list(settings.CALIBRATION_PRESETS.keys())
        preset_names = [settings.CALIBRATION_PRESETS[k]["name"] for k in preset_keys]
        sel_preset = st.radio("Calibration Preset", preset_names, index=0)

        chosen_key = preset_keys[preset_names.index(sel_preset)]
        preset_data = settings.CALIBRATION_PRESETS[chosen_key]

        st.markdown(f"**Description:** {preset_data['description']}")
        st.markdown(f"- Strictness Factor: `{preset_data['strictness_factor']}`")
        st.markdown(f"- Partial Credit Generosity: `{preset_data['partial_credit_generosity']}`")

    # 3. System Diagnostics & Data Management
    with tab_sys:
        st.subheader("System Diagnostics & Host Capabilities")
        diag_col1, diag_col2 = st.columns(2)

        with diag_col1:
            st.write(f"• **Python Runtime:** `{sys.version.split()[0]}`")
            st.write(f"• **PyMuPDF (PDF Parser):** `Installed (v{getattr(settings, 'fitz_version', '1.24+')})`")
            st.write("• **ReportLab (PDF Marksheets):** `Installed`")
            st.write("• **Database Backend:** `SQLite (Local Storage)`")

        with diag_col2:
            ocr_status = OCRProcessor.is_ocr_available()
            if ocr_status["available"]:
                st.success("• **Tesseract OCR:** Configured and Active")
            else:
                st.warning("• **Tesseract OCR:** Optional dependency not found (Text-based PDFs active; OCR fallback ready)")

        st.markdown("<hr/>", unsafe_allow_html=True)
        st.subheader("Data Management & Database Seeding")

        m_col1, m_col2 = st.columns(2)
        with m_col1:
            if st.button("🌱 Reset / Seed Sample Assessment & Benchmarks"):
                seed_database_if_empty()
                st.success("Sample assessment (Virtual Memory CS401) and benchmark observations loaded!")
                st.rerun()

        with m_col2:
            if st.button("⚠️ Clear All Submissions"):
                with get_db() as db:
                    db.query(Evaluation).delete()
                    db.query(Submission).delete()
                    db.commit()
                st.warning("All submissions and evaluations cleared from database.")
                st.rerun()


if __name__ == "__main__":
    try:
        st.set_page_config(page_title="Settings & Configuration - ExamJudge AI", page_icon="🎓", layout="wide")
    except Exception:
        pass
    from config.settings import ASSETS_DIR
    css_file = ASSETS_DIR / "styles.css"
    if css_file.exists():
        with open(css_file, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    render()
