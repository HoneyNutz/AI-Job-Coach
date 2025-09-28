import os
import json
from .data_agent import Resume, JobDescription
from pydantic import HttpUrl
from typing import Dict, List, Optional
from openai import OpenAI

class GenerationAgent:
    def __init__(self, api_key: str = None):
        """
        Initializes the GenerationAgent with an OpenAI API key.
        The API key is required for all generation tasks.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Please set it as an environment variable 'OPENAI_API_KEY'.")
        # Ensure the SDK can find the API key and initialize a client
        os.environ["OPENAI_API_KEY"] = self.api_key
        self.client = OpenAI()
        # Allow overriding via env, default to gpt-5-mini per current configuration
        self.model_name = os.getenv("OPENAI_MODEL", "gpt-5-mini")

    def _call_llm(self, prompt: str, temperature: float = 0.5, max_tokens: int = 1500) -> str:
        """
        Private method to handle calls to OpenAI API with automatic fallback.
        """
        try:
            # Try Responses API first for reasoning models
            if self.model_name.startswith("gpt-5") or self.model_name.startswith("o4"):
                try:
                    kwargs = {
                        "model": self.model_name,
                        "input": [
                            {"role": "system", "content": "You are an expert career assistant. Provide precise, structured responses."},
                            {"role": "user", "content": prompt},
                        ],
                        "max_output_tokens": max_tokens,
                        "reasoning": {"effort": "medium"}
                    }
                    response = self.client.responses.create(**kwargs)
                    return getattr(response, "output_text", "").strip()
                except Exception as e:
                    print(f"Responses API failed, falling back to Chat Completions: {e}")
                    # Fall through to chat completions
            
            # Use Chat Completions API as fallback or for non-reasoning models
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",  # Reliable fallback model
                messages=[
                    {"role": "system", "content": "You are an expert career assistant. Provide precise, structured responses."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"An error occurred while calling the OpenAI API: {e}")
            return f"Error: Could not connect to the generation service. Details: {e}"

    def _extract_json_object(self, text: str) -> str:
        """Best-effort extraction of the first top-level JSON object from a text response."""
        if not text:
            return ""
        # Quick path: already clean
        s = text.strip()
        if s.startswith('{') and s.endswith('}'):
            return s
        # Remove common markdown fences
        if s.startswith('```'):
            s = s.strip('`')
        # Find first '{' and attempt to parse balanced braces
        start = s.find('{')
        if start == -1:
            return ""
        depth = 0
        for i in range(start, len(s)):
            if s[i] == '{':
                depth += 1
            elif s[i] == '}':
                depth -= 1
                if depth == 0:
                    candidate = s[start:i+1]
                    return candidate
        return ""

    _CONTEXT_LIMIT = 6000 # Characters

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
        # Low temperature for factual summarization, slightly higher token budget for fidelity
        return self._call_llm(prompt, temperature=0.0, max_tokens=2000)

    def extract_job_details(self, raw_text: str) -> Dict:
        """
        Parses raw job description text into a structured dictionary using an LLM,
        conforming to the jsonresume.org/job-description-schema.
        """
        processed_text = self._summarize_if_needed(raw_text, context="job description")

        prompt = f"""
        You are an expert HR analyst. Analyze the job description and return a STRICT JSON object that conforms to this schema and types:

        Required keys and types:
        - name: string (job title)
        - hiringOrganization: string (company)
        - jobLocation: string
        - description: string (1-3 sentences)
        - responsibilities: array of strings (each a distinct duty)
        - qualifications: array of strings (each a distinct qualification)
        - skills: string (comma-separated list of skills, e.g., "Python, React, Agile")
        - educationRequirements: array of strings
        - experienceRequirements: array of strings
        - originalText: string (the full original job description text; include as-is, unmodified)

        Rules:
        - Combine scattered bullets into unified arrays for responsibilities and qualifications.
        - If bullets are not explicitly present, infer 5-10 concise items from the prose.
        - Preserve important named entities and specific tools in responsibilities/qualifications where appropriate.
        - The output MUST be valid JSON and contain ALL required keys. Avoid leaving arrays empty unless absolutely no information exists; infer items when possible from the text.

        Job Description Text to Analyze (variable length):
        ---
        {processed_text}
        ---

        Full Original Text (do not modify; place into originalText):
        ---
        {raw_text}
        ---

        Return ONLY the JSON object.
        """
        # Use the JSON retry helper with a higher token budget and low temperature for structure fidelity
        response_obj = self._call_llm_with_json_retry(prompt, max_retries=2, temperature=0.2, max_tokens=4000)
        response_str = json.dumps(response_obj) if isinstance(response_obj, dict) else str(response_obj)
        try:
            if response_str.startswith('```json'):
                response_str = response_str[7:-4].strip()
            data = json.loads(response_str)

            # Normalize and guarantee required keys/types
            def ensure_list(value):
                if value is None:
                    return []
                if isinstance(value, list):
                    # Coerce all items to strings, strip empties
                    return [str(x).strip() for x in value if str(x).strip()]
                if isinstance(value, str):
                    parts = [p.strip() for p in value.replace('\r', '\n').split('\n') if p.strip()]
                    # Fallback: also split on semicolons if present
                    if len(parts) <= 1 and ';' in value:
                        parts = [p.strip() for p in value.split(';') if p.strip()]
                    return parts
                return [str(value).strip()]

            data.setdefault('name', '')
            data.setdefault('hiringOrganization', '')
            data.setdefault('jobLocation', '')
            data.setdefault('description', '')
            data.setdefault('responsibilities', [])
            data.setdefault('qualifications', [])
            data.setdefault('skills', '')
            data.setdefault('educationRequirements', [])
            data.setdefault('experienceRequirements', [])
            data.setdefault('originalText', raw_text)

            # Coerce list-typed fields
            for field in ['responsibilities', 'qualifications', 'educationRequirements', 'experienceRequirements']:
                data[field] = ensure_list(data.get(field))

            # Ensure skills is a comma-separated string
            if isinstance(data.get('skills'), list):
                data['skills'] = ', '.join([s for s in data['skills'] if s])
            elif not isinstance(data.get('skills'), str):
                data['skills'] = str(data['skills']) if data.get('skills') else ''

            # Heuristic fallback: if responsibilities/qualifications empty, infer from processed text lines
            if not data['responsibilities'] or not data['qualifications']:
                lines = [ln.strip(' •-*\t') for ln in processed_text.split('\n') if ln.strip()]
                bullets = [ln for ln in lines if len(ln) > 5]
                # Split heuristically into two halves if needed
                if not data['responsibilities'] and bullets:
                    data['responsibilities'] = bullets[: min(8, len(bullets))]
                if not data['qualifications'] and bullets:
                    data['qualifications'] = bullets[min(8, len(bullets)) : min(16, len(bullets))]

            # Second-pass recovery: if still empty, run focused extraction against originalText
            if (not data['responsibilities'] or not data['qualifications']) and raw_text:
                if not data['responsibilities']:
                    resp_prompt = f"""
                    Extract 8-12 distinct job responsibilities from the job description below.
                    Return ONLY a valid JSON object of the form: {{"items": ["resp1", "resp2", ...]}}.
                    Do not include any other keys.

                    Job Description:
                    ---
                    {raw_text}
                    ---
                    """
                    resp_obj = self._call_llm_with_json_retry(resp_prompt, max_retries=2, temperature=0.2, max_tokens=1200)
                    if isinstance(resp_obj, dict) and isinstance(resp_obj.get('items'), list):
                        data['responsibilities'] = [str(x).strip() for x in resp_obj['items'] if str(x).strip()]

                if not data['qualifications']:
                    qual_prompt = f"""
                    Extract 8-12 distinct candidate qualifications or requirements from the job description below (skills, experience, certifications).
                    Return ONLY a valid JSON object of the form: {{"items": ["qual1", "qual2", ...]}}.
                    Do not include any other keys.

                    Job Description:
                    ---
                    {raw_text}
                    ---
                    """
                    qual_obj = self._call_llm_with_json_retry(qual_prompt, max_retries=2, temperature=0.2, max_tokens=1200)
                    if isinstance(qual_obj, dict) and isinstance(qual_obj.get('items'), list):
                        data['qualifications'] = [str(x).strip() for x in qual_obj['items'] if str(x).strip()]

            return data
        except (json.JSONDecodeError, TypeError):
            print("Warning: LLM did not return valid JSON for job details. Falling back.")
            # Return a minimally valid structure while preserving the original text
            return {
                "name": "",
                "hiringOrganization": "",
                "jobLocation": "",
                "description": "",
                "responsibilities": [],
                "qualifications": [],
                "skills": "",
                "educationRequirements": [],
                "experienceRequirements": [],
                "originalText": raw_text,
            }

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

    def _call_llm_with_json_retry(self, prompt: str, max_retries=3, temperature: float = 0.3, max_tokens: int = 2000) -> dict:
        """Calls the LLM with robust JSON parsing and retry logic."""
        # Enhance prompt to be more explicit about JSON requirements
        json_prompt = f"""{prompt}
        
CRITICAL: Your response must be ONLY valid JSON. No explanations, no markdown, no extra text.
        Start with {{ and end with }}. Ensure all strings are properly quoted and escaped."""
        
        for attempt in range(max_retries):
            response_str = self._call_llm(json_prompt, temperature=temperature, max_tokens=max_tokens)
            
            # Skip if we got an error from the API
            if response_str.startswith("Error:"):
                print(f"API error on attempt {attempt + 1}: {response_str}")
                continue
                
            # Multiple parsing strategies
            for strategy in [self._parse_json_direct, self._parse_json_extract, self._parse_json_fix]:
                try:
                    result = strategy(response_str)
                    if result and isinstance(result, dict) and "error" not in result:
                        return result
                except Exception as e:
                    continue
            
            # Log failure details
            preview = (response_str or "")[:300].replace('\n', ' ')
            print(f"JSON parse failed attempt {attempt + 1}. Preview: {preview}")
            
            # Update prompt for retry
            json_prompt = f"""Fix this invalid JSON and return ONLY the corrected JSON:
            {response_str[:1000]}
            
            Requirements:
            - Must be valid JSON starting with {{ and ending with }}
            - All strings must be quoted
            - No trailing commas
            - No comments or explanations"""
        
        return {"error": f"Failed to get valid JSON after {max_retries} attempts"}
    
    def _parse_json_direct(self, text: str) -> dict:
        """Direct JSON parsing after basic cleanup."""
        cleaned = text.strip()
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]
        if cleaned.startswith('```'):
            cleaned = cleaned[3:]
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]
        return json.loads(cleaned.strip())
    
    def _parse_json_extract(self, text: str) -> dict:
        """Extract JSON object using brace matching."""
        extracted = self._extract_json_object(text)
        if extracted:
            return json.loads(extracted)
        raise json.JSONDecodeError("No JSON object found", text, 0)
    
    def _parse_json_fix(self, text: str) -> dict:
        """Attempt to fix common JSON issues."""
        import re
        # Remove common issues
        fixed = text.strip()
        # Remove trailing commas
        fixed = re.sub(r',\s*}', '}', fixed)
        fixed = re.sub(r',\s*]', ']', fixed)
        # Try to extract just the JSON part
        match = re.search(r'\{.*\}', fixed, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise json.JSONDecodeError("Could not fix JSON", text, 0)

    def blueprint_step_1_strategic_assessment(self, resume: Resume, job_description: JobDescription):
        """Generates the strategic assessment part of the blueprint."""
        prompt = f"""Analyze this resume against the job description and return a strategic assessment.
        
Resume Summary: {resume.basics.summary or 'No summary'}
Resume Skills: {', '.join(resume.skills) if resume.skills else 'No skills listed'}
Work Experience: {len(resume.work)} positions
        
Job Requirements: {', '.join(job_description.responsibilities[:5]) if job_description.responsibilities else 'No requirements listed'}
Required Skills: {job_description.skills or 'No skills specified'}
        
Analyze keyword alignment and identify gaps. Return JSON with exactly these keys:
{{
  "alignment_score": "XX%",
  "overall_fitness": "one sentence assessment",
  "key_opportunities": ["opportunity 1", "opportunity 2", "opportunity 3"]
}}"""
        return self._call_llm_with_json_retry(prompt, temperature=0.2, max_tokens=1000)

    def blueprint_step_2_keyword_table(self, resume: Resume, job_description: JobDescription):
        """Generates the keyword optimization table as a JSON array."""
        # Extract key info to avoid token bloat
        resume_text = f"{resume.basics.summary or ''} {' '.join(resume.skills or [])} {' '.join([w.name + ' ' + ' '.join(w.highlights or []) for w in resume.work[:3]])}"
        job_keywords = f"{job_description.skills or ''} {' '.join(job_description.responsibilities[:10]) if job_description.responsibilities else ''}"
        
        prompt = f"""Extract 8-12 key skills/keywords from this job description and check if they appear in the resume.
        
Job Keywords: {job_keywords[:1000]}
Resume Content: {resume_text[:1000]}
        
Return a JSON array with this exact structure:
[
  {{
    "keyword": "specific skill or technology",
    "found": true or false,
    "priority": "High" or "Medium" or "Low",
    "confidence": 0-100 integer,
    "action": "specific suggestion for improvement"
  }}
]"""
        return self._call_llm_with_json_retry(prompt, temperature=0.2, max_tokens=1800)

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
        return self._call_llm(prompt, max_tokens=700)

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
