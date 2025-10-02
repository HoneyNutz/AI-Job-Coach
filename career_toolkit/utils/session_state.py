"""Session state initialization and management."""

import os
import json
import streamlit as st
from agents.data_agent import Resume, JobDescription


USER_ASSETS_DIR = "career_toolkit/user_assets"


def initialize_session_state():
    """Initialize session state variables and load persistent assets."""
    # Load persistent assets if they exist
    if 'assets_loaded' not in st.session_state:
        os.makedirs(USER_ASSETS_DIR, exist_ok=True)
        
        # Load Resume
        resume_path = os.path.join(USER_ASSETS_DIR, "resume.json")
        if os.path.exists(resume_path):
            with open(resume_path, 'r') as f:
                st.session_state.resume = Resume.model_validate_json(f.read())
        else:
            # Fallback to backup resume
            try:
                with open("career_toolkit/backup_resume.json", 'r') as f:
                    st.session_state.resume = Resume.model_validate_json(f.read())
            except (FileNotFoundError, Exception):
                st.session_state.resume = Resume()
        
        # Load Signature
        st.session_state.signature_content = None
        st.session_state.signature_filename = ""
        if os.path.exists(USER_ASSETS_DIR):
            for f in os.listdir(USER_ASSETS_DIR):
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.svg')):
                    sig_path = os.path.join(USER_ASSETS_DIR, f)
                    with open(sig_path, "rb") as file:
                        st.session_state.signature_content = file.read()
                    st.session_state.signature_filename = f
                    break  # Load the first one found
        
        # Load user preferences
        config_path = os.path.join(USER_ASSETS_DIR, "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    st.session_state.preferred_model = config.get('preferred_model', 'gpt-4o-mini')
            except Exception:
                pass
        
        st.session_state.assets_loaded = True

    # Set initial step based on whether assets are present
    if 'step' not in st.session_state:
        has_resume_file = os.path.exists(os.path.join(USER_ASSETS_DIR, "resume.json"))
        has_signature_file = False
        if os.path.exists(USER_ASSETS_DIR):
            for f in os.listdir(USER_ASSETS_DIR):
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".svg")):
                    has_signature_file = True
                    break

        # If either a resume or a signature exists, don't start on Settings
        if has_resume_file or has_signature_file:
            st.session_state.step = "enter_jd"
        else:
            st.session_state.step = "settings"

    # Initialize other session state variables
    if 'job_description' not in st.session_state:
        st.session_state.job_description = JobDescription()
    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = os.getenv("OPENAI_API_KEY", "")
    if 'added_skills' not in st.session_state:
        st.session_state.added_skills = []
    if 'cover_letter' not in st.session_state:
        st.session_state.cover_letter = ""
    if 'recipient_name' not in st.session_state:
        st.session_state.recipient_name = "Hiring Team"
    if 'recipient_title' not in st.session_state:
        st.session_state.recipient_title = "Talent Acquisition"
    if 'company_address' not in st.session_state:
        st.session_state.company_address = ""
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "main_app"  # Default page
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'preferred_model' not in st.session_state:
        st.session_state.preferred_model = "gpt-4o-mini"  # Default to fast model
    if 'show_settings_modal' not in st.session_state:
        st.session_state.show_settings_modal = False
