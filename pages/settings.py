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
    st.markdown('<div class="academic-header"><h1>Settings & AI Setup</h1><p>Configure your AI evaluator connection, select grading strictness, and manage exam data</p></div>', unsafe_allow_html=True)

    tab_api, tab_calib, tab_sys = st.tabs([
        "🔑 AI Provider & Connection",
        "⚙️ Grading Style Preference",
        "🖥️ System Health & Data Tools"
    ])

    # 1. API Configuration Tab
    with tab_api:
        st.subheader("AI Evaluator Backend")
        st.caption("Choose the AI service used for grading. Both Google Gemini and the Offline Demo Evaluator are available.")

        provider_choice = st.selectbox(
            "Evaluation Provider",
            options=["Google Gemini (Recommended)", "OpenAI", "Offline Demo Evaluator (Free & Calibrated)"],
            index=0 if settings.DEFAULT_PROVIDER == "gemini" else (1 if settings.DEFAULT_PROVIDER == "openai" else 2)
        )

        env_file_path = settings.BASE_DIR / ".env"

        if "Gemini" in provider_choice:
            st.markdown("##### Google Gemini Setup")
            st.markdown(
                "Get a free API key from [Google AI Studio](https://aistudio.google.com/). "
                "Enter it below to enable live AI grading."
            )

            current_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
            masked_key = ("*" * (len(current_key) - 4) + current_key[-4:]) if len(current_key) > 4 else ""

            col_k1, col_k2 = st.columns([3, 1])
            with col_k1:
                gemini_key_input = st.text_input(
                    "Google Gemini API Key",
                    value="",
                    type="password",
                    placeholder=f"Current: {masked_key}" if masked_key else "Paste AIzaSy... here"
                )
            with col_k2:
                gemini_model = st.selectbox(
                    "Gemini Model",
                    options=["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
                    index=0
                )

            if st.button("Save Gemini Settings", type="primary"):
                target_key = gemini_key_input.strip() if gemini_key_input.strip() else current_key
                if target_key:
                    os.environ["GEMINI_API_KEY"] = target_key
                    os.environ["LLM_PROVIDER"] = "gemini"
                    os.environ["LLM_MODEL"] = gemini_model
                    # Write to .env
                    with open(env_file_path, "w") as f:
                        f.write(f"LLM_PROVIDER=gemini\nLLM_MODEL={gemini_model}\nGEMINI_API_KEY={target_key}\n")
                    st.success("Gemini API key saved and activated successfully!")
                    st.rerun()
                else:
                    st.warning("Please enter a valid Gemini API key.")

            # Live Test Connection Button
            st.markdown("---")
            st.markdown("##### Test Connection")
            if st.button("🔌 Test Gemini Connection"):
                active_key = gemini_key_input.strip() or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
                provider = GeminiProvider(api_key=active_key, model=gemini_model)
                with st.spinner("Connecting to Google Gemini..."):
                    success, msg = provider.test_connection()
                if success:
                    st.success(f"✓ **Connected**: {msg}")
                else:
                    st.error(f"❌ **Connection Failed**: {msg}")

        elif "OpenAI" in provider_choice:
            st.markdown("##### OpenAI Setup")
            current_open_key = os.getenv("OPENAI_API_KEY") or ""
            masked_open = ("*" * (len(current_open_key) - 4) + current_open_key[-4:]) if len(current_open_key) > 4 else ""

            openai_key_input = st.text_input(
                "OpenAI API Key",
                value="",
                type="password",
                placeholder=f"Current: {masked_open}" if masked_open else "Paste sk-... here"
            )
            openai_model = st.selectbox("OpenAI Model", options=["gpt-4o-mini", "gpt-4o"], index=0)

            if st.button("Save OpenAI Settings", type="primary"):
                target_key = openai_key_input.strip() if openai_key_input.strip() else current_open_key
                if target_key:
                    os.environ["OPENAI_API_KEY"] = target_key
                    os.environ["LLM_PROVIDER"] = "openai"
                    os.environ["LLM_MODEL"] = openai_model
                    with open(env_file_path, "w") as f:
                        f.write(f"LLM_PROVIDER=openai\nLLM_MODEL={openai_model}\nOPENAI_API_KEY={target_key}\n")
                    st.success("OpenAI credentials saved successfully!")
                    st.rerun()

            if st.button("🔌 Test OpenAI Connection"):
                active_key = openai_key_input.strip() or os.getenv("OPENAI_API_KEY")
                provider = OpenAIProvider(api_key=active_key, model=openai_model)
                with st.spinner("Connecting to OpenAI..."):
                    success, msg = provider.test_connection()
                if success:
                    st.success(f"✓ **Connected**: {msg}")
                else:
                    st.error(f"❌ **Connection Failed**: {msg}")

        else:
            st.markdown("##### Offline Demo Evaluator (No API Key Required)")
            st.info(
                "**Offline Demo Evaluator Active.** "
                "This mode runs entirely locally on your machine without requiring any external internet API keys. "
                "It evaluates answer substance, checks required concepts, and generates authentic faculty feedback. "
                "Perfect for testing and faculty demonstrations."
            )
            if st.button("Activate Offline Demo Mode", type="primary"):
                os.environ["LLM_PROVIDER"] = "mock"
                st.success("Offline demo evaluator activated successfully.")

    # 2. Strictness Calibration Tab
    with tab_calib:
        st.subheader("Grading Style Preference")
        st.caption("Adjust how strictly the AI grades descriptive answers to match your department standards.")

        preset_keys = list(settings.CALIBRATION_PRESETS.keys())
        preset_names = [settings.CALIBRATION_PRESETS[k]["name"] for k in preset_keys]
        sel_preset = st.radio("Grading Standard Preset", preset_names, index=0)

        chosen_key = preset_keys[preset_names.index(sel_preset)]
        preset_data = settings.CALIBRATION_PRESETS[chosen_key]

        st.markdown(f"**Policy Description:** {preset_data['description']}")
        st.markdown(f"• **Marking Rigor Factor:** `{preset_data['strictness_factor']}x`")
        st.markdown(f"• **Partial Credit Policy:** `{preset_data['partial_credit_generosity'].capitalize()}`")

    # 3. System Diagnostics & Data Management
    with tab_sys:
        st.subheader("System Health & Installed Libraries")
        diag_col1, diag_col2 = st.columns(2)

        with diag_col1:
            st.write(f"• **Python Engine:** `{sys.version.split()[0]}`")
            st.write(f"• **PDF Reader (PyMuPDF):** `Ready (v{getattr(settings, 'fitz_version', '1.24+')})`")
            st.write("• **Grade Sheet Generator (ReportLab):** `Ready`")
            st.write("• **Database:** `SQLite (Local Storage)`")

        with diag_col2:
            ocr_status = OCRProcessor.is_ocr_available()
            if ocr_status["available"]:
                st.success("• **OCR Reader (Tesseract):** Configured and Active")
            else:
                st.info("• **PDF Text Reader:** Active (Ready for all digital & text-based PDFs)")

        st.markdown("<hr/>", unsafe_allow_html=True)
        st.subheader("Sample Data & Database Tools")

        m_col1, m_col2 = st.columns(2)
        with m_col1:
            if st.button("🌱 Load Sample CS Exam & Benchmark Papers"):
                seed_database_if_empty()
                st.success("Sample exam ('Operating Systems: Virtual Memory') and benchmark papers loaded!")
                st.rerun()

        with m_col2:
            if st.button("⚠️ Clear Student Answer Records"):
                with get_db() as db:
                    db.query(Evaluation).delete()
                    db.query(Submission).delete()
                    db.commit()
                st.warning("All student submissions and graded records have been cleared.")
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
