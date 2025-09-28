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

# --- Agent Initialization ---
@st.cache_resource
def load_agents(api_key: str):
    return ScraperAgent(), AnalysisAgent(), GenerationAgent(api_key=api_key)

scraper_agent, analysis_agent, generation_agent = load_agents(st.session_state.get("openai_api_key"))

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
        sig_path = os.path.join(USER_ASSETS_DIR, "signature.png")
        if os.path.exists(sig_path):
            with open(sig_path, "rb") as f:
                st.session_state.signature_content = f.read()
            st.session_state.signature_filename = "signature.png"
        
        st.session_state.assets_loaded = True

    # Set initial step based on whether assets are present
    if 'step' not in st.session_state:
        if os.path.exists(os.path.join(USER_ASSETS_DIR, "resume.json")):
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


# --- UI Rendering Functions ---
def render_settings():
    st.header("⚙️ Application Settings")
    st.markdown("Here you can upload or update your baseline resume and signature.")

    # --- Resume Upload ---
    st.subheader("1. Your Resume")
    resume_uploader = st.file_uploader("Upload your JSON Resume", type="json")
    if resume_uploader is not None:
        try:
            resume_content = resume_uploader.read().decode('utf-8')
            # Save to session state
            st.session_state.resume = Resume.model_validate_json(resume_content)
            # Save persistently
            with open(os.path.join(USER_ASSETS_DIR, "resume.json"), "w") as f:
                f.write(resume_content)
            st.success("Resume updated and saved successfully!")
        except Exception as e:
            st.error(f"Invalid resume format: {e}")
    st.markdown("**Current Resume:**")
    st.json(st.session_state.resume.model_dump_json(indent=2, exclude_none=True))

    # --- Signature Upload ---
    st.subheader("2. Your Signature")
    signature_uploader = st.file_uploader("Upload your signature image (PNG format recommended)", type=["png", "jpg", "jpeg", "svg"])
    if signature_uploader is not None:
        # Standardize filename to signature.png
        new_filename = "signature.png"
        
        # Save to session state
        st.session_state.signature_content = signature_uploader.read()
        st.session_state.signature_filename = new_filename
        
        # Save new signature persistently
        with open(os.path.join(USER_ASSETS_DIR, new_filename), "wb") as f:
            f.write(st.session_state.signature_content)
        st.success(f"Signature updated and saved as '{new_filename}'!")
    
    if st.session_state.signature_content:
        st.markdown("**Current Signature:**")
        st.image(st.session_state.signature_content)
    else:
        st.info("No custom signature loaded. The cover letter will have a blank space for a signature.")

    st.markdown("--- ")
    if st.button("Back to Main Application", use_container_width=True):
        st.session_state.step = "enter_jd"
        st.rerun()


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
    st.header("📝 Enter Job Description Details")
    if st.button("← Back"):
        st.session_state.step = "welcome"
        st.rerun()
    jd_link = st.text_input("Link to the Job Description")
    jd_text = st.text_area("Paste the full job description content here", height=300)

    if st.button("Process Job Description"):
        if not jd_text:
            st.warning("Please paste the job description content.")
            return
        if not st.session_state.openai_api_key:
            st.error("OpenAI API Key is required. Please set it in the sidebar.")
            return
        
        with st.spinner("Analyzing job description..."):
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
            
            if jd_link:
                extracted_data['url'] = jd_link
            st.session_state.job_description = JobDescription(**extracted_data)
            st.session_state.step = "jd_processed"
            st.rerun()

def render_jd_processed():
    st.header("✅ Job Description Processed")
    jd = st.session_state.job_description
    st.markdown(f"**Job Title:** {jd.name}")
    st.markdown(f"**Company:** {jd.hiringOrganization}")

    with st.expander("View Full Processed JSON"):
        st.json(jd.model_dump_json(indent=2, exclude_none=True))
    
    if st.session_state.added_skills:
        st.info(f"I've inferred and added the following skills that were not explicitly listed: {', '.join(st.session_state.added_skills)}")

    st.markdown("--- ")
    st.markdown("What would you like to do next?")
    if st.button("Analyze Resume & Generate Documents"):
        st.session_state.step = "skill_gap"
        st.rerun()


def render_blueprint_content():
    """Renders the interactive blueprint UI from data in session state."""
    resume = st.session_state.resume
    assessment = st.session_state.blueprint_parts.get('assessment', {})
    keywords = st.session_state.blueprint_parts.get('keyword_table', [])

    st.subheader("1. Strategic Assessment")
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
    st.markdown("### Keyword Optimization Table")
    if isinstance(keywords, list):
        for item in keywords:
            st.markdown(f"**{item.get('keyword')}**")
            col1, col2, col3 = st.columns(3)
            found_text = "✅ Found" if item.get('found') else "❌ Missing"
            col1.metric("Status", found_text)
            col2.metric("Priority", item.get('priority', 'N/A'))
            confidence = item.get('confidence', 0)
            col3.progress(confidence / 100)
            col3.caption(f"Confidence: {confidence}%")
            st.warning(f"**Suggested Action:** {item.get('action')}")
            st.divider()
    else:
        st.error(keywords.get('error', 'Failed to generate keyword table.'))
    st.divider()

    st.markdown("### Recommended Professional Summary")
    edited_summary = st.text_area("Edit the AI-generated summary below:", value=st.session_state.blueprint_parts.get('editable_summary', ''), height=150, key="editable_summary_area")
    if st.button("Update Resume Summary"):
        st.session_state.resume.basics.summary = edited_summary
        st.success("Professional summary updated in the resume editor below!")
        st.rerun()
    st.divider()

    st.markdown("### Achievement-Driven Bullet Points")
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
    st.header("🔍 Skill Gap Analysis & Resume Editor")
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

            status.write("Step 2/4: Analyzing keyword alignment...")
            st.session_state.blueprint_parts['keyword_table'] = generation_agent.blueprint_step_2_keyword_table(resume, jd)

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

    col1, col2, col3 = st.columns([1, 1, 1])
    if col1.button("Save & Archive", use_container_width=True):
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

    if col2.button("Generate PDF Resume", use_container_width=True, disabled=not st.session_state.get('files_saved', False)):
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

    if col3.button("Proceed to Cover Letter Generation", use_container_width=True):
        st.session_state.step = "cover_letter"
        st.rerun()

def render_cover_letter():
    st.header("✉️ Cover Letter Generation")
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

                # Save the user-uploaded signature if it exists
                if st.session_state.signature_content and st.session_state.signature_filename:
                    graphics_dest = os.path.join(output_folder, "graphics")
                    os.makedirs(graphics_dest, exist_ok=True)
                    signature_path = os.path.join(graphics_dest, st.session_state.signature_filename)
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
                    signature_typst_code = f'#image("graphics/{escape_typst_string(st.session_state.signature_filename)}", width: 150pt)\n#v(-1em)'
                
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

def render_job_tracker():
    st.header("📈 Job Application Tracker")
    st.markdown("Here you can view and manage all of your analyzed job applications.")

    output_dir = "output"
    if not os.path.exists(output_dir) or not os.listdir(output_dir):
        st.info("No job applications have been saved yet. Analyze a job to get started!")
        return

    job_folders = [d for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d))]
    
    for job_folder in sorted(job_folders):
        job_path = os.path.join(output_dir, job_folder)
        notes = get_job_notes(job_path)

        with st.container(border=True):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.subheader(job_folder.replace('_', ' '))
                st.metric("Status", notes.get("status", "N/A"))

            with col2:
                st.markdown("**Quick Actions**")
                if st.button("View / Edit Notes", key=f"notes_{job_folder}", use_container_width=True):
                    st.session_state.editing_notes_for = job_folder
                
                if st.session_state.get(f"confirm_delete_{job_folder}"):
                    if st.button("Confirm Deletion", key=f"confirm_btn_{job_folder}", type="primary", use_container_width=True):
                        shutil.rmtree(job_path)
                        st.success(f"Successfully deleted application for {job_folder}.")
                        del st.session_state[f"confirm_delete_{job_folder}"]
                        st.rerun()
                else:
                    if st.button("Delete Application", key=f"delete_{job_folder}", use_container_width=True):
                        st.session_state[f"confirm_delete_{job_folder}"] = True
                        st.rerun()

            with st.expander("View Details & Documents"):
                # Display Job Description
                st.markdown("**Job Description**")
                jd_path = os.path.join(job_path, "job_description.json")
                if os.path.exists(jd_path):
                    with open(jd_path, 'r') as f:
                        jd_data = json.load(f)
                    st.json(jd_data)
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

st.title("🤖 AI Job Coach")

# --- Sidebar Navigation ---
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["AI Job Coach", "Job Tracker"], key="nav")

if page == "Job Tracker":
    st.session_state.current_page = "job_tracker"
else:
    st.session_state.current_page = "main_app"

st.sidebar.markdown("--- ")

# --- Sidebar Configuration ---
st.sidebar.header("Configuration")
st.session_state.openai_api_key = st.sidebar.text_input(
    "OpenAI API Key", type="password", value=st.session_state.openai_api_key
)
if not st.session_state.openai_api_key:
    st.sidebar.warning("OpenAI API Key is required for all features.")

st.sidebar.markdown("--- ")
if st.sidebar.button("Update Settings (Resume/Signature)"):
    st.session_state.step = "settings"
    st.rerun()

# --- Main Content ---
if st.session_state.current_page == "job_tracker":
    render_job_tracker()
else:
    if st.session_state.step == "settings":
        render_settings()
    elif st.session_state.step == "update_resume":
        render_update_resume()
    elif st.session_state.step == "enter_jd":
        render_enter_jd()
    elif st.session_state.step == "jd_processed":
        render_jd_processed()
    elif st.session_state.step == "skill_gap":
        render_skill_gap()
    elif st.session_state.step == "cover_letter":
        render_cover_letter()
