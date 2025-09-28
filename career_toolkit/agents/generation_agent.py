import openai
import os
import json
from .data_agent import Resume, JobDescription
from pydantic import HttpUrl
from typing import Dict, List, Optional

class GenerationAgent:
    def __init__(self, api_key: str = None):
        """
        Initializes the GenerationAgent with an OpenAI API key.
        The API key is required for all generation tasks.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Please set it as an environment variable 'OPENAI_API_KEY'.")
        openai.api_key = self.api_key

    def _call_llm(self, prompt: str, temperature: float = 0.5, max_tokens: int = 1500) -> str:
        """
        Private method to handle calls to the OpenAI ChatCompletion API.
        """
        try:
            response = openai.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert career assistant integrated into a Python application. Your responses should be concise and directly usable."}, 
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"An error occurred while calling the OpenAI API: {e}")
            return f"Error: Could not connect to the generation service. Details: {e}"

    _CONTEXT_LIMIT = 3800 # Characters

    def _summarize_if_needed(self, text: str, context: str = "job description") -> str:
        """Summarizes text if it exceeds a certain character limit to prevent truncation."""
        if len(text) <= self._CONTEXT_LIMIT:
            return text

        print(f"Info: Text for {context} is long ({len(text)} chars). Summarizing to fit context window.")
        
        prompt = f"""
        You are an expert data pre-processor for an AI system. The following text is too long to be processed directly.
        Your task is to summarize it into a concise version that preserves ALL essential information for analysis.
        Do not lose any key details, especially named entities, skills, qualifications, responsibilities, and specific requirements.
        The goal is to reduce the character count while retaining all critical data.

        Context of the text: {context}

        Original Text:
        ---
        {text}
        ---

        Return ONLY the summarized, condensed text.
        """
        return self._call_llm(prompt, temperature=0.0, max_tokens=1000) # Low temperature for factual summarization

    def extract_job_details(self, raw_text: str) -> Dict:
        """
        Parses raw job description text into a structured dictionary using an LLM,
        conforming to the jsonresume.org/job-description-schema.
        """
        processed_text = self._summarize_if_needed(raw_text, context="job description")

        prompt = f"""
        You are an expert HR analyst. Your task is to meticulously analyze the following job description text and extract the key information, structuring it into a clean JSON object that conforms to the JSON Resume schema for a job description.

        **Instructions:**
        1.  **Read the entire text carefully** to understand the context of the role, the company, and the ideal candidate.
        2.  **Synthesize information**: The required details might be spread across different sections. Combine related points into a coherent whole for each field.
        3.  **Be comprehensive**: Extract all relevant details for each field.
        4.  **Format correctly**: For fields like 'responsibilities' and 'qualifications', combine the points into a single, well-structured string. You can use newline characters (\\n) to separate bullet points or different thoughts. For 'skills', provide a comma-separated list.

        **JSON Schema Fields to Populate:**
        - `name`: The job title.
        - `hiringOrganization`: The name of the company.
        - `jobLocation`: The location of the job.
        - `description`: A brief, engaging summary of the company or the role's purpose.
        - `responsibilities`: A JSON array of strings, where each string is a distinct duty or responsibility.
        - `qualifications`: A JSON array of strings, where each string is a distinct qualification.
        - `skills`: A comma-separated string of the most important technical and soft skills mentioned (e.g., "Python, React, Project Management, Agile").
        - `educationRequirements`: A JSON array of strings describing the required education.
        - `experienceRequirements`: A JSON array of strings describing the required experience.

        **Job Description Text to Analyze:**
        ---
        {processed_text}
        ---

        Now, provide the JSON object. Return only the JSON.
        """
        response_str = self._call_llm(prompt)
        try:
            if response_str.startswith('```json'):
                response_str = response_str[7:-4].strip()
            data = json.loads(response_str)

            # Post-process fields that should be lists but might be strings
            for field in ['responsibilities', 'qualifications', 'educationRequirements', 'experienceRequirements']:
                if field in data and isinstance(data[field], str):
                    # Split by newline and filter out empty strings
                    data[field] = [item.strip() for item in data[field].split('\n') if item.strip()]
            
            return data
        except (json.JSONDecodeError, TypeError):
            print("Warning: LLM did not return valid JSON for job details. Falling back.")
            return {"description": raw_text} # Fallback

    def _analyze_for_cover_letter(self, resume: Resume, job_description: JobDescription) -> dict:
        """Analyzes the resume and job description to extract key themes and evidence for the cover letter."""
        prompt = f"""
        <Persona> You are an AI Career Strategist. Your task is to find the strongest narrative threads between a resume and a job description. </Persona>
        <Input_Data>
        - Resume: {resume.model_dump_json(indent=2)}
        - Job Description: {job_description.model_dump_json(indent=2)}
        </Input_Data>
        <Instructions>
        1.  **Identify Core Themes:** From the job description, identify the 3 most critical themes (e.g., 'Data-Driven Decision Making', 'Cross-Functional Leadership', 'Cloud Infrastructure Management').
        2.  **Find STAR-D Evidence:** For each theme, scan the resume for the single strongest piece of evidence. This should be a quantified achievement.
        3.  **Synthesize:** Create a "story point" for each theme.
        4.  **Output:** Return a JSON object with a single key, `story_points`, which is a list of objects. Each object in the list should have two keys: `theme` (string) and `evidence` (a string describing the specific, quantified achievement from the resume that supports the theme). Return ONLY the JSON object.
        </Instructions>
        """
        return self._call_llm_with_json_retry(prompt)

    def generate_cover_letter(self, resume: Resume, job_description: JobDescription, recipient_name: str) -> str:
        """
        Generates a personalized cover letter based on the resume, job description, and a new strategic prompt.
        """
        resume_json = resume.model_dump_json(indent=2)
        job_description_json = job_description.model_dump_json(indent=2)

        # Step 1: Perform the analysis to get the story points.
        story_points_data = self._analyze_for_cover_letter(resume, job_description)
        if 'error' in story_points_data:
            return f"Error during analysis phase: {story_points_data['error']}"

        prompt = f"""
        <Persona> You are an AI Career Communications Expert. Your task is to write a compelling cover letter narrative based on pre-analyzed story points. </Persona>
        <Goal> To write a passionate and highly-targeted cover letter (approx. 300 words) that weaves the provided story points into a seamless and persuasive narrative. </Goal>
        <Input_Data>
        - Story Points: {json.dumps(story_points_data, indent=2)}
        - User Name: {resume.basics.name}
        - Company Name: {job_description.hiringOrganization}
        - Job Title: {job_description.name}
        </Input_Data>
        <Methodology>
        1.  **The Hook:** Start with a powerful opening paragraph that expresses genuine enthusiasm for the role and company. Briefly introduce the core themes from the story points as the foundation of your fitness for the role.
        2.  **The Proof:** In the body of the letter (1-2 paragraphs), dedicate a few sentences to each `story_point`. Seamlessly weave the `theme` and its corresponding `evidence` into a compelling narrative. Show, don't just tell. Connect your past achievements directly to the company's needs.
        3.  **The Closing:** Conclude with a confident closing paragraph that reiterates your interest, summarizes your value proposition, and includes a clear call to action.
        </Methodology>
        <Constraints>
        - **Strict 300-word approximation.**
        - **Narrative Flow:** Do not just list the story points. You must connect them into a fluid, well-written letter.
        - **Tone:** Maintain a pleasant, passionate, and professional tone.
        </Constraints>
        <Output_Format> Generate ONLY the body text of the cover letter. Do NOT include salutations or closings. </Output_Format>
        """
        return self._call_llm(prompt, temperature=0.7, max_tokens=600)

    def _call_llm_with_json_retry(self, prompt: str, max_retries=2) -> dict:
        """Calls the LLM and retries if the output is not valid JSON, asking the LLM to fix it."""
        current_prompt = prompt
        for attempt in range(max_retries):
            response_str = self._call_llm(current_prompt, temperature=0.5)
            try:
                # Clean the response string of markdown fences
                if response_str.startswith('```json'):
                    response_str = response_str[7:-4].strip()
                return json.loads(response_str)
            except json.JSONDecodeError:
                print(f"Warning: LLM returned invalid JSON on attempt {attempt + 1}.")
                current_prompt = f"""
                Your previous response was not valid JSON. Please fix it.
                PREVIOUS INVALID RESPONSE:
                ---
                {response_str}
                ---
                Return ONLY the corrected, valid JSON object.
                """
        return {"error": f"Failed to get valid JSON after {max_retries} attempts."}

    def blueprint_step_1_strategic_assessment(self, resume: Resume, job_description: JobDescription):
        """Generates the strategic assessment part of the blueprint, including score, fitness, and opportunities."""
        prompt = f"""
        <Persona> You are an AI Career Strategist. </Persona>
        <Task> Analyze the resume and job description to perform a strategic assessment. </Task>
        <Input_Data>
        - Resume: {resume.model_dump_json(indent=2)}
        - Job Description: {job_description.model_dump_json(indent=2)}
        </Input_Data>
        <Instructions>
        1. **Keyword Mapping:** Scrutinize the job description. Extract the top 15-20 hard skills, soft skills, and technical qualifications. Calculate a 'Keyword Alignment Score' representing the percentage of these keywords present in the resume.
        2. **Experience Gap Identification:** Compare the job's core responsibilities against the resume's work history. Identify the top 3 areas where the user's experience is weakest or poorly communicated.
        3. **Initial Verdict:** Provide a one-sentence summary of the resume's current fitness for the role.
        4. **Output:** Return a JSON object with three keys: `alignment_score` (string percentage), `overall_fitness` (string), and `key_opportunities` (a list of 3 strings). Return ONLY the JSON object.
        </Instructions>
        """
        return self._call_llm_with_json_retry(prompt)

    def blueprint_step_2_keyword_table(self, resume: Resume, job_description: JobDescription):
        """Generates the keyword optimization table as a JSON array."""
        prompt = f"""
        <Persona> You are an AI Career Strategist. </Persona>
        <Task> Create a keyword optimization analysis. </Task>
        <Input_Data>
        - Resume: {resume.model_dump_json(indent=2)}
        - Job Description: {job_description.model_dump_json(indent=2)}
        </Input_Data>
        <Instructions>
        1.  Extract the top 15 most important keywords/skills from the job description.
        2.  For each keyword, determine if it's present in the resume (boolean true/false).
        3.  Assign a priority ('High', 'Medium', 'Low') based on its importance.
        4.  Provide a specific, actionable suggestion for where and how to include the keyword.
        5.  Calculate a confidence score (0-100) for each keyword based on how well the resume currently represents that skill.
        6.  **Output:** Return a JSON array where each object has keys: `keyword` (string), `found` (boolean), `priority` (string), `confidence` (integer), and `action` (string). Return ONLY the JSON array.
        </Instructions>
        """
        return self._call_llm_with_json_retry(prompt)

    def blueprint_step_3_summary(self, resume: Resume, job_description: JobDescription):
        """Rewrites the professional summary."""
        prompt = f"""
        <Persona> You are an AI Career Strategist. </Persona>
        <Task> Rewrite the user's professional summary. </Task>
        <Input_Data>
        - Current Summary: "{resume.basics.summary}"
        - Top 3 Job Requirements: {job_description.responsibilities[:3]}
        </Input_Data>
        <Instructions>
        1.  Rewrite the user's professional summary to be a powerful, 3-4 line "elevator pitch."
        2.  It must directly reflect the top 3 requirements of the job description and include high-priority keywords.
        3.  **Output:** Return only the rewritten summary as a single string.
        </Instructions>
        """
        return self._call_llm(prompt, max_tokens=500)

    def blueprint_step_4_achievements(self, highlight: str, work_title: str, job_description: JobDescription):
        """Rewrites a single work experience highlight using the STAR-D method."""
        prompt = f"""
        <Persona> You are an AI Career Strategist. </Persona>
        <Task> Rewrite a resume bullet point for maximum impact using the STAR-D method. </Task>
        <Input_Data>
        - Original Bullet Point: "{highlight}"
        - Role: "{work_title}"
        - Job Description Context: {job_description.responsibilities + job_description.qualifications}
        </Input_Data>
        <Instructions>
        1.  Rewrite the provided bullet point using the **STAR-D (Situation, Task, Action, Result, Detail)** method.
        2.  Focus on transforming passive duties into active, quantified achievements.
        3.  **Crucially, if a specific metric is missing, invent a plausible and specific placeholder metric to make the achievement tangible.** Frame it clearly as a placeholder (e.g., "...resulting in a [~15-20%] reduction in processing time," or "...managing a project budget of [approx. $250,000]"). This gives the user a concrete template to edit.
        4.  Provide a concise rationale for *why* the change was made, referencing either ATS optimization or recruitment psychology.
        5.  **Output:** Return a JSON object with three keys: `original_bullet` (string), `optimized_bullet` (string), and `rationale` (string). Return ONLY the JSON object.
        </Instructions>
        """
        return self._call_llm_with_json_retry(prompt)

    def generate_resume_recommendations(self, analysis_results: Dict) -> List[str]:
        """
        Generates specific, actionable recommendations for resume improvement based on analysis.
        (This is a placeholder for a more advanced implementation)
        """
        prompt = f"""
        Based on the following resume analysis, provide 3-5 specific, actionable recommendations for improvement.
        Focus on suggesting keywords from the job description and aligning experience with requirements.

        **Analysis:**
        {json.dumps(analysis_results, indent=2)}
        **Task:**
        Return a numbered list of recommendations.
        """
        # For this specific task, we can rely on the simpler recommendations from the analysis agent
        # or use a more advanced LLM call in the future.
        return analysis_results.get("recommendations", ["No recommendations generated."])

    def infer_skills(self, raw_text: str) -> Dict:
        """
        Infers potential skills from a job description that might not be explicitly listed.
        """
        prompt = f"""
        Analyze the following job description text. Based on the responsibilities and qualifications,
        infer a list of related technical or soft skills that an ideal candidate would likely possess, 
        even if they are not explicitly mentioned. 

        For example, if the job requires managing projects and leading a team, you might infer 'Agile Methodologies' or 'Leadership'.

        Job Description Text:
        --- 
        {raw_text[:2000]}
        ---

        Return a JSON object with a single key, "skills", containing a comma-separated string of the inferred skills.
        Return only the JSON object.
        """
        response_str = self._call_llm(prompt, temperature=0.2)
        try:
            if response_str.startswith('```json'):
                response_str = response_str[7:-4].strip()
            return json.loads(response_str)
        except (json.JSONDecodeError, TypeError):
            return {"skills": ""}
