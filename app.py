"""
Automated Descriptive Exam Assessment Engine with LLM-as-a-Judge.
Main Application Entrypoint and Modern Streamlit Navigation Router.
"""

import streamlit as st
import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import ASSETS_DIR
from database.seed_data import seed_database_if_empty

# Page configuration
st.set_page_config(
    page_title="ExamJudge AI - Descriptive Examination Assessment Engine",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize database schema and initial sample data
try:
    seed_database_if_empty()
except Exception as e:
    st.error(f"Database initialization warning: {str(e)}")

# Inject Custom Academic CSS
css_file = ASSETS_DIR / "styles.css"
if css_file.exists():
    with open(css_file, "r") as f:
        custom_css = f.read()
    st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)

# Define native Streamlit multi-page navigation
pages = [
    st.Page("pages/dashboard.py", title="Class Dashboard", icon="📊", default=True),
    st.Page("pages/new_assessment.py", title="Create New Exam", icon="📝"),
    st.Page("pages/results.py", title="Student Results & Review", icon="📋"),
    st.Page("pages/batch_evaluation.py", title="Grade Papers (Batch Upload)", icon="📁"),
    st.Page("pages/benchmark.py", title="Accuracy & Benchmark Tests", icon="📈"),
    st.Page("pages/reports.py", title="Reports & Marksheets", icon="📄"),
    st.Page("pages/settings.py", title="Settings & AI Setup", icon="⚙️"),
]

pg = st.navigation(pages)

# Sidebar Branding & Operational Status
with st.sidebar:
    st.markdown("""
    <div style="padding: 0.25rem 0 0.75rem 0; border-bottom: 2px solid #e2e8f0; margin-bottom: 0.75rem;">
        <div style="font-size: 1.25rem; font-weight: 800; color: #1e3a8a; letter-spacing: -0.02em;">
            🎓 ExamJudge AI
        </div>
        <div style="font-size: 0.75rem; color: #64748b; font-weight: 600; text-transform: uppercase;">
            Faculty Grading Assistant
        </div>
    </div>
    """, unsafe_allow_html=True)

    from core.llm_client import get_llm_provider
    provider = get_llm_provider()
    p_info = provider.get_provider_info()
    status_color = "#059669" if p_info["configured"] else "#d97706"

    st.markdown(f"""
    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 0.75rem; font-size: 0.75rem; margin-top: 1rem;">
        <div style="font-weight: 700; color: #1e293b; margin-bottom: 4px;">AI ASSISTANT STATUS</div>
        <div style="display: flex; align-items: center; gap: 6px;">
            <span style="height: 8px; width: 8px; background-color: {status_color}; border-radius: 50%; display: inline-block;"></span>
            <span style="font-weight: 600; color: {status_color};">{p_info['mode']}</span>
        </div>
        <div style="color: #64748b; margin-top: 4px;">Active Model: <code>{p_info['model']}</code></div>
    </div>
    """, unsafe_allow_html=True)
    st.caption("AI-Assisted Descriptive Exam Assessment")

# Execute the active page
pg.run()
