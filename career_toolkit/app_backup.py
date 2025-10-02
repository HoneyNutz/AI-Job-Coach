import streamlit as st
import os
import shutil
import subprocess
import json
from datetime import datetime
from agents.data_agent import Resume, JobDescription
from agents.scraper_agent import ScraperAgent
from agents.analysis_agent import AnalysisAgent
from agents.generation_agent import GenerationAgent

# Configure page settings for dark mode
st.set_page_config(
    page_title="AI Job Coach",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply modern dark mode CSS
def apply_dark_mode_theme():
    st.markdown("""
    <style>
    /* Import modern font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Root variables for dark theme */
    :root {
        --primary-color: #6366f1;
        --primary-hover: #4f46e5;
        --secondary-color: #10b981;
        --background-dark: #0f172a;
        --background-secondary: #1e293b;
        --background-tertiary: #334155;
        --text-primary: #f8fafc;
        --text-secondary: #cbd5e1;
        --text-muted: #94a3b8;
        --border-color: #475569;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --error-color: #ef4444;
        --info-color: #3b82f6;
    }
    
    /* Main app background */
    .stApp {
        background: linear-gradient(135deg, var(--background-dark) 0%, #1a202c 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Sidebar styling - Fixed visibility with all possible selectors */
    .css-1d391kg, 
    .stSidebar, 
    [data-testid="stSidebar"],
    section[data-testid="stSidebar"],
    .css-1lcbmhc,
    .css-1y4p8pa,
    .stSidebarContent {
        background: var(--background-secondary) !important;
        border-right: 1px solid var(--border-color) !important;
        min-width: 280px !important;
        visibility: visible !important;
        display: block !important;
        opacity: 1 !important;
    }
    
    /* Fix sidebar content positioning to not affect main content */
    .stSidebarContent,
    [data-testid="stSidebarContent"] {
        position: relative !important;
        width: 280px !important;
        flex-shrink: 0 !important;
    }
    
    /* Force sidebar content visibility */
    .css-1d391kg *, 
    .stSidebar *, 
    [data-testid="stSidebar"] *,
    section[data-testid="stSidebar"] *,
    .stSidebarContent * {
        color: var(--text-primary) !important;
        visibility: visible !important;
    }
    
    /* Sidebar headers and text */
    .css-1d391kg .stMarkdown, 
    .stSidebar .stMarkdown,
    [data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] .stMarkdown,
    .stSidebarContent .stMarkdown {
        color: var(--text-primary) !important;
        display: block !important;
    }
    
    /* Mobile-first sidebar */
    @media (max-width: 768px) {
        .css-1d391kg, 
        .stSidebar, 
        [data-testid="stSidebar"],
        section[data-testid="stSidebar"],
        .stSidebarContent {
            min-width: 100% !important;
            position: fixed !important;
            z-index: 999 !important;
            height: 100vh !important;
        }
    }
    
    /* Main content area - ensure proper centering */
    .appview-container .main .block-container,
    .main .block-container,
    section.main > div {
        padding-top: 0 !important;
        padding-bottom: 2rem !important;
        padding-left: 5rem !important;
        padding-right: 5rem !important;
        max-width: 1400px !important;
        margin-left: auto !important;
        margin-right: auto !important;
        background: transparent !important;
    }
    
    /* Ensure main content doesn't get offset by sidebar */
    section.main {
        margin-left: 0 !important;
    }
    
    /* Hide default sidebar */
    section[data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* Responsive padding */
    @media (max-width: 1200px) {
        .main .block-container {
            padding-left: 2rem;
            padding-right: 2rem;
        }
    }
    
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
        font-weight: 600;
        letter-spacing: -0.025em;
    }
    
    h1 {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.5rem !important;
        margin-bottom: 1rem;
    }
    
    /* Text styling */
    .stMarkdown, .stText, p, span, div {
        color: var(--text-secondary) !important;
        line-height: 1.6;
    }
    
    /* Containers and cards */
    .stContainer > div {
        background: var(--background-secondary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        font-family: 'Inter', sans-serif;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 2px 4px rgba(99, 102, 241, 0.2);
        cursor: pointer;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(99, 102, 241, 0.4);
        background: linear-gradient(135deg, var(--primary-hover), var(--primary-color));
    }
    
    .stButton > button:active {
        transform: translateY(0);
        box-shadow: 0 2px 4px rgba(99, 102, 241, 0.2);
    }
    
    /* Primary button styling */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--secondary-color), #059669);
        box-shadow: 0 2px 4px rgba(16, 185, 129, 0.2);
    }
    
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(16, 185, 129, 0.4);
    }
    
    .stButton > button[kind="primary"]:active {
        transform: translateY(0);
        box-shadow: 0 2px 4px rgba(16, 185, 129, 0.2);
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        background: var(--background-tertiary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2) !important;
    }
    
    /* Metrics */
    .metric-container {
        background: var(--background-secondary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
    
    [data-testid="metric-container"] {
        background: var(--background-secondary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    [data-testid="metric-container"] > div {
        color: var(--text-primary) !important;
    }
    
    /* Progress bars - Dynamic color based on score */
    .stProgress > div > div > div {
        border-radius: 4px;
    }
    
    /* Low score progress bars (0-30%) - Red */
    .stProgress[data-score="low"] > div > div > div,
    .progress-low > div > div > div {
        background: linear-gradient(90deg, #ef4444, #dc2626) !important;
    }
    
    /* Medium score progress bars (31-70%) - Yellow/Orange */
    .stProgress[data-score="medium"] > div > div > div,
    .progress-medium > div > div > div {
        background: linear-gradient(90deg, #f59e0b, #d97706) !important;
    }
    
    /* High score progress bars (71-100%) - Green */
    .stProgress[data-score="high"] > div > div > div,
    .progress-high > div > div > div {
        background: linear-gradient(90deg, #10b981, #059669) !important;
    }
    
    /* Default progress bar styling */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--error-color), var(--warning-color)) !important;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background: var(--background-tertiary) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
        border: 1px solid var(--border-color) !important;
        transition: all 0.2s ease !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: var(--background-secondary) !important;
        border-color: var(--primary-color) !important;
    }
    
    .streamlit-expanderContent {
        background: var(--background-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 0 0 8px 8px !important;
        animation: slideDown 0.3s ease-out;
    }
    
    @keyframes slideDown {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Sidebar elements - Enhanced visibility with all selectors */
    .css-1d391kg .stRadio > label, 
    .stSidebar .stRadio > label,
    [data-testid="stSidebar"] .stRadio > label,
    section[data-testid="stSidebar"] .stRadio > label {
        color: var(--text-primary) !important;
        font-weight: 500 !important;
        font-size: 1rem !important;
        display: block !important;
        visibility: visible !important;
    }
    
    .css-1d391kg .stTextInput > label,
    .stSidebar .stTextInput > label,
    [data-testid="stSidebar"] .stTextInput > label,
    section[data-testid="stSidebar"] .stTextInput > label {
        color: var(--text-primary) !important;
        font-weight: 500 !important;
        display: block !important;
        visibility: visible !important;
    }
    
    /* Sidebar radio buttons */
    .css-1d391kg .stRadio > div,
    .stSidebar .stRadio > div,
    [data-testid="stSidebar"] .stRadio > div,
    section[data-testid="stSidebar"] .stRadio > div {
        background: var(--background-tertiary) !important;
        border-radius: 8px !important;
        padding: 0.5rem !important;
        margin: 0.25rem 0 !important;
        display: block !important;
        visibility: visible !important;
    }
    
    /* Sidebar headers */
    .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3,
    .stSidebar h1, .stSidebar h2, .stSidebar h3,
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        margin-bottom: 1rem !important;
        display: block !important;
        visibility: visible !important;
    }
    
    /* Sidebar buttons */
    .css-1d391kg .stButton > button,
    .stSidebar .stButton > button,
    [data-testid="stSidebar"] .stButton > button,
    section[data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        margin: 0.5rem 0 !important;
        background: linear-gradient(135deg, var(--primary-color), var(--primary-hover)) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        display: block !important;
        visibility: visible !important;
    }
    
    .css-1d391kg .stButton > button:hover,
    .stSidebar .stButton > button:hover,
    [data-testid="stSidebar"] .stButton > button:hover,
    section[data-testid="stSidebar"] .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(99, 102, 241, 0.3) !important;
    }
    
    /* Status indicators */
    .status-not-applied { color: var(--info-color) !important; }
    .status-applied { color: var(--warning-color) !important; }
    .status-interviewing { color: #f97316 !important; }
    .status-offer { color: var(--success-color) !important; }
    .status-accepted { color: var(--success-color) !important; }
    .status-closed { color: var(--error-color) !important; }
    
    /* Alerts and notifications */
    .stAlert {
        border-radius: 8px;
        border: none;
        backdrop-filter: blur(10px);
        animation: slideIn 0.3s ease-out;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    .stSuccess {
        background: rgba(16, 185, 129, 0.1) !important;
        border: 1px solid var(--success-color) !important;
        color: var(--success-color) !important;
        border-left: 4px solid var(--success-color) !important;
    }
    
    .stError {
        background: rgba(239, 68, 68, 0.1) !important;
        border: 1px solid var(--error-color) !important;
        color: var(--error-color) !important;
        border-left: 4px solid var(--error-color) !important;
    }
    
    .stWarning {
        background: rgba(245, 158, 11, 0.1) !important;
        border: 1px solid var(--warning-color) !important;
        color: var(--warning-color) !important;
        border-left: 4px solid var(--warning-color) !important;
    }
    
    .stInfo {
        background: rgba(59, 130, 246, 0.1) !important;
        border: 1px solid var(--info-color) !important;
        color: var(--info-color) !important;
        border-left: 4px solid var(--info-color) !important;
    }
    
    /* File uploader */
    .stFileUploader > div {
        background: var(--background-tertiary) !important;
        border: 2px dashed var(--border-color) !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    
    .stFileUploader > div:hover {
        border-color: var(--primary-color) !important;
        background: rgba(99, 102, 241, 0.05) !important;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: var(--primary-color) !important;
    }
    
    /* Loading animation */
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
    }
    
    .stSpinner {
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    /* Tables */
    .stDataFrame {
        background: var(--background-secondary) !important;
        border-radius: 8px !important;
        overflow: hidden;
    }
    
    /* Custom job tracker cards */
    .job-card {
        background: var(--background-secondary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        transition: all 0.2s ease;
    }
    
    .job-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 12px -1px rgba(0, 0, 0, 0.4);
        border-color: var(--primary-color);
    }
    
    .employer-name {
        color: var(--primary-color) !important;
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        margin-bottom: 0.5rem !important;
    }
    
    .job-title {
        color: var(--text-primary) !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        margin-bottom: 1rem !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {visibility: hidden;}
    
    /* Top Navigation Bar Styling */
    .nav-bar-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0 2rem;
        margin: 0 -5rem 2rem -5rem !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        position: sticky;
        top: 0;
        z-index: 1000;
    }
    
    /* Navigation container layout */
    .nav-bar-container > div {
        max-width: 1400px;
        margin: 0 auto;
        display: flex;
        align-items: center;
        justify-content: space-between;
        height: 70px;
    }
    
    /* Override default column styling in nav */
    .nav-bar-container [data-testid="column"] {
        padding: 0 !important;
        flex: 0 0 auto !important;
    }
    
    /* Logo column takes less space */
    .nav-bar-container [data-testid="column"]:first-child {
        flex: 0 0 auto !important;
        margin-right: auto !important;
    }
    
    /* Logo styling */
    .nav-logo {
        color: white;
        font-size: 1.5rem;
        font-weight: bold;
        transition: transform 0.3s ease;
        cursor: default;
    }
    
    .nav-logo:hover {
        transform: scale(1.05);
    }
    
    /* Navigation links container - add gap between items */
    .nav-bar-container [data-testid="column"]:not(:first-child):not(:nth-child(2)) {
        margin-left: 1rem !important;
    }
    
    /* Style navigation buttons to look like nav links */
    .nav-bar-container .stButton button {
        background: transparent !important;
        color: white !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
        border-radius: 8px !important;
        box-shadow: none !important;
        position: relative !important;
        height: auto !important;
    }
    
    /* Hover effect with background */
    .nav-bar-container .stButton button:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        transform: none !important;
        box-shadow: none !important;
    }
    
    /* Underline animation on hover - simulated with border */
    .nav-bar-container .stButton button:hover::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        width: 80%;
        height: 2px;
        background: white;
        transform: translateX(-50%);
        transition: all 0.3s ease;
    }
    
    /* Active/selected state */
    .nav-bar-container .stButton button:active,
    .nav-bar-container .stButton button:focus {
        background: rgba(255, 255, 255, 0.15) !important;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--background-dark);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--border-color);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-muted);
    }
    
    /* Mobile navigation improvements */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        
        /* Ensure sidebar toggle is visible on mobile */
        [data-testid="collapsedControl"] {
            background: var(--primary-color) !important;
            color: white !important;
            border-radius: 50% !important;
            width: 3rem !important;
            height: 3rem !important;
            position: fixed !important;
            top: 1rem !important;
            left: 1rem !important;
            z-index: 1000 !important;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3) !important;
        }
        
        [data-testid="collapsedControl"]:hover {
            background: var(--primary-hover) !important;
            transform: scale(1.1) !important;
        }
    }
    
    /* Navigation status indicator */
    .nav-indicator {
        position: fixed;
        top: 1rem;
        right: 1rem;
        background: var(--background-secondary);
        color: var(--text-primary);
        padding: 0.5rem 1rem;
        border-radius: 20px;
        border: 1px solid var(--border-color);
        font-size: 0.8rem;
        z-index: 999;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    @media (min-width: 769px) {
        .nav-indicator {
            display: none;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Apply the theme
apply_dark_mode_theme()

# --- Agent Initialization ---
@st.cache_resource
def load_agents(api_key: str, model_name: str):
    # Set environment variable for model selection
    os.environ["OPENAI_MODEL"] = model_name
    return ScraperAgent(), AnalysisAgent(), GenerationAgent(api_key=api_key)

scraper_agent, analysis_agent, generation_agent = load_agents(
    st.session_state.get("openai_api_key"),
    st.session_state.get("preferred_model", "gpt-4o-mini")
)

# --- App State Management ---
USER_ASSETS_DIR = "career_toolkit/user_assets"

def initialize_session_state():
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
                    break # Load the first one found
        
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
        # Determine if a signature image exists in user assets
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
        st.session_state.current_page = "main_app" # Default page
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'preferred_model' not in st.session_state:
        st.session_state.preferred_model = "gpt-4o-mini"  # Default to fast model
    if 'show_settings_modal' not in st.session_state:
        st.session_state.show_settings_modal = False


# --- UI Rendering Functions ---
def render_settings():
    """Settings page."""
    # Add tabs for better organization
    tab1, tab2, tab3, tab4 = st.tabs(["🤖 AI Model", "🔑 API Key", "📄 Resume", "✍️ Signature"])
    
    with tab1:
        render_model_settings()
    
    with tab2:
        render_api_key_settings()
    
    with tab3:
        render_resume_settings()
    
    with tab4:
        render_signature_settings()

def render_model_settings():
    """Render AI model selection settings."""
    model_options = {
        "gpt-4o-mini": "GPT-4o Mini (Fast & Cost-Effective)",
        "gpt-5": "GPT-5 (Advanced Reasoning)"
    }
    
    # Create two columns for model cards
    col1, col2 = st.columns(2)
    
    with col1:
        is_mini_selected = st.session_state.preferred_model == "gpt-4o-mini"
        border_color = "var(--primary-color)" if is_mini_selected else "var(--border-color)"
        bg_color = "rgba(99, 102, 241, 0.1)" if is_mini_selected else "var(--background-secondary)"
        
        st.markdown(f'<div style="background: {bg_color}; padding: 1.5rem; border-radius: 10px; border: 2px solid {border_color}; height: 100%; cursor: pointer;"><div style="font-size: 1.2rem; color: var(--text-primary); font-weight: 600; margin-bottom: 0.5rem;">⚡ GPT-4o Mini</div><div style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.5; margin-bottom: 1rem;">Fast and cost-effective model ideal for most tasks. 3x faster and 10x cheaper than premium models.</div><div style="color: var(--success-color); font-weight: 500;">✓ Recommended for daily use</div><div style="color: var(--text-muted); font-size: 0.85rem; margin-top: 0.5rem;">Best for: Resume optimization, keyword analysis, cover letters</div></div>', unsafe_allow_html=True)
        
        if st.button("Select GPT-4o Mini", key="select_mini_modal", use_container_width=True, type="primary" if is_mini_selected else "secondary"):
            st.session_state.preferred_model = "gpt-4o-mini"
            # Save preference to config file
            config_path = os.path.join(USER_ASSETS_DIR, "config.json")
            with open(config_path, 'w') as f:
                json.dump({"preferred_model": "gpt-4o-mini"}, f)
            # Clear cache to reload agents with new model
            st.cache_resource.clear()
            st.success("✓ Model updated to GPT-4o Mini")
    
    with col2:
        is_gpt5_selected = st.session_state.preferred_model == "gpt-5"
        border_color = "var(--primary-color)" if is_gpt5_selected else "var(--border-color)"
        bg_color = "rgba(99, 102, 241, 0.1)" if is_gpt5_selected else "var(--background-secondary)"
        
        st.markdown(f'<div style="background: {bg_color}; padding: 1.5rem; border-radius: 10px; border: 2px solid {border_color}; height: 100%; cursor: pointer;"><div style="font-size: 1.2rem; color: var(--text-primary); font-weight: 600; margin-bottom: 0.5rem;">🧠 GPT-5</div><div style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.5; margin-bottom: 1rem;">Advanced reasoning model with superior analysis capabilities. Best for complex career decisions.</div><div style="color: var(--warning-color); font-weight: 500;">⚠ Premium pricing</div><div style="color: var(--text-muted); font-size: 0.85rem; margin-top: 0.5rem;">Best for: Complex analysis, strategic career planning</div></div>', unsafe_allow_html=True)
        
        if st.button("Select GPT-5", key="select_gpt5_modal", use_container_width=True, type="primary" if is_gpt5_selected else "secondary"):
            st.session_state.preferred_model = "gpt-5"
            # Save preference to config file
            config_path = os.path.join(USER_ASSETS_DIR, "config.json")
            with open(config_path, 'w') as f:
                json.dump({"preferred_model": "gpt-5"}, f)
            # Clear cache to reload agents with new model
            st.cache_resource.clear()
            st.success("✓ Model updated to GPT-5")
    
    # Show current selection
    current_model_display = model_options[st.session_state.preferred_model]
    st.info(f"🤖 **Current Model:** {current_model_display}")

def render_api_key_settings():
    """Render API key configuration."""
    st.markdown("### Configure your OpenAI API Key")
    
    new_api_key = st.text_input(
        "OpenAI API Key", 
        type="password", 
        value=st.session_state.openai_api_key,
        key="api_key_input_modal",
        help="Enter your OpenAI API key to enable AI features"
    )
    
    if new_api_key != st.session_state.openai_api_key:
        st.session_state.openai_api_key = new_api_key
        # Clear cache to reload agents with new API key
        st.cache_resource.clear()
        if new_api_key:
            st.success("✓ API Key updated successfully")
        else:
            st.warning("⚠ API Key cleared")
    
    if not st.session_state.openai_api_key:
        st.error("❌ OpenAI API Key is required for all AI features.")
    else:
        st.success("✓ API Key is configured")
    
    st.info("💡 **Tip:** You can get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)")

def render_resume_settings():
    """Render resume upload settings."""
    resume_uploader = st.file_uploader("Upload your JSON Resume", type="json", key="resume_uploader_modal")
    if resume_uploader is not None:
        try:
            resume_content = resume_uploader.read().decode('utf-8')
            # Save to session state
            st.session_state.resume = Resume.model_validate_json(resume_content)
            # Save persistently
            with open(os.path.join(USER_ASSETS_DIR, "resume.json"), "w") as f:
                f.write(resume_content)
            st.success("✓ Resume updated and saved successfully!")
        except Exception as e:
            st.error(f"❌ Invalid resume format: {e}")
    
    with st.expander("📄 View Current Resume", expanded=False):
        st.json(st.session_state.resume.model_dump_json(indent=2, exclude_none=True))

def render_signature_settings():
    """Render signature upload settings."""
    signature_uploader = st.file_uploader("Upload your signature image (PNG, JPG, SVG)", type=["png", "jpg", "jpeg", "svg"], key="signature_uploader_modal")
    if signature_uploader is not None:
        # Clear any old signature files first
        if os.path.exists(USER_ASSETS_DIR):
            for f in os.listdir(USER_ASSETS_DIR):
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.svg')):
                    os.remove(os.path.join(USER_ASSETS_DIR, f))

        # Save new signature with its original name
        st.session_state.signature_content = signature_uploader.read()
        st.session_state.signature_filename = signature_uploader.name
        with open(os.path.join(USER_ASSETS_DIR, signature_uploader.name), "wb") as f:
            f.write(st.session_state.signature_content)
        st.success(f"✓ Signature '{signature_uploader.name}' uploaded and saved!")
    
    if st.session_state.signature_content:
        st.markdown("**Current Signature:**")
        st.image(st.session_state.signature_content, width=300)
    else:
        st.info("💡 No custom signature loaded. The cover letter will have a blank space for a signature.")


def render_update_resume():
    st.header("📄 Update Your Resume")
    if st.button("← Back to Welcome"):
        st.session_state.step = "welcome"
        st.rerun()
    uploaded_file = st.file_uploader("Upload your JSON Resume", type="json")
    if uploaded_file is not None:
        try:
            resume_content = uploaded_file.read().decode('utf-8')
            st.session_state.resume = Resume.model_validate_json(resume_content)
            st.success("Resume updated successfully!")
            st.session_state.step = "enter_jd"
            st.rerun()
        except Exception as e:
            st.error(f"Invalid resume format: {e}")

def render_enter_jd():
    # Helpful instructions
    st.markdown("""
    <div style="background: rgba(99, 102, 241, 0.1); padding: 1rem; border-radius: 8px; border-left: 4px solid var(--primary-color); margin-bottom: 1.5rem;">
        <p style="margin: 0; color: var(--text-secondary);">
            <strong>💡 Quick Tip:</strong> Copy the entire job posting including company info, responsibilities, qualifications, and benefits for the best analysis.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    jd_link = st.text_input(
        "🔗 Job Posting URL (Optional)", 
        placeholder="https://company.com/careers/job-id",
        help="Paste the link to the original job posting for reference"
    )
    
    jd_text = st.text_area(
        "📄 Job Description Content", 
        height=300,
        placeholder="Paste the complete job description here...\n\nInclude:\n• Job title and company name\n• Role description\n• Required skills and qualifications\n• Responsibilities\n• Benefits and perks",
        help="Copy and paste the full job description text"
    )
    
    # Character count
    if jd_text:
        char_count = len(jd_text)
        word_count = len(jd_text.split())
        st.caption(f"📊 {char_count:,} characters • {word_count:,} words")

    col1, col2 = st.columns([3, 1])
    with col1:
        process_button = st.button("🚀 Analyze Job Description", type="primary", use_container_width=True)
    with col2:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = "welcome"
            st.rerun()
    
    if process_button:
        if not jd_text:
            st.warning("Please paste the job description content.")
            return
        if not st.session_state.openai_api_key:
            st.error("OpenAI API Key is required. Please set it in the sidebar.")
            return
        
        with st.spinner("🔍 Analyzing job description with AI..."):
            # Reset blueprint state for the new job
            if 'blueprint_generated' in st.session_state:
                st.session_state.blueprint_generated = False
            if 'blueprint_parts' in st.session_state:
                st.session_state.blueprint_parts = {}

            extracted_data = generation_agent.extract_job_details(jd_text)
            
            # Check for inferred skills
            original_skills = set(s.strip() for s in (extracted_data.get('skills') or "").split(',') if s.strip())
            inferred_skills_data = generation_agent.infer_skills(jd_text)
            inferred_skills = set(s.strip() for s in (inferred_skills_data.get('skills') or "").split(',') if s.strip())
            all_skills = original_skills.union(inferred_skills)
            st.session_state.added_skills = list(inferred_skills - original_skills)
            extracted_data['skills'] = ", ".join(all_skills)
            
            # Preserve full original JD text separately if provided by generator
            if 'originalText' in extracted_data:
                st.session_state.job_description_full_text = extracted_data.get('originalText')
                # Remove from dict to avoid validation issues if model forbids extras
                extracted_data.pop('originalText', None)

            if jd_link:
                extracted_data['url'] = jd_link
            st.session_state.job_description = JobDescription(**extracted_data)
            st.session_state.step = "jd_processed"
            st.rerun()

def render_jd_processed():
    
    jd = st.session_state.job_description
    
    # Main job header card
    st.markdown(f'<div style="background: linear-gradient(135deg, var(--primary-color), var(--primary-hover)); padding: 2rem; border-radius: 12px; margin-bottom: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.3);"><h2 style="color: white; margin: 0 0 0.5rem 0; font-size: 1.8rem;">{jd.name or "Job Title"}</h2><p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 1.2rem; font-weight: 500;">📍 {jd.hiringOrganization or "Company Name"}</p></div>', unsafe_allow_html=True)
    
    # Key details in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f'<div style="background: var(--background-secondary); padding: 1.5rem; border-radius: 10px; border: 1px solid var(--border-color); height: 100%;"><div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.5rem;">📍 LOCATION</div><div style="font-size: 1.1rem; color: var(--text-primary); font-weight: 500;">{jd.jobLocation or "Not specified"}</div></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'<div style="background: var(--background-secondary); padding: 1.5rem; border-radius: 10px; border: 1px solid var(--border-color); height: 100%;"><div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.5rem;">💼 EMPLOYMENT TYPE</div><div style="font-size: 1.1rem; color: var(--text-primary); font-weight: 500;">{jd.employmentType or "Not specified"}</div></div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'<div style="background: var(--background-secondary); padding: 1.5rem; border-radius: 10px; border: 1px solid var(--border-color); height: 100%;"><div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.5rem;">📅 DATE POSTED</div><div style="font-size: 1.1rem; color: var(--text-primary); font-weight: 500;">{jd.datePosted or "Not specified"}</div></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Company description
    if jd.description:
        with st.expander("🏢 About the Company", expanded=True):
            st.markdown(f'<div style="color: var(--text-secondary); line-height: 1.6;">{jd.description}</div>', unsafe_allow_html=True)
    
    # Skills section with enhanced styling
    if jd.skills:
        with st.expander("🎯 Required Skills & Technologies", expanded=True):
            skills_list = [s.strip() for s in jd.skills.split(',') if s.strip()]
            
            # Highlight inferred skills
            inferred_set = set(st.session_state.added_skills) if st.session_state.added_skills else set()
            
            skills_html = '<div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 1rem;">'
            for skill in skills_list:
                if skill in inferred_set:
                    # Inferred skills - different color
                    skills_html += f'<span style="background: linear-gradient(135deg, #8b5cf6, #6366f1); color: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem; font-weight: 500; box-shadow: 0 2px 4px rgba(139,92,246,0.3);">{skill} ✨</span>'
                else:
                    # Regular skills
                    skills_html += f'<span style="background: var(--background-tertiary); color: var(--text-primary); padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem; border: 1px solid var(--border-color);">{skill}</span>'
            skills_html += '</div>'
            
            st.markdown(skills_html, unsafe_allow_html=True)
            
            if st.session_state.added_skills:
                st.info(f"✨ **AI-Inferred Skills:** I've identified {len(st.session_state.added_skills)} additional skills that weren't explicitly listed but are relevant to this role.")
    
    # Responsibilities
    if jd.responsibilities:
        with st.expander("📋 Key Responsibilities", expanded=False):
            for i, resp in enumerate(jd.responsibilities, 1):
                st.markdown(f'<div style="margin-bottom: 0.75rem; padding-left: 1rem; border-left: 3px solid var(--primary-color);"><span style="color: var(--primary-color); font-weight: 600;">{i}.</span> <span style="color: var(--text-secondary);">{resp}</span></div>', unsafe_allow_html=True)
    
    # Qualifications
    if jd.qualifications:
        with st.expander("✅ Required Qualifications", expanded=False):
            for i, qual in enumerate(jd.qualifications, 1):
                st.markdown(f'<div style="margin-bottom: 0.75rem; padding-left: 1rem; border-left: 3px solid var(--secondary-color);"><span style="color: var(--secondary-color); font-weight: 600;">{i}.</span> <span style="color: var(--text-secondary);">{qual}</span></div>', unsafe_allow_html=True)
    
    # Experience requirements
    if jd.experienceRequirements:
        with st.expander("💼 Experience Requirements", expanded=False):
            for i, exp in enumerate(jd.experienceRequirements, 1):
                st.markdown(f'<div style="margin-bottom: 0.75rem; padding-left: 1rem; border-left: 3px solid var(--info-color);"><span style="color: var(--info-color); font-weight: 600;">{i}.</span> <span style="color: var(--text-secondary);">{exp}</span></div>', unsafe_allow_html=True)
    
    # Education requirements
    if jd.educationRequirements:
        with st.expander("🎓 Education Requirements", expanded=False):
            for i, edu in enumerate(jd.educationRequirements, 1):
                st.markdown(f'<div style="margin-bottom: 0.75rem; padding-left: 1rem; border-left: 3px solid var(--warning-color);"><span style="color: var(--warning-color); font-weight: 600;">{i}.</span> <span style="color: var(--text-secondary);">{edu}</span></div>', unsafe_allow_html=True)
    
    # Benefits
    if jd.jobBenefits:
        with st.expander("🎁 Benefits & Perks", expanded=False):
            st.markdown(f'<div style="color: var(--text-secondary); line-height: 1.6;">{jd.jobBenefits}</div>', unsafe_allow_html=True)
    
    # Job URL if available
    if jd.url:
        st.markdown(f'<div style="margin-top: 1.5rem; padding: 1rem; background: var(--background-secondary); border-radius: 8px; border: 1px solid var(--border-color);"><span style="color: var(--text-muted);">🔗 Job Posting:</span> <a href="{jd.url}" target="_blank" style="color: var(--primary-color); text-decoration: none; font-weight: 500;">{jd.url}</a></div>', unsafe_allow_html=True)
    
    # Developer view - collapsed by default
    with st.expander("🔧 Developer View (Raw JSON)", expanded=False):
        st.json(jd.model_dump_json(indent=2, exclude_none=True))
    
    st.markdown("---")
    
    # Action buttons
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("🚀 Analyze Resume & Generate Documents", type="primary", use_container_width=True):
            st.session_state.step = "skill_gap"
            st.rerun()
    with col2:
        if st.button("← Edit Job Details", use_container_width=True):
            st.session_state.step = "enter_jd"
            st.rerun()


def render_blueprint_content():
    """Renders the interactive blueprint UI from data in session state."""
    resume = st.session_state.resume
    assessment = st.session_state.blueprint_parts.get('assessment', {})
    keywords = st.session_state.blueprint_parts.get('keyword_table', [])

    st.subheader("1. Strategic Assessment")
    if st.button("Rerun Strategic Assessment", key="rerun_assessment"):
        with st.spinner("Re-running strategic assessment..."):
            st.session_state.blueprint_parts['assessment'] = generation_agent.blueprint_step_1_strategic_assessment(resume, st.session_state.job_description)
            st.success("Strategic assessment updated.")
            st.rerun()
    if 'error' not in assessment:
        st.markdown(f"* **Position Alignment Score:** {assessment.get('alignment_score', 'N/A')}")
        st.markdown(f"* **Overall Fitness:** {assessment.get('overall_fitness', 'N/A')}")
        st.markdown("* **Key Opportunity Areas:**")
        for opp in assessment.get('key_opportunities', []):
            st.markdown(f"  * {opp}")
    else:
        st.error(assessment.get('error', 'Failed to generate assessment.'))
    st.divider()

    st.subheader("2. Content & Keyword Enhancements")
    st.markdown("### Semantic Skill Analysis")
    if st.button("Rerun Semantic Keyword Analysis", key="rerun_keywords"):
        with st.spinner("Re-running semantic keyword analysis..."):
            st.session_state.blueprint_parts['keyword_table'] = generation_agent.blueprint_step_2_semantic_keyword_analysis(resume, st.session_state.job_description)
            st.success("Semantic keyword analysis updated.")
            st.rerun()
    if isinstance(keywords, list):
        # Enhanced semantic skill analysis display
        for i, item in enumerate(keywords):
            with st.container():
                # Main skill information
                col1, col2, col3 = st.columns([3, 1, 1])
                
                # Skill name with semantic match info
                status_icon = "✅" if item.get('found') else "❌"
                similarity_score = item.get('similarity_score', 0)
                matched_skill = item.get('matched_skill', 'None')
                
                with col1:
                    st.markdown(f"**{status_icon} {item.get('keyword')}**")
                    if matched_skill and matched_skill != 'None':
                        st.caption(f"🔗 Matched with: **{matched_skill}** (similarity: {similarity_score:.2f})")
                    else:
                        st.caption("❗ No semantic match found in resume")
                
                # Priority with enhanced color coding
                priority = item.get('priority', 'N/A')
                priority_colors = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
                priority_color = priority_colors.get(priority, "⚪")
                with col2:
                    st.markdown(f"{priority_color} **{priority}**")
                    st.caption("Priority")
                
                # Semantic similarity score with color coding
                confidence = item.get('confidence', 0)
                with col3:
                    # Determine color class based on score
                    if confidence >= 70:
                        color_class = "progress-high"
                        color_text = "🟢"
                    elif confidence >= 30:
                        color_class = "progress-medium"
                        color_text = "🟡"
                    else:
                        color_class = "progress-low"
                        color_text = "🔴"
                    
                    # Create colored progress bar
                    st.markdown(f'<div class="{color_class}">', unsafe_allow_html=True)
                    st.progress(confidence / 100)
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.caption(f"{color_text} {confidence}% Match")
                
                # Context and action information
                context = item.get('context', '')
                source = item.get('source', '')
                action = item.get('action', 'No action specified')
                
                if context and context != '':
                    st.caption(f"📍 **Context:** {context}")
                if source and source != '':
                    st.caption(f"🎯 **Source:** {source.title()}")
                
                # Action recommendation
                st.info(f"💡 **Recommendation:** {action}")
                
                # Add separator between items
                if i < len(keywords) - 1:
                    st.markdown("---")
    else:
        st.error(keywords.get('error', 'Failed to generate keyword table.'))
    st.divider()

    st.markdown("### Recommended Professional Summary")
    if st.button("Regenerate Summary", key="rerun_summary"):
        with st.spinner("Re-generating professional summary..."):
            st.session_state.blueprint_parts['editable_summary'] = generation_agent.blueprint_step_3_summary(resume, st.session_state.job_description)
            st.success("Summary updated.")
            st.rerun()
    edited_summary = st.text_area("Edit the AI-generated summary below:", value=st.session_state.blueprint_parts.get('editable_summary', ''), height=150, key="editable_summary_area")
    if st.button("Update Resume Summary"):
        st.session_state.resume.basics.summary = edited_summary
        st.success("Professional summary updated in the resume editor below!")
        st.rerun()
    st.divider()

    st.markdown("### Achievement-Driven Bullet Points")
    if st.button("Rerun Achievement Suggestions", key="rerun_achievements"):
        with st.spinner("Re-running achievement suggestions..."):
            st.session_state.blueprint_parts['achievements'] = {}
            for i, work_item in enumerate(resume.work):
                if work_item.highlights:
                    for j, highlight in enumerate(work_item.highlights):
                        unique_key = f"{i}_{j}"
                        result = generation_agent.blueprint_step_4_achievements(highlight, work_item.name, st.session_state.job_description)
                        if 'error' not in result:
                            st.session_state.blueprint_parts['achievements'][unique_key] = result
            st.success("Achievement suggestions updated.")
            st.rerun()
    for key, result in st.session_state.blueprint_parts.get('achievements', {}).items():
        try:
            work_idx, highlight_idx = map(int, key.split('_'))
            if work_idx >= len(st.session_state.resume.work) or highlight_idx >= len(st.session_state.resume.work[work_idx].highlights):
                continue

            st.markdown(f"**For your role at {st.session_state.resume.work[work_idx].name}:**")
            st.markdown(f"* **Original:** {result['original_bullet']}")
            
            edited_bullet = st.text_area(
                "Edit the AI-optimized bullet point:", 
                value=result['optimized_bullet'], 
                key=f"editable_bullet_{key}",
                height=100
            )
            st.caption(f"**Rationale:** {result['rationale']}")

            if st.button("Apply this suggestion", key=f"apply_{key}"):
                if st.session_state.resume.work[work_idx].highlights[highlight_idx] == result['original_bullet']:
                    st.session_state.resume.work[work_idx].highlights[highlight_idx] = edited_bullet
                    st.success("Suggestion applied! The resume editor below has been updated.")
                    del st.session_state.blueprint_parts['achievements'][key]
                    st.rerun()
                else:
                    st.warning("The original bullet point seems to have changed. Cannot apply suggestion automatically.")
            st.divider()
        except (ValueError, IndexError):
            continue

def render_skill_gap():
    if st.button("← Back to Job Details"):
        st.session_state.step = "jd_processed"
        st.rerun()

    # --- Initial, Fast Analysis --- 
    if not st.session_state.analysis_results or st.session_state.analysis_results.get('resume_hash') != hash(st.session_state.resume.model_dump_json()):
        with st.spinner("Comparing your resume to the job description..."):
            st.session_state.analysis_results = analysis_agent.analyze(st.session_state.resume, st.session_state.job_description)
            st.session_state.analysis_results['resume_hash'] = hash(st.session_state.resume.model_dump_json())
    
    st.metric("Overall Resume Match Score", st.session_state.analysis_results.get('overall_score', 'N/A'))
    st.markdown("--- ")
    st.markdown("### AI-Powered Resume Blueprint")

    # --- One-Time Blueprint Generation --- 
    if not st.session_state.get('blueprint_generated'):
        with st.status("Generating your strategic resume blueprint...", expanded=True) as status:
            st.session_state.blueprint_parts = {} # Initialize/reset
            resume = st.session_state.resume
            jd = st.session_state.job_description

            status.write("Step 1/4: Performing strategic assessment...")
            st.session_state.blueprint_parts['assessment'] = generation_agent.blueprint_step_1_strategic_assessment(resume, jd)

            status.write("Step 2/4: Performing semantic skill analysis...")
            st.session_state.blueprint_parts['keyword_table'] = generation_agent.blueprint_step_2_semantic_keyword_analysis(resume, jd)

            status.write("Step 3/4: Rewriting professional summary...")
            st.session_state.blueprint_parts['editable_summary'] = generation_agent.blueprint_step_3_summary(resume, jd)

            status.write("Step 4/4: Rewriting achievement bullet points...")
            st.session_state.blueprint_parts['achievements'] = {}
            for i, work_item in enumerate(resume.work):
                if work_item.highlights:
                    for j, highlight in enumerate(work_item.highlights):
                        unique_key = f"{i}_{j}"
                        result = generation_agent.blueprint_step_4_achievements(highlight, work_item.name, jd)
                        if 'error' not in result:
                            st.session_state.blueprint_parts['achievements'][unique_key] = result
            
            st.session_state.blueprint_generated = True
            status.update(label="Blueprint generation complete!", state="complete", expanded=True)
            st.rerun()

    # --- Display Interactive Blueprint --- 
    if st.session_state.get('blueprint_generated'):
        render_blueprint_content()

    st.markdown("--- ")
    st.markdown("### 📝 Live Resume Editor")
    
    # Create a sanitized folder name from the job title
    job_title = st.session_state.job_description.name or "Untitled Job"
    sanitized_title = "".join(c for c in job_title if c.isalnum() or c in (' ', '_')).rstrip()
    output_folder = os.path.join("output", sanitized_title)

    # Editable text area for the resume
    edited_resume_json = st.text_area(
        "Edit your resume JSON below. Click 'Save & Archive' to save your changes.",
        value=st.session_state.resume.model_dump_json(indent=2),
        height=500
    )

    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    # Validate Improvements Button
    if col1.button("🔍 Validate Improvements", use_container_width=True):
        try:
            # Parse the edited resume
            new_resume = Resume.model_validate_json(edited_resume_json)
            
            # Run new analysis
            with st.spinner("Analyzing improvements..."):
                new_analysis = analysis_agent.analyze(new_resume, st.session_state.job_description)
                
                # Compare with old analysis
                if st.session_state.analysis_results:
                    comparison = generation_agent.compare_resume_improvements(
                        st.session_state.analysis_results,
                        new_analysis
                    )
                    
                    # Display comparison results
                    st.markdown("---")
                    st.markdown("### 📊 Improvement Analysis")
                    
                    # Status message with color
                    if comparison['color'] == 'success':
                        st.success(comparison['message'])
                    elif comparison['color'] == 'warning':
                        st.warning(comparison['message'])
                    elif comparison['color'] == 'info':
                        st.info(comparison['message'])
                    else:
                        st.error(comparison['message'])
                    
                    # Metrics
                    metric_col1, metric_col2, metric_col3 = st.columns(3)
                    with metric_col1:
                        st.metric("Previous Score", comparison['old_score'])
                    with metric_col2:
                        st.metric("New Score", comparison['new_score'], comparison['improvement'])
                    with metric_col3:
                        st.metric("Improved Matches", 
                                f"{comparison['improved_matches']}/{comparison['total_matches']}")
                    
                    # Recommendation
                    st.info(f"💡 **Recommendation:** {comparison['recommendation']}")
                    
                    # Option to apply changes
                    if st.button("✅ Apply These Changes"):
                        st.session_state.resume = new_resume
                        st.session_state.analysis_results = new_analysis
                        st.session_state.analysis_results['resume_hash'] = hash(new_resume.model_dump_json())
                        st.success("Changes applied! Resume updated.")
                        st.rerun()
                else:
                    st.warning("No previous analysis found. Save your resume first.")
                    
        except Exception as e:
            st.error(f"Error validating improvements: {e}")
    
    if col2.button("💾 Save & Archive", use_container_width=True):
        # Create initial notes file
        notes_path = os.path.join(output_folder, "notes.json")
        if not os.path.exists(notes_path):
            initial_notes = {
                "status": "Not Applied",
                "applied_date": None,
                "closed_date": None,
                "comments": ""
            }
            save_job_notes(output_folder, initial_notes)
        try:
            # Validate the edited JSON
            new_resume = Resume.model_validate_json(edited_resume_json)
            st.session_state.resume = new_resume

            # Create directory and save files
            os.makedirs(output_folder, exist_ok=True)
            with open(os.path.join(output_folder, "resume.json"), "w") as f:
                f.write(edited_resume_json)
            with open(os.path.join(output_folder, "job_description.json"), "w") as f:
                f.write(st.session_state.job_description.model_dump_json(indent=2))
            
            st.session_state.files_saved = True
            st.success(f"Resume and job description saved to `{output_folder}`! Re-running analysis with updated resume...")
            st.rerun()

        except Exception as e:
            st.error(f"Error saving resume. Please ensure it is valid JSON. Details: {e}")

    if col3.button("📄 Generate PDF Resume", use_container_width=True, disabled=not st.session_state.get('files_saved', False)):
        if not shutil.which("typst"):
            st.error("Typst is not installed or not in your system's PATH. Please install it to generate a PDF.")
            return

        with st.spinner("Generating PDF resume..."):
            try:
                source_template_path = os.path.abspath("career_toolkit/typst_templates/resume.typ")
                # Copy the template into the output folder to ensure it's in the root
                local_template_path = os.path.join(output_folder, "resume_template.typ")
                shutil.copy(source_template_path, local_template_path)

                output_pdf_path = os.path.join(output_folder, "resume.pdf")

                # Run the typst compile command, setting the root to the output folder.
                # The input file is now the *copied* template inside the root.
                process = subprocess.run(
                    ["typst", "compile", local_template_path, output_pdf_path, "--root", output_folder],
                    capture_output=True,
                    text=True,
                    check=True
                )
                st.success(f"Successfully generated PDF! View it at: `{output_pdf_path}`")

            except FileNotFoundError:
                st.error(f"Typst template file not found at `{source_template_path}`.")
            except subprocess.CalledProcessError as e:
                st.error(f"Failed to compile Typst resume. Error:\n{e.stderr}")
            except Exception as e:
                st.error(f"An unexpected error occurred during PDF generation: {e}")

    if col4.button("✉️ Cover Letter", use_container_width=True):
        st.session_state.step = "cover_letter"
        st.rerun()

def render_cover_letter():
    if st.button("← Back to Skill Gap Analysis"):
        st.session_state.step = "skill_gap"
        st.rerun()

    st.markdown("I will now generate a personalized cover letter by researching the company and highlighting your most relevant skills. You can edit the generated text and recipient details before creating the final PDF.")
    
    # --- Recipient Details ---
    st.markdown("#### Recipient Details")
    col1, col2, col3 = st.columns(3)
    st.session_state.recipient_name = col1.text_input("Recipient Name", value=st.session_state.recipient_name)
    st.session_state.recipient_title = col2.text_input("Recipient Title", value=st.session_state.recipient_title)
    st.session_state.company_address = col3.text_input("Company Address", value=st.session_state.company_address)

    # --- Cover Letter Text Generation and Editing ---
    st.markdown("#### Cover Letter Content")
    if st.button("Generate/Regenerate AI Cover Letter"):
        with st.spinner("Crafting your cover letter..."):
            # Generate the content
            cover_letter_content = generation_agent.generate_cover_letter(
                st.session_state.resume, 
                st.session_state.job_description, 
                st.session_state.recipient_name
            )
            st.session_state.cover_letter = cover_letter_content

            # Save the raw text content to the output folder
            job_title = st.session_state.job_description.name or "Untitled Job"
            sanitized_title = "".join(c for c in job_title if c.isalnum() or c in (' ', '_')).rstrip()
            output_folder = os.path.join("output", sanitized_title)
            os.makedirs(output_folder, exist_ok=True)
            with open(os.path.join(output_folder, "cover_letter_content.txt"), "w") as f:
                f.write(cover_letter_content)
            st.success(f"Cover letter content saved to `{os.path.join(output_folder, 'cover_letter_content.txt')}`")

    st.session_state.cover_letter = st.text_area(
        "Edit the generated cover letter below:", 
        value=st.session_state.cover_letter, 
        height=400
    )

    # --- PDF Generation ---
    if st.button("Generate PDF Cover Letter", disabled=not st.session_state.cover_letter):
        if not shutil.which("typst"):
            st.error("Typst is not installed or not in your system's PATH. Please install it to generate a PDF.")
            return

        job_title = st.session_state.job_description.name or "Untitled Job"
        sanitized_title = "".join(c for c in job_title if c.isalnum() or c in (' ', '_')).rstrip()
        output_folder = os.path.join("output", sanitized_title)
        os.makedirs(output_folder, exist_ok=True)

        with st.spinner("Generating PDF cover letter..."):
            try:
                template_path = "career_toolkit/typst_templates/coverletter.typ"
                output_typ_path = os.path.join(output_folder, "cover_letter.typ")
                output_pdf_path = os.path.join(output_folder, "cover_letter.pdf")

                # Save the user-uploaded signature directly into the output folder
                if st.session_state.signature_content and st.session_state.signature_filename:
                    signature_path = os.path.join(output_folder, st.session_state.signature_filename)
                    with open(signature_path, "wb") as f:
                        f.write(st.session_state.signature_content)

                with open(template_path, 'r') as f:
                    template_content = f.read()

                def escape_typst_string(s):
                    return s.replace('\\', '\\\\').replace('"', '\\"')

                def escape_typst_string(s):
                    return s.replace('\\', '\\\\').replace('"', '\\"')

                # Dynamically add the signature image to the template if it exists
                signature_typst_code = ""
                if st.session_state.signature_content and st.session_state.signature_filename:
                    signature_typst_code = f'#image("{escape_typst_string(st.session_state.signature_filename)}", width: 150pt)\n#v(-1em)'
                
                # Replace placeholders in the template
                replacements = {
                    '#let recipient_name = "Talent Management Team"': f'#let recipient_name = "{escape_typst_string(st.session_state.recipient_name)}"',
                    '#let recipient_title = "Talent Acquisition"': f'#let recipient_title = "{escape_typst_string(st.session_state.recipient_title)}"',
                    '#let company_name = "<COMPANY NAME>"': f'#let company_name = "{escape_typst_string(st.session_state.job_description.hiringOrganization or "")}"',
                    '#let company_address = "<ADDRESS>"': f'#let company_address = "{escape_typst_string(st.session_state.company_address)}"',
                    '#lorem(50)\n\n#lorem(65)\n\n#lorem(85)': st.session_state.cover_letter.replace('\n', '\n\n'),
                    '#v(3em) // Space for signature': signature_typst_code
                }
                for placeholder, value in replacements.items():
                    template_content = template_content.replace(placeholder, value)

                with open(output_typ_path, 'w') as f:
                    f.write(template_content)

                # Run Typst compilation
                subprocess.run(
                    ["typst", "compile", output_typ_path, "--root", output_folder],
                    capture_output=True, text=True, check=True
                )
                st.success(f"Successfully generated cover letter PDF! View it at: `{output_pdf_path}`")

            except subprocess.CalledProcessError as e:
                st.error(f"Failed to compile Typst cover letter. Error:\n{e.stderr}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

def get_job_notes(job_folder_path: str) -> dict:
    """Reads the notes.json file for a given job."""
    notes_path = os.path.join(job_folder_path, "notes.json")
    if os.path.exists(notes_path):
        with open(notes_path, 'r') as f:
            return json.load(f)
    return {}

def save_job_notes(job_folder_path: str, notes: dict):
    """Saves the notes dictionary to notes.json."""
    notes_path = os.path.join(job_folder_path, "notes.json")
    with open(notes_path, 'w') as f:
        json.dump(notes, f, indent=2)

def render_progress_tracker():
    """Renders a visual progress tracker for the workflow."""
    # Define workflow steps
    steps = [
        {"name": "📄 Upload Resume", "key": "settings"},
        {"name": "📝 Enter Job", "key": "enter_jd"},
        {"name": "✅ Review Job", "key": "jd_processed"},
        {"name": "🔍 Analysis", "key": "skill_gap"},
        {"name": "✉️ Cover Letter", "key": "cover_letter"}
    ]
    
    # Determine current step
    current_step = st.session_state.get('step', 'settings')
    current_index = next((i for i, s in enumerate(steps) if s['key'] == current_step), 0)
    
    # Create progress bar HTML - using single line strings to avoid whitespace issues
    progress_html = '<div style="display: flex; justify-content: space-between; align-items: center; margin: 2rem 0; padding: 1rem; background: var(--background-secondary); border-radius: 12px; border: 1px solid var(--border-color);">'
    
    for i, step in enumerate(steps):
        # Determine step status
        if i < current_index:
            status_color = "#10b981"  # Green - completed
            status_icon = "✓"
            opacity = "0.7"
        elif i == current_index:
            status_color = "#6366f1"  # Blue - current
            status_icon = "●"
            opacity = "1"
        else:
            status_color = "#475569"  # Gray - pending
            status_icon = "○"
            opacity = "0.5"
        
        # Add step - using single line to avoid whitespace issues
        progress_html += f'<div style="flex: 1; text-align: center; opacity: {opacity};"><div style="width: 40px; height: 40px; border-radius: 50%; background: {status_color}; color: white; display: flex; align-items: center; justify-content: center; margin: 0 auto 0.5rem; font-size: 1.2rem; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">{status_icon}</div><div style="font-size: 0.85rem; color: var(--text-secondary); font-weight: 500;">{step["name"]}</div></div>'
        
        # Add connector line (except after last step)
        if i < len(steps) - 1:
            connector_color = status_color if i < current_index else "#475569"
            progress_html += f'<div style="flex: 0.5; height: 2px; background: {connector_color}; margin: 0 0.5rem 2rem; opacity: 0.5;"></div>'
    
    progress_html += '</div>'
    
    st.markdown(progress_html, unsafe_allow_html=True)

def render_job_tracker():
    

    output_dir = "output"
    if not os.path.exists(output_dir) or not os.listdir(output_dir):
        st.info("No job applications have been saved yet. Analyze a job to get started!")
        return

    job_folders = [d for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d))]
    
    # Create a list of job data for better organization
    job_data = []
    for job_folder in job_folders:
        job_path = os.path.join(output_dir, job_folder)
        notes = get_job_notes(job_path)
        
        # Get employer name from job description
        employer_name = "Unknown Company"
        jd_path = os.path.join(job_path, "job_description.json")
        if os.path.exists(jd_path):
            try:
                with open(jd_path, 'r') as f:
                    jd_data = json.load(f)
                employer_name = jd_data.get('hiringOrganization', 'Unknown Company')
            except:
                pass
        
        job_data.append({
            'folder': job_folder,
            'path': job_path,
            'notes': notes,
            'employer': employer_name,
            'job_title': job_folder.replace('_', ' ')
        })
    
    # Sort by employer name, then by job title
    job_data.sort(key=lambda x: (x['employer'], x['job_title']))
    
    for job_info in job_data:
        job_folder = job_info['folder']
        job_path = job_info['path']
        notes = job_info['notes']
        employer_name = job_info['employer']
        job_title = job_info['job_title']

        with st.container(border=True):
            # Header with employer and job title
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"### 🏢 {employer_name}")
                st.markdown(f"**{job_title}**")
                
                # Status with color coding
                status = notes.get("status", "Not Applied")
                status_colors = {
                    "Not Applied": "🔵",
                    "Applied": "🟡", 
                    "Interviewing": "🟠",
                    "Offer Received": "🟢",
                    "Offer Accepted": "✅",
                    "Closed/Rejected": "🔴"
                }
                status_icon = status_colors.get(status, "⚪")
                st.markdown(f"{status_icon} **Status:** {status}")
                
                # Show dates if available
                if notes.get("applied_date"):
                    st.caption(f"📅 Applied: {notes.get('applied_date')}")
                if notes.get("closed_date"):
                    st.caption(f"🏁 Closed: {notes.get('closed_date')}")

            with col2:
                st.markdown("**Actions**")
                if st.button("📝 Edit Notes", key=f"notes_{job_folder}", use_container_width=True):
                    st.session_state.editing_notes_for = job_folder
                
            with col3:
                st.markdown("**Manage**")
                if st.session_state.get(f"confirm_delete_{job_folder}"):
                    if st.button("⚠️ Confirm Delete", key=f"confirm_btn_{job_folder}", type="primary", use_container_width=True):
                        shutil.rmtree(job_path)
                        st.success(f"Successfully deleted application for {employer_name}.")
                        del st.session_state[f"confirm_delete_{job_folder}"]
                        st.rerun()
                else:
                    if st.button("🗑️ Delete", key=f"delete_{job_folder}", use_container_width=True):
                        st.session_state[f"confirm_delete_{job_folder}"] = True
                        st.rerun()

            with st.expander("View Details & Documents"):
                # Display Job Description
                st.markdown("**Job Description**")
                jd_path = os.path.join(job_path, "job_description.json")
                if os.path.exists(jd_path):
                    with open(jd_path, 'r') as f:
                        jd_data = json.load(f)
                    
                    st.markdown(f"**Company:** {jd_data.get('hiringOrganization', 'N/A')}")
                    st.markdown(f"**Location:** {jd_data.get('jobLocation', 'N/A')}")
                    if jd_data.get('url'):
                        st.markdown(f"[View Original Posting]({jd_data.get('url')})")
                    
                    if jd_data.get('description'):
                        st.markdown(f"**Description:**\n{jd_data.get('description')}")

                    if jd_data.get('responsibilities'):
                        st.markdown("**Responsibilities:**")
                        for resp in jd_data.get('responsibilities'):
                            st.markdown(f"- {resp}")

                    if jd_data.get('qualifications'):
                        st.markdown("**Qualifications:**")
                        for qual in jd_data.get('qualifications'):
                            st.markdown(f"- {qual}")
                else:
                    st.warning("Job description file not found.")

                # Display Document Links
                st.markdown("**Generated Documents**")
                doc_col1, doc_col2 = st.columns(2)
                resume_pdf_path = os.path.join(job_path, "resume.pdf")
                cover_letter_pdf_path = os.path.join(job_path, "cover_letter.pdf")

                if os.path.exists(resume_pdf_path):
                    with open(resume_pdf_path, "rb") as f:
                        doc_col1.download_button("📄 Download Resume PDF", f.read(), file_name="resume.pdf", use_container_width=True)
                else:
                    doc_col1.button("📄 Resume PDF Not Found", disabled=True, use_container_width=True)
                
                if os.path.exists(cover_letter_pdf_path):
                    with open(cover_letter_pdf_path, "rb") as f:
                        doc_col2.download_button("✉️ Download Cover Letter PDF", f.read(), file_name="cover_letter.pdf", use_container_width=True)
                else:
                    doc_col2.button("✉️ Cover Letter PDF Not Found", disabled=True, use_container_width=True)

    # --- Notes Editing Modal ---
    if 'editing_notes_for' in st.session_state and st.session_state.editing_notes_for:
        job_folder = st.session_state.editing_notes_for
        job_path = os.path.join(output_dir, job_folder)
        notes = get_job_notes(job_path)

        with st.form(key=f"notes_form_{job_folder}"):
            st.subheader(f"Editing Notes for: {job_folder.replace('_', ' ')}")
            
            status_options = ["Not Applied", "Applied", "Interviewing", "Offer Received", "Offer Accepted", "Closed/Rejected"]
            current_status = notes.get("status", "Not Applied")
            new_status = st.selectbox("Application Status", options=status_options, index=status_options.index(current_status))

            applied_date = st.date_input("Date Applied", value=None if not notes.get("applied_date") else datetime.fromisoformat(notes.get("applied_date")))
            closed_date = st.date_input("Date Closed", value=None if not notes.get("closed_date") else datetime.fromisoformat(notes.get("closed_date")))
            comments = st.text_area("Comments", value=notes.get("comments", ""))

            submitted = st.form_submit_button("Save Notes")
            if submitted:
                updated_notes = {
                    "status": new_status,
                    "applied_date": applied_date.isoformat() if applied_date else None,
                    "closed_date": closed_date.isoformat() if closed_date else None,
                    "comments": comments
                }
                save_job_notes(job_path, updated_notes)
                st.success("Notes saved!")
                st.session_state.editing_notes_for = None
                st.rerun()

# --- Main App Logic ---
initialize_session_state()

# --- Top Navigation Bar ---
def render_top_nav():
    """Render the top navigation bar with Streamlit columns and buttons."""
    
    # Create navigation bar container
    st.markdown('<div class="nav-bar-container">', unsafe_allow_html=True)
    
    # Create columns: logo on left, spacer, then nav items on right
    logo_col, spacer, nav1, nav2, nav3 = st.columns([3, 4, 1.5, 1.5, 1.5])
    
    # Logo
    with logo_col:
        st.markdown('<div class="nav-logo">🤖 AI Job Coach</div>', unsafe_allow_html=True)
    
    # Navigation buttons on the right
    with nav1:
        if st.button("🎯 Job Coach", key="btn_coach"):
            st.session_state.current_page = "main_app"
            if st.session_state.step == "settings":
                st.session_state.step = "enter_jd"
            st.rerun()
    
    with nav2:
        if st.button("📈 Job Tracker", key="btn_tracker"):
            st.session_state.current_page = "job_tracker"
            st.rerun()
    
    with nav3:
        if st.button("⚙️ Settings", key="btn_settings"):
            st.session_state.step = "settings"
            st.session_state.current_page = "main_app"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Render navigation
render_top_nav()

# Conditional page headers based on current page/section
current_page = st.session_state.get('current_page', 'main_app')
current_step = st.session_state.get('step', 'enter_jd')

if current_page == "job_tracker":
    # Job Tracker Header
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0 2rem 0;">
        <h1 style="font-size: 2.5rem; margin-bottom: 0.5rem;">📈 Job Tracker</h1>
        <p style="font-size: 1.1rem; color: var(--text-muted); margin: 0;">
            Manage and track all your job applications in one place
        </p>
    </div>
    """, unsafe_allow_html=True)
elif current_step == "settings":
    # Settings Header
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0 2rem 0;">
        <h1 style="font-size: 2.5rem; margin-bottom: 0.5rem;">⚙️ Settings</h1>
        <p style="font-size: 1.1rem; color: var(--text-muted); margin: 0;">
            Configure your AI model, API key, resume, and signature preferences
        </p>
    </div>
    """, unsafe_allow_html=True)
else:
    # Job Coach section - show subtitle and progress tracker
    st.markdown("""
    <div style="text-align: center; padding: 0.5rem 0 1rem 0;">
        <p style="font-size: 1.1rem; color: var(--text-muted); margin: 0;">
            Optimize your resume with AI-powered insights tailored to each job application
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show progress tracker
    render_progress_tracker()
    
    # Show current step title (left-aligned)
    step_titles = {
        "update_resume": "Upload Resume",
        "enter_jd": "Enter Job Description",
        "jd_processed": "Job Description Processed",
        "skill_gap": "Skill Gap Analysis",
        "cover_letter": "Generate Cover Letter"
    }
    
    if current_step in step_titles:
        st.markdown(f"""
        <div style="padding: 1rem 0 0.5rem 0;">
            <h2 style="font-size: 1.8rem; margin: 0; color: var(--text-primary);">
                {step_titles[current_step]}
            </h2>
        </div>
        """, unsafe_allow_html=True)

# --- Main Content ---
if st.session_state.current_page == "job_tracker":
    render_job_tracker()
elif st.session_state.step == "settings":
    render_settings()
else:
    if st.session_state.step == "update_resume":
        render_update_resume()
    elif st.session_state.step == "enter_jd":
        render_enter_jd()
    elif st.session_state.step == "jd_processed":
        render_jd_processed()
    elif st.session_state.step == "skill_gap":
        render_skill_gap()
    elif st.session_state.step == "cover_letter":
        render_cover_letter()
