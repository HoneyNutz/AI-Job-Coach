"""
AI Job Coach - Main Application Entry Point
Modular architecture with separated concerns
"""

import os
import streamlit as st

# Import data models
from agents.data_agent import Resume, JobDescription
from agents.scraper_agent import ScraperAgent
from agents.analysis_agent import AnalysisAgent
from agents.generation_agent import GenerationAgent

# Import UI components
from ui.styles import apply_dark_mode_theme
from ui.navigation import render_top_nav
from ui.components import render_page_header

# Import utilities
from utils.session_state import initialize_session_state

# Import pages
from pages import settings, job_tracker, job_coach

# Configure page settings
st.set_page_config(
    page_title="AI Job Coach",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply styling
apply_dark_mode_theme()

# Initialize session state
initialize_session_state()

# --- Agent Initialization ---
@st.cache_resource
def load_agents(api_key: str, model_name: str):
    """Load and cache AI agents."""
    os.environ["OPENAI_MODEL"] = model_name
    return ScraperAgent(), AnalysisAgent(), GenerationAgent(api_key=api_key)

# Load agents with current configuration
scraper_agent, analysis_agent, generation_agent = load_agents(
    st.session_state.get("openai_api_key"),
    st.session_state.get("preferred_model", "gpt-4o-mini")
)

# --- Navigation ---
render_top_nav()

# --- Page Header ---
render_page_header()

# --- Main Content Routing ---
current_page = st.session_state.get('current_page', 'main_app')
current_step = st.session_state.get('step', 'enter_jd')

if current_page == "job_tracker":
    # Render job tracker page
    job_tracker.render()
    
elif current_step == "settings":
    # Render settings page
    settings.render()
    
else:
    # Job Coach workflow - fully modular!
    job_coach.render(
        scraper_agent=scraper_agent,
        analysis_agent=analysis_agent,
        generation_agent=generation_agent
    )

# --- Footer Info ---
st.markdown("---")
st.caption("🤖 AI Job Coach - Powered by OpenAI | Built with Streamlit")
