"""Settings page for AI Job Coach configuration."""

import os
import json
import streamlit as st
from agents.data_agent import Resume

USER_ASSETS_DIR = "career_toolkit/user_assets"


def render():
    """Render the settings page with all configuration options."""
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
