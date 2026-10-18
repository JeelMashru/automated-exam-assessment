"""
Automated Descriptive Exam Assessment Engine with LLM-as-a-Judge.
Main Application Entrypoint and Sidebar Router.
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
from pages import (
    dashboard,
    new_assessment,
    results,
    batch_evaluation,
    benchmark,
    reports,
    settings as settings_page,
)

# Page configuration
st.set_page_config(
    page_title="AI Descriptive Exam Assessment Engine",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize database schema and initial data
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


def main():
    # Sidebar Header & Brand
    with st.sidebar:
        st.markdown("""
        <div style="padding: 0.5rem 0; border-bottom: 2px solid #e2e8f0; margin-bottom: 1.25rem;">
            <div style="font-size: 1.3rem; font-weight: 800; color: #1e3a8a; letter-spacing: -0.02em;">
                🎓 ExamJudge AI
            </div>
            <div style="font-size: 0.75rem; color: #64748b; font-weight: 600; text-transform: uppercase; margin-top: 2px;">
                Descriptive Assessment Engine
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Navigation Menu
        nav_options = [
            "1. Dashboard",
            "2. New Assessment",
            "3. Assessment Results",
            "4. Batch Evaluation",
            "5. Benchmark and Validation",
            "6. Reports and Exports",
            "7. Settings and API Configuration",
        ]

        if "nav_selection" not in st.session_state:
            st.session_state["nav_selection"] = nav_options[0]

        selection = st.radio(
            "NAVIGATION",
            nav_options,
            index=nav_options.index(st.session_state["nav_selection"]),
            label_visibility="collapsed"
        )
        st.session_state["nav_selection"] = selection

        st.markdown("---")
        
        # Operational Status Indicator in Sidebar
        from core.llm_client import get_llm_provider
        provider = get_llm_provider()
        p_info = provider.get_provider_info()
        status_color = "#059669" if p_info["configured"] else "#d97706"

        st.markdown(f"""
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 0.75rem; font-size: 0.75rem;">
            <div style="font-weight: 700; color: #1e293b; margin-bottom: 4px;">ENGINE STATUS</div>
            <div style="display: flex; align-items: center; gap: 6px;">
                <span style="height: 8px; width: 8px; background-color: {status_color}; border-radius: 50%; display: inline-block;"></span>
                <span style="font-weight: 600; color: {status_color};">{p_info['mode']}</span>
            </div>
            <div style="color: #64748b; margin-top: 4px;">Model: <code>{p_info['model']}</code></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)
        st.caption("v1.0.0 | Academic Assessment Platform")

    # Page Dispatcher
    if "Dashboard" in selection:
        dashboard.render()
    elif "New Assessment" in selection:
        new_assessment.render()
    elif "Assessment Results" in selection:
        results.render()
    elif "Batch Evaluation" in selection:
        batch_evaluation.render()
    elif "Benchmark and Validation" in selection:
        benchmark.render()
    elif "Reports and Exports" in selection:
        reports.render()
    elif "Settings and API Configuration" in selection:
        settings_page.render()


if __name__ == "__main__":
    main()
