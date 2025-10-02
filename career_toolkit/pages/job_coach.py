import os
import shutil
import subprocess
import streamlit as st
from agents.data_agent import Resume, JobDescription
from utils.file_helpers import save_job_notes
from agents.orchestrator import BlueprintOrchestrator

def render(scraper_agent, analysis_agent, generation_agent):
    # Your extracted functions here

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

                # New pipeline: structure -> enrich -> map to JobDescription
                structured = scraper_agent.structure_from_text(jd_text, generation_agent)
                enriched = generation_agent.enrich_job_description_schema_v1(structured, jd_text)
                # Persist enriched structured JD for downstream features (alignment report)
                st.session_state.structured_jd_v1 = enriched

                # Build JobDescription-compatible dict
                loc = enriched.get('location') or {}
                loc_parts = [
                    loc.get('address') or '',
                    loc.get('city') or '',
                    loc.get('region') or '',
                    loc.get('postalCode') or '',
                    loc.get('countryCode') or '',
                ]
                job_location_str = ', '.join([p for p in loc_parts if p]).strip(', ')

                # Flatten skills array of objects -> comma-separated string
                skills_list = []
                for s in enriched.get('skills') or []:
                    try:
                        name = (s.get('name') or '').strip()
                        if name:
                            skills_list.append(name)
                        for kw in (s.get('keywords') or []):
                            kw_s = str(kw).strip()
                            if kw_s:
                                skills_list.append(kw_s)
                    except Exception:
                        continue
                # De-duplicate while preserving order
                seen = set()
                flat_skills = []
                for item in skills_list:
                    if item.lower() not in seen:
                        seen.add(item.lower())
                        flat_skills.append(item)
                skills_str = ", ".join(flat_skills)

                extracted_data = {
                    'name': enriched.get('title') or '',
                    'hiringOrganization': enriched.get('company') or '',
                    'employmentType': enriched.get('type') or '',
                    'datePosted': enriched.get('date') or '',
                    'description': enriched.get('description') or '',
                    'jobLocation': job_location_str,
                    'skills': skills_str,
                    'responsibilities': enriched.get('responsibilities') or [],
                    'qualifications': enriched.get('qualifications') or [],
                    # Leave these empty; not provided by v1 schema directly
                    'educationRequirements': [],
                    'experienceRequirements': [],
                }

                # Track original text and url for downstream use
                st.session_state.job_description_full_text = jd_text
                if jd_link:
                    extracted_data['url'] = jd_link

                # Reset added/inferred markers for UI (optional for now)
                st.session_state.added_skills = []
                st.session_state.added_qualifications = []
                st.session_state.added_experience_requirements = []

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
        
        # Qualifications - mark AI-inferred items
        if jd.qualifications:
            with st.expander("✅ Required Qualifications", expanded=False):
                # Check if we have AI-inferred qualifications tracked
                inferred_quals = set(st.session_state.get('added_qualifications', []))
                
                for i, qual in enumerate(jd.qualifications, 1):
                    # Add sparkle if AI-inferred
                    qual_display = qual
                    if qual in inferred_quals:
                        qual_display = f'{qual} ✨'
                    st.markdown(f'<div style="margin-bottom: 0.75rem; padding-left: 1rem; border-left: 3px solid var(--secondary-color);"><span style="color: var(--secondary-color); font-weight: 600;">{i}.</span> <span style="color: var(--text-secondary);">{qual_display}</span></div>', unsafe_allow_html=True)
                
                if inferred_quals:
                    st.info(f"✨ **AI-Enhanced:** {len(inferred_quals)} qualification(s) were intelligently inferred from the job description.")
        
        # Experience requirements - mark AI-inferred items
        if jd.experienceRequirements:
            with st.expander("💼 Experience Requirements", expanded=False):
                # Check if we have AI-inferred experience requirements tracked
                inferred_exp = set(st.session_state.get('added_experience_requirements', []))
                
                for i, exp in enumerate(jd.experienceRequirements, 1):
                    # Add sparkle if AI-inferred
                    exp_display = exp
                    if exp in inferred_exp:
                        exp_display = f'{exp} ✨'
                    st.markdown(f'<div style="margin-bottom: 0.75rem; padding-left: 1rem; border-left: 3px solid var(--info-color);"><span style="color: var(--info-color); font-weight: 600;">{i}.</span> <span style="color: var(--text-secondary);">{exp_display}</span></div>', unsafe_allow_html=True)
                
                if inferred_exp:
                    st.info(f"✨ **AI-Enhanced:** {len(inferred_exp)} experience requirement(s) were intelligently inferred.")
        
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
        
        # Alignment Report (Markdown)
        st.subheader("📊 Alignment Report")
        if 'structured_jd_v1' not in st.session_state or not isinstance(st.session_state.structured_jd_v1, dict):
            st.info("Alignment report becomes available after the job description is structured. Go back and re-process the JD if needed.")
        else:
            col_a, col_b = st.columns([1, 1])
            with col_a:
                if st.button("Generate Alignment Report", key="gen_align_report", type="primary"):
                    with st.spinner("Generating alignment report..."):
                        md = generation_agent.generate_alignment_report_markdown(
                            st.session_state.resume,
                            st.session_state.structured_jd_v1
                        )
                        st.session_state.alignment_report_md = md
            with col_b:
                if st.session_state.get('alignment_report_md'):
                    st.download_button(
                        label="Download Report (.md)",
                        data=st.session_state.alignment_report_md,
                        file_name="alignment_report.md",
                        mime="text/markdown",
                        key="dl_align_report"
                    )

            if st.session_state.get('alignment_report_md'):
                st.markdown(st.session_state.alignment_report_md)
                if st.button("Regenerate Report", key="regen_align_report"):
                    with st.spinner("Regenerating alignment report..."):
                        md = generation_agent.generate_alignment_report_markdown(
                            st.session_state.resume,
                            st.session_state.structured_jd_v1
                        )
                        st.session_state.alignment_report_md = md
                        st.rerun()
        
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
                            if isinstance(result, dict) and 'error' not in result:
                                safe = {
                                    'original_bullet': result.get('original_bullet') or highlight,
                                    'optimized_bullet': result.get('optimized_bullet') or highlight,
                                    'rationale': result.get('rationale') or 'Optimized using STAR-D principles based on the target role.'
                                }
                                st.session_state.blueprint_parts['achievements'][unique_key] = safe
                st.success("Achievement suggestions updated.")
                st.rerun()
        # Defensive normalization in case old sessions have malformed entries
        ach_store = st.session_state.blueprint_parts.get('achievements', {})
        if isinstance(ach_store, dict):
            for _k, _v in list(ach_store.items()):
                if isinstance(_v, dict):
                    ach_store[_k] = {
                        'original_bullet': _v.get('original_bullet') or 'N/A',
                        'optimized_bullet': _v.get('optimized_bullet') or _v.get('original_bullet') or 'N/A',
                        'rationale': _v.get('rationale') or 'Optimized using STAR-D principles based on the target role.'
                    }
                else:
                    text_v = str(_v)
                    ach_store[_k] = {
                        'original_bullet': text_v,
                        'optimized_bullet': text_v,
                        'rationale': 'Optimized using STAR-D principles based on the target role.'
                    }

        for key, result in st.session_state.blueprint_parts.get('achievements', {}).items():
            try:
                work_idx, highlight_idx = map(int, key.split('_'))
                if work_idx >= len(st.session_state.resume.work) or highlight_idx >= len(st.session_state.resume.work[work_idx].highlights):
                    continue

                st.markdown(f"**For your role at {st.session_state.resume.work[work_idx].name}:**")
                st.markdown(f"* **Original:** {result.get('original_bullet', 'N/A')}")
                
                edited_bullet = st.text_area(
                    "Edit the AI-optimized bullet point:", 
                    value=result.get('optimized_bullet', ''), 
                    key=f"editable_bullet_{key}",
                    height=100
                )
                
                # Show rationale with safe default to avoid KeyError
                st.caption(f"**Rationale:** {result.get('rationale', 'Optimized using STAR-D principles based on the target role.')}")

                if st.button("Apply this suggestion", key=f"apply_{key}"):
                    original = result.get('original_bullet', '')
                    if original and st.session_state.resume.work[work_idx].highlights[highlight_idx] == original:
                        st.session_state.resume.work[work_idx].highlights[highlight_idx] = edited_bullet
                        st.success("Suggestion applied! The resume editor below has been updated.")
                        del st.session_state.blueprint_parts['achievements'][key]
                        st.rerun()
                    else:
                        st.warning("The original bullet point seems to have changed. Cannot apply suggestion automatically.")
                st.divider()
            except (ValueError, IndexError, KeyError, AttributeError) as e:
                # Skip malformed achievement entries
                st.warning(f"Skipping malformed achievement entry: {e}")
                continue

    def render_skill_gap():
        # Back button at the top
        if st.button("← Back to Job Details"):
            st.session_state.step = "jd_processed"
            st.rerun()
            return  # Stop rendering this page

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
                st.session_state.blueprint_parts = {}  # Initialize/reset
                resume = st.session_state.resume
                jd = st.session_state.job_description

                # Use orchestrator to run steps with progress updates
                orchestrator = BlueprintOrchestrator(generation_agent)
                parts = orchestrator.generate_blueprint(
                    resume,
                    jd,
                    progress=lambda msg: status.write(msg)
                )
                st.session_state.blueprint_parts = parts
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
            return  # Stop rendering this page

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
                        '#lorem(50)\n\n#lorem(65)\n\n#lorem(85)': str(st.session_state.cover_letter or '').replace('\n', '\n\n'),
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
    
    # Route to appropriate function based on current step
    step = st.session_state.get('step', 'enter_jd')
    
    if step == "enter_jd":
        render_enter_jd()
    elif step == "jd_processed":
        render_jd_processed()
    elif step == "skill_gap":
        render_skill_gap()
    elif step == "cover_letter":
        render_cover_letter()
    else:
        # Default to enter_jd
        render_enter_jd()
