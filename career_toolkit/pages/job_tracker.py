"""Job Tracker page for managing job applications."""

import os
import json
import shutil
import streamlit as st
from datetime import datetime
from utils.file_helpers import get_job_notes, save_job_notes


def render():
    """Render the job tracker page with all job applications."""
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
