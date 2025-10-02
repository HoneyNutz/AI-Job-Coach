"""Navigation bar component for the AI Job Coach application."""

import streamlit as st


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
