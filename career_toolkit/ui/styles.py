"""CSS styles for the AI Job Coach application."""

import streamlit as st


def apply_dark_mode_theme():
    """Apply modern dark mode theme with custom CSS."""
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
    
    /* Hide default sidebar */
    section[data-testid="stSidebar"] {
        display: none !important;
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
    
    .stSpinner {
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
    }
    
    /* Progress bars */
    .stProgress > div > div > div {
        border-radius: 4px;
    }
    
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
    
    .nav-bar-container > div {
        max-width: 1400px;
        margin: 0 auto;
        display: flex;
        align-items: center;
        justify-content: space-between;
        height: 70px;
    }
    
    .nav-bar-container [data-testid="column"] {
        padding: 0 !important;
        flex: 0 0 auto !important;
    }
    
    .nav-bar-container [data-testid="column"]:first-child {
        flex: 0 0 auto !important;
        margin-right: auto !important;
    }
    
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
    
    .nav-bar-container [data-testid="column"]:not(:first-child):not(:nth-child(2)) {
        margin-left: 1rem !important;
    }
    
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
    
    .nav-bar-container .stButton button:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        transform: none !important;
        box-shadow: none !important;
    }
    
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
    
    .nav-bar-container .stButton button:active,
    .nav-bar-container .stButton button:focus {
        background: rgba(255, 255, 255, 0.15) !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {visibility: hidden;}
    
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
    </style>
    """, unsafe_allow_html=True)
