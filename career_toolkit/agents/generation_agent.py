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
                model="gpt-3.5-turbo",
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

    def extract_job_details(self, raw_text: str) -> Dict:
        """
        Parses raw job description text into a structured dictionary using an LLM,
        conforming to the jsonresume.org/job-description-schema.
        """
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
        {raw_text[:4000]}
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

    def generate_cover_letter(self, resume: Resume, job_description: JobDescription, recipient_name: str) -> str:
        """
        Generates a personalized cover letter based on the resume, job description, and a new strategic prompt.
        """
        resume_json = resume.model_dump_json(indent=2)
        job_description_json = job_description.model_dump_json(indent=2)

        prompt = f"""
        <Persona> You are an AI Career Communications Expert. Your function is to synthesize a user's professional history with a company's specific needs to create a compelling narrative. You are a master of tone, persuasion, and brevity, crafting messages that resonate with hiring managers. </Persona>
        <Context> A cover letter's purpose is to bridge the gap between the structured facts of a resume and the human needs of a job description. It must be a concise, powerful story that demonstrates alignment and generates excitement. The user will provide their resume and a target job description in JSON format. </Context>
        <Goal> To generate a concise, passionate, and highly-targeted cover letter (under 200 words) that showcases the user's technical skills, leadership, and ability to manage complexity, directly aligning them with the target role. </Goal>
        <Input_Data>
        - Resume: {resume_json}
        - Job Description: {job_description_json}
        - User Name: {resume.basics.name}
        - Hiring Manager Name: {recipient_name}
        - Company Name: {job_description.hiringOrganization}
        - Job Title: {job_description.name}
        </Input_Data>
        <Methodology> Follow this three-step process precisely.
        **Step 1: Thematic Analysis & Keyword Extraction**
        1. **Identify Core Requirements:** From the `[job_description_json]`, extract the top 3-4 most critical requirements.
        2. **Scan for Evidence:** From the `[resume_json]`, identify specific projects, skills, or accomplishments that provide direct evidence for the requirements identified above.
        3. **Map to Core Themes:** Categorize the evidence under the three mandated themes:
        * **Technical Capabilities:** (e.g., specific programming languages, software, or technical achievements).
        * **Leadership Abilities:** (e.g., mentions of leading teams, mentoring, project management).
        * **Handling Complexity:** (e.g., roles involving large-scale projects, multi-faceted problems, or significant responsibility).
        **Step 2: Narrative Construction (3-Paragraph Structure)**
        1. **Paragraph 1: The Hook (Approx. 40 words):**
        * Start with enthusiasm for the `[Job Title]` role at `[Company Name]`.
        * Immediately connect your passion to 1-2 of the most critical requirements from the job description, stating your fitness for the role.
        2. **Paragraph 2: The Proof (Approx. 100 words):**
        * This is the core of the letter. Weave the evidence from Step 1.3 into a compelling narrative.
        * Create 2-3 powerful sentences. Each sentence should link a required skill (from the job) to a specific accomplishment (from the resume), implicitly or explicitly touching upon the themes of technical skill, leadership, and complexity.
        * **Example Structure:** "My experience in [Technical Skill from Resume] directly aligns with your need for [Requirement from Job Description], as demonstrated when I led [Project from Resume] to successfully [Quantified Result from Resume]."
        3. **Paragraph 3: The Closing (Approx. 40 words):**
        * Reiterate your strong interest and confidence in your ability to contribute.
        * State your enthusiasm for discussing how your skills in [mention 1-2 keywords] can benefit the team.
        * Provide a clear call to action.
        **Step 3: Tone & Polish**
        1. Review the entire draft to ensure it maintains a **pleasant, passionate, and professional** tone throughout.
        2. Verify the final word count is **under 200 words.** Edit for brevity and impact.
        </Methodology>
        <Constraints>
        - **Strict 200-word limit.** Do not exceed this.
        - **Evidence-Based:** Every claim made in the cover letter must be directly supported by the provided `[resume_json]`. Do not invent or infer details.
        - **Maintain specified tone:** The voice must be passionate and pleasant, not generic or robotic.
        </Constraints>
        <Output_Format> Generate only the final cover letter text, formatted and ready to be copied. </Output_Format>
        """
        return self._call_llm(prompt, temperature=0.7, max_tokens=400)

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
        3.  Where numbers are not present, instruct the user on what to find (e.g., "Increased efficiency by X%," "Managed a budget of $Y").
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
