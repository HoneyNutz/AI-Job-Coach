"""Reusable UI components for the AI Job Coach application."""

import streamlit as st


def render_progress_tracker():
    """Render a visual progress tracker for the job application workflow."""
    steps = [
        {"key": "enter_jd", "name": "Enter Job"},
        {"key": "jd_processed", "name": "Job Details"},
        {"key": "skill_gap", "name": "Analysis"},
        {"key": "cover_letter", "name": "Cover Letter"}
    ]
    
    current_step = st.session_state.get('step', 'enter_jd')
    current_index = next((i for i, s in enumerate(steps) if s['key'] == current_step), 0)
    
    # Create progress bar HTML
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
        
        # Add step
        progress_html += f'<div style="flex: 1; text-align: center; opacity: {opacity};"><div style="width: 40px; height: 40px; border-radius: 50%; background: {status_color}; color: white; display: flex; align-items: center; justify-content: center; margin: 0 auto 0.5rem; font-size: 1.2rem; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">{status_icon}</div><div style="font-size: 0.85rem; color: var(--text-secondary); font-weight: 500;">{step["name"]}</div></div>'
        
        # Add connector line (except after last step)
        if i < len(steps) - 1:
            connector_color = status_color if i < current_index else "#475569"
            progress_html += f'<div style="flex: 0.5; height: 2px; background: {connector_color}; margin: 0 0.5rem 2rem; opacity: 0.5;"></div>'
    
    progress_html += '</div>'
    
    st.markdown(progress_html, unsafe_allow_html=True)


def render_page_header():
    """Render conditional page headers based on current page/section."""
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
