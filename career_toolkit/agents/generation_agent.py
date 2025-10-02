import os
import json
import warnings
import asyncio
import concurrent.futures
import hashlib
import re
from functools import lru_cache
from sentence_transformers import SentenceTransformer, util
from .data_agent import Resume, JobDescription
from pydantic import HttpUrl
from typing import Dict, List, Optional, Tuple
from openai import OpenAI

# Shared constants to keep prompts consistent
JD_SCHEMA_V1 = """
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "title": "Job Description Schema",
  "type": "object",
  "additionalProperties": true,
  "properties": {
    "title": {"type": "string"},
    "company": {"type": "string"},
    "type": {"type": "string"},
    "date": {"type": "string"},
    "description": {"type": "string"},
    "location": {
      "type": "object",
      "additionalProperties": true,
      "properties": {
        "address": {"type": "string"},
        "postalCode": {"type": "string"},
        "city": {"type": "string"},
        "countryCode": {"type": "string"},
        "region": {"type": "string"}
      }
    },
    "remote": {"type": "string", "enum": ["Full", "Hybrid", "None"]},
    "salary": {"type": "string"},
    "experience": {"type": "string"},
    "responsibilities": {"type": "array", "items": {"type": "string"}},
    "qualifications": {"type": "array", "items": {"type": "string"}},
    "skills": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": true,
        "properties": {
          "name": {"type": "string"},
          "level": {"type": "string"},
          "keywords": {"type": "array", "items": {"type": "string"}}
        }
      }
    }
  }
}
"""

JD_SCHEMA_FIELDS_V1 = (
    "title, company, type, date, description, "
    "location(address, postalCode, city, countryCode, region), "
    "remote(Full|Hybrid|None), salary, experience, "
    "responsibilities[], qualifications[], "
    "skills[]: array of objects {name, level, keywords[]}"
)

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
        # Allow overriding via env, but restrict to allowed models only
        allowed_models = {"gpt-4o-mini", "gpt-5"}
        env_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.model_name = env_model if env_model in allowed_models else "gpt-4o-mini"
        # Per policy: use the same selected model for all tasks
        self.fast_model = self.model_name
        self.premium_model = self.model_name
        # Simple in-memory cache for job descriptions
        self._job_cache = {}
        # Initialize sentence transformer for semantic analysis
        self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')

    def _call_llm(self, prompt: str, temperature: float = 0.5, max_tokens: int = 1500, model_override: str = None, json_mode: bool = False) -> str:
        """
        Private method to handle calls to OpenAI API with automatic fallback.
        json_mode: If True, forces JSON response format (only works with compatible models)
        """
        try:
            # Decide target model once and route accordingly
            selected_model = model_override or self.model_name
            # Use Responses API only for GPT-5 with medium reasoning
            if selected_model == "gpt-5":
                try:
                    kwargs = {
                        "model": selected_model,
                        "input": [
                            {"role": "system", "content": "You are an expert career assistant. Provide precise, structured responses."},
                            {"role": "user", "content": prompt},
                        ],
                        "max_output_tokens": max_tokens,
                        "reasoning": {"effort": "medium"}
                    }
                    # Enforce JSON output when requested
                    if json_mode:
                        kwargs["response_format"] = {"type": "json_object"}
                    response = self.client.responses.create(**kwargs)
                    return getattr(response, "output_text", "").strip()
                except Exception as e:
                    print(f"Responses API failed, falling back to Chat Completions: {e}")
                    # Fall through to chat completions
            
            # Use Chat Completions API for GPT-4o-mini (or as fallback)
            
            # Build kwargs for API call
            kwargs = {
                "model": selected_model,
                "messages": [
                    {"role": "system", "content": "You are an expert career assistant. Provide precise, structured responses."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # Add JSON mode for compatible models (gpt-4o, gpt-4-turbo, gpt-3.5-turbo-1106+)
            if json_mode and any(m in selected_model for m in ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo-1106", "gpt-3.5-turbo-0125"]):
                kwargs["response_format"] = {"type": "json_object"}
            
            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"An error occurred while calling the OpenAI API: {e}")
            return f"Error: Could not connect to the generation service. Details: {e}"
    
    def _call_fast_llm(self, prompt: str, temperature: float = 0.3, max_tokens: int = 1000) -> str:
        """Fast model call for structured tasks."""
        return self._call_llm(prompt, temperature, max_tokens, model_override=self.fast_model)
    
    def _call_premium_llm(self, prompt: str, temperature: float = 0.5, max_tokens: int = 1500) -> str:
        """Premium model call for complex tasks."""
        return self._call_llm(prompt, temperature, max_tokens, model_override=self.premium_model)

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
<role>Expert Data Analyst specializing in information preservation and compression</role>

<task>Condense lengthy text while preserving 100% of critical information for career analysis</task>

<context>{context}</context>

<preservation_priorities>
1. All technical skills, tools, and technologies
2. Specific qualifications and requirements
3. Company names, job titles, and proper nouns
4. Quantifiable metrics and numbers
5. Key responsibilities and duties
6. Educational requirements and certifications
</preservation_priorities>

<compression_strategy>
- Remove redundant phrases and filler words
- Combine similar points into concise bullets
- Maintain all specific terminology
- Preserve industry jargon and acronyms
- Keep all measurable criteria intact
</compression_strategy>

<original_text>
{text}
</original_text>

Return only the condensed text with all critical information preserved.
        """
        # Optimized settings for information preservation
        return self._call_llm(prompt, temperature=0.1, max_tokens=2000)

    def extract_job_details(self, raw_text: str) -> Dict:
        """
        DEPRECATED: Use structure_job_description_schema_v1() + enrich_job_description_schema_v1().
        Returns legacy fields for backward compatibility:
        {"name","hiringOrganization","jobLocation","description","responsibilities","qualifications","skills","educationRequirements","experienceRequirements","originalText"}
        """
        warnings.warn(
            "extract_job_details() is deprecated; use structure_job_description_schema_v1() + enrich_job_description_schema_v1()",
            DeprecationWarning,
            stacklevel=2,
        )
        # Route to new pipeline and map to legacy shape
        processed_text = self._summarize_if_needed(raw_text, context="job description")
        structured = self.structure_job_description_schema_v1(processed_text)
        enriched = self.enrich_job_description_schema_v1(structured, processed_text)

        loc = enriched.get('location') or {}
        loc_parts = [
            loc.get('address') or '',
            loc.get('city') or '',
            loc.get('region') or '',
            loc.get('postalCode') or '',
            loc.get('countryCode') or '',
        ]
        job_location_str = ', '.join([p for p in loc_parts if p]).strip(', ')

        skills_list = []
        for s in enriched.get('skills') or []:
            try:
                if isinstance(s, dict):
                    name = (s.get('name') or '').strip()
                    if name:
                        skills_list.append(name)
                    for kw in (s.get('keywords') or []):
                        kw_s = str(kw).strip()
                        if kw_s:
                            skills_list.append(kw_s)
                else:
                    item = str(s).strip()
                    if item:
                        skills_list.append(item)
            except Exception:
                continue
        seen = set()
        flat_skills = []
        for item in skills_list:
            key = item.lower()
            if key not in seen:
                seen.add(key)
                flat_skills.append(item)
        skills_str = ", ".join(flat_skills)

        return {
            "name": enriched.get("title") or "",
            "hiringOrganization": enriched.get("company") or "",
            "jobLocation": job_location_str,
            "description": enriched.get("description") or "",
            "responsibilities": enriched.get("responsibilities") or [],
            "qualifications": enriched.get("qualifications") or [],
            "skills": skills_str,
            # v1 schema does not include these arrays; keep empty for backward compat
            "educationRequirements": [],
            "experienceRequirements": [],
            "originalText": raw_text,
        }

    def structure_job_description_schema_v1(self, raw_text: str) -> Dict:
        """
        Structures a job description into the provided schema (title, company, type, date, description,
        location, remote, salary, experience, responsibilities, qualifications, skills).

        Uses strict JSON mode when available and normalizes missing fields to safe defaults.
        Note: The 'meta' field is intentionally omitted/ignored in this model.
        """
        processed_text = self._summarize_if_needed(raw_text, context="job description")

        # Prompt focuses on: schema conformance, inference rules, and valid JSON only
        prompt = f"""
You are an expert Job Description parser. Restructure the following job description to match the exact schema below.
If fields like skills or qualifications are not explicit, infer them from responsibilities and description.
Return ONLY valid JSON for the object (no markdown, no comments, no explanations).

<schema>
{{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "title": "Job Description Schema",
  "type": "object",
  "additionalProperties": true,
  "properties": {{
    "title": {{"type": "string"}},
    "company": {{"type": "string"}},
    "type": {{"type": "string"}},
    "date": {{"type": "string"}},
    "description": {{"type": "string"}},
    "location": {{
      "type": "object",
      "additionalProperties": true,
      "properties": {{
        "address": {{"type": "string"}},
        "postalCode": {{"type": "string"}},
        "city": {{"type": "string"}},
        "countryCode": {{"type": "string"}},
        "region": {{"type": "string"}}
      }}
    }},
    "remote": {{"type": "string", "enum": ["Full", "Hybrid", "None"]}},
    "salary": {{"type": "string"}},
    "experience": {{"type": "string"}},
    "responsibilities": {{"type": "array", "items": {{"type": "string"}}}},
    "qualifications": {{"type": "array", "items": {{"type": "string"}}}},
    "skills": {{
      "type": "array",
      "items": {{
        "type": "object",
        "additionalProperties": true,
        "properties": {{
          "name": {{"type": "string"}},
          "level": {{"type": "string"}},
          "keywords": {{"type": "array", "items": {{"type": "string"}}}}
        }}
      }}
    }}
  }}
}}
</schema>

<input_text>
{processed_text}
</input_text>
"""
        # Use strict JSON mode first, with retries
        obj = self._call_llm_with_json_retry(prompt, max_retries=3, temperature=0.1, max_tokens=3500, model_override=self.fast_model)
        if not isinstance(obj, dict):
            obj = {}

        # Normalize and guarantee required shapes/types
        def ensure_list_str(arr):
            if arr is None:
                return []
            if isinstance(arr, list):
                return [str(x).strip() for x in arr if str(x).strip()]
            return [str(arr).strip()]

        def ensure_skills(sklist):
            if not sklist:
                return []
            out = []
            for s in sklist if isinstance(sklist, list) else []:
                try:
                    name = str(s.get("name", "")).strip() if isinstance(s, dict) else str(s)
                    level = str(s.get("level", "")).strip() if isinstance(s, dict) else ""
                    keywords = s.get("keywords", []) if isinstance(s, dict) else []
                    if not isinstance(keywords, list):
                        keywords = [str(keywords)]
                    keywords = [str(k).strip() for k in keywords if str(k).strip()]
                    if name:
                        out.append({"name": name, "level": level, "keywords": keywords})
                except Exception:
                    continue
            return out

        obj.setdefault("title", "")
        obj.setdefault("company", "")
        obj.setdefault("type", "")
        obj.setdefault("date", "")
        obj.setdefault("description", "")
        obj.setdefault("location", {})
        obj.setdefault("remote", "")
        obj.setdefault("salary", "")
        obj.setdefault("experience", "")
        obj.setdefault("responsibilities", [])
        obj.setdefault("qualifications", [])
        obj.setdefault("skills", [])

        # Coerce lists
        obj["responsibilities"] = ensure_list_str(obj.get("responsibilities"))
        obj["qualifications"] = ensure_list_str(obj.get("qualifications"))
        obj["skills"] = ensure_skills(obj.get("skills"))

        # Normalize remote to allowed set if possible
        remote_val = (obj.get("remote") or "").strip().lower()
        if remote_val.startswith("full"):
            obj["remote"] = "Full"
        elif remote_val.startswith("hyb"):
            obj["remote"] = "Hybrid"
        elif remote_val.startswith("none") or remote_val.startswith("on"):
            obj["remote"] = "None"

        # Ensure location is a dict with string fields
        if not isinstance(obj.get("location"), dict):
            obj["location"] = {}
        for k in ["address", "postalCode", "city", "countryCode", "region"]:
            v = obj["location"].get(k)
            if v is not None and not isinstance(v, str):
                obj["location"][k] = str(v)

        return obj

    def enrich_job_description_schema_v1(self, structured: Dict, raw_text: str) -> Dict:
        """
        Infers and fills missing fields in the structured job description, preserving existing values.
        - Only fills: title, company, type, date, description, location, remote, salary, experience,
          responsibilities[], qualifications[], skills[] (name, level, keywords)
        - Returns a fully normalized dict.
        """
        # Ensure we have a base structure to merge into
        base = self.structure_job_description_schema_v1(raw_text) if not isinstance(structured, dict) else structured.copy()

        processed_text = self._summarize_if_needed(raw_text, context="job description")
        prompt = f"""
You are an expert Job Description parser. Given a partially structured Job Description object and the original job description text,
infer and fill ONLY the missing fields according to the schema below. Preserve any existing values.
Return ONLY valid JSON for the completed object (no markdown, no comments, no explanations).

<schema_fields>
title, company, type, date, description, location(address, postalCode, city, countryCode, region),
remote(Full|Hybrid|None), salary, experience, responsibilities[], qualifications[],
skills[]: array of objects {{name, level, keywords[]}}
</schema_fields>

<partial_object>
{json.dumps(base, indent=2)}
</partial_object>

<original_text>
{processed_text}
</original_text>
"""
        obj = self._call_llm_with_json_retry(prompt, max_retries=3, temperature=0.1, max_tokens=3500, model_override=self.fast_model)
        if not isinstance(obj, dict):
            obj = {}

        # Merge: prefer values from obj when set, fall back to base
        def pick(new_val, old_val):
            if new_val is None:
                return old_val
            if isinstance(new_val, str):
                return new_val if new_val.strip() else old_val
            if isinstance(new_val, list):
                return new_val if len(new_val) > 0 else old_val
            if isinstance(new_val, dict):
                return new_val if len(new_val.keys()) > 0 else old_val
            return new_val or old_val

        merged = {}
        merged["title"] = pick(obj.get("title"), base.get("title", ""))
        merged["company"] = pick(obj.get("company"), base.get("company", ""))
        merged["type"] = pick(obj.get("type"), base.get("type", ""))
        merged["date"] = pick(obj.get("date"), base.get("date", ""))
        merged["description"] = pick(obj.get("description"), base.get("description", ""))
        merged["location"] = pick(obj.get("location"), base.get("location", {}))
        merged["remote"] = pick(obj.get("remote"), base.get("remote", ""))
        merged["salary"] = pick(obj.get("salary"), base.get("salary", ""))
        merged["experience"] = pick(obj.get("experience"), base.get("experience", ""))
        merged["responsibilities"] = pick(obj.get("responsibilities"), base.get("responsibilities", []))
        merged["qualifications"] = pick(obj.get("qualifications"), base.get("qualifications", []))
        merged["skills"] = pick(obj.get("skills"), base.get("skills", []))

        # Normalize similar to structure method
        def ensure_list_str(arr):
            if arr is None:
                return []
            if isinstance(arr, list):
                return [str(x).strip() for x in arr if str(x).strip()]
            return [str(arr).strip()]

        def ensure_skills(sklist):
            if not sklist:
                return []
            out = []
            for s in sklist if isinstance(sklist, list) else []:
                try:
                    name = str(s.get("name", "")).strip() if isinstance(s, dict) else str(s)
                    level = str(s.get("level", "")).strip() if isinstance(s, dict) else ""
                    keywords = s.get("keywords", []) if isinstance(s, dict) else []
                    if not isinstance(keywords, list):
                        keywords = [str(keywords)]
                    keywords = [str(k).strip() for k in keywords if str(k).strip()]
                    if name:
                        out.append({"name": name, "level": level, "keywords": keywords})
                except Exception:
                    continue
            return out

        merged["responsibilities"] = ensure_list_str(merged.get("responsibilities"))
        merged["qualifications"] = ensure_list_str(merged.get("qualifications"))
        merged["skills"] = ensure_skills(merged.get("skills"))

        # Normalize remote
        remote_val = (merged.get("remote") or "").strip().lower()
        if remote_val.startswith("full"):
            merged["remote"] = "Full"
        elif remote_val.startswith("hyb"):
            merged["remote"] = "Hybrid"
        elif remote_val.startswith("none") or remote_val.startswith("on"):
            merged["remote"] = "None"

        # Ensure location as strings
        if not isinstance(merged.get("location"), dict):
            merged["location"] = {}
        for k in ["address", "postalCode", "city", "countryCode", "region"]:
            v = merged["location"].get(k)
            if v is not None and not isinstance(v, str):
                merged["location"][k] = str(v)

        return merged

    def _analyze_for_cover_letter(self, resume: Resume, job_description: JobDescription) -> dict:
        """Analyzes the resume and job description to extract key themes and evidence for the cover letter."""
        prompt = f"""
<role>Senior Career Strategist specializing in executive-level positioning and narrative development</role>

<objective>Identify the 3 strongest alignment points between candidate experience and job requirements</objective>

<methodology>
1. Analyze job description to identify the 3 most critical success factors
2. Match each factor to the strongest quantified achievement from the resume
3. Prioritize achievements with specific metrics, outcomes, or business impact
</methodology>

<resume_data>
{resume.model_dump_json(indent=2)}
</resume_data>

<job_requirements>
{job_description.model_dump_json(indent=2)}
</job_requirements>

<output_format>
{{
  "story_points": [
    {{
      "theme": "Primary job requirement or skill area",
      "evidence": "Specific quantified achievement from resume with metrics"
    }}
  ]
}}
</output_format>

        Focus on achievements with numbers, percentages, dollar amounts, or measurable outcomes. Return only the JSON object.
        """
        return self._call_llm_with_json_retry(prompt, model_override=self.fast_model)

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
<role>Executive Communications Specialist with expertise in persuasive business writing</role>

<task>Write a compelling 300-word cover letter that transforms story points into a persuasive narrative</task>

<story_points>
{json.dumps(story_points_data, indent=2)}
</story_points>

<candidate_info>
Name: {resume.basics.name}
Target Company: {job_description.hiringOrganization}
Target Role: {job_description.name}
</candidate_info>

<structure>
Paragraph 1 (Hook): Express genuine enthusiasm and preview your strongest qualifications
Paragraph 2-3 (Evidence): Weave story points into a cohesive narrative showing impact
Paragraph 4 (Close): Reinforce value proposition and request next steps
</structure>

<writing_guidelines>
- Use active voice and strong action verbs
- Include specific metrics from story points naturally
- Show business impact, not just responsibilities
- Maintain confident, professional tone
- Connect achievements to company needs
- Target exactly 300 words
</writing_guidelines>

<example_integration>
Instead of: "I managed a team"
Write: "Leading a 12-person cross-functional team, I delivered a $2M cost reduction initiative 3 months ahead of schedule"
</example_integration>

Generate only the cover letter body text. No salutation or signature.
        """
        return self._call_llm(prompt, temperature=0.6, max_tokens=500)

    def generate_alignment_report_markdown(self, resume: Resume, structured_jd: Dict) -> str:
        """
        Generates a comprehensive alignment report in Markdown.
        structured_jd should follow the v1 schema (title/company/type/date/description/location/remote/salary/experience/responsibilities/qualifications/skills[]).
        """
        # Build minimal safe structured JD snippet for the prompt
        sjd = structured_jd or {}
        try:
            skills_preview = []
            for s in sjd.get('skills') or []:
                if isinstance(s, dict):
                    if s.get('name'):
                        skills_preview.append(s['name'])
                    for kw in (s.get('keywords') or []):
                        skills_preview.append(str(kw))
                else:
                    skills_preview.append(str(s))
            skills_preview = list(dict.fromkeys([x.strip() for x in skills_preview if str(x).strip()]))[:20]
        except Exception:
            skills_preview = []

        jd_min = {
            "title": sjd.get("title", ""),
            "company": sjd.get("company", ""),
            "type": sjd.get("type", ""),
            "date": sjd.get("date", ""),
            "description": sjd.get("description", "")[:800],
            "location": sjd.get("location", {}),
            "remote": sjd.get("remote", ""),
            "salary": sjd.get("salary", ""),
            "experience": sjd.get("experience", ""),
            "responsibilities": (sjd.get("responsibilities") or [])[:10],
            "qualifications": (sjd.get("qualifications") or [])[:10],
            "skills_preview": skills_preview,
        }

        prompt = f"""
You are a job description and resume analysis expert. Create a detailed Markdown report following the exact format.

<job_description_structured>
{json.dumps(jd_min, indent=2)}
</job_description_structured>

<resume_json>
{resume.model_dump_json(indent=2)}
</resume_json>

<instructions>
1) ## Overall Alignment Score: Provide a percentage (e.g., 85%) and a one-sentence rationale.
2) ## Strengths: Key Matches: Markdown table with columns | Job Requirement | Matching Resume Experience | (3-5 rows)
3) ## Gaps: Missing Requirements: Markdown table with columns | Job Requirement | Suggestion | (list critical gaps with advice)
4) ## Resume Tailoring Recommendations: 3-4 actionable bullets (concise and specific).

Rules:
- Use concise bullets and tables; no extra commentary outside the sections.
- Base content strictly on the provided JD and resume.
- If something is unclear or missing in the JD, make a reasonable inference and proceed.
</instructions>

Return ONLY the Markdown content.
"""
        return self._call_llm(prompt, temperature=0.3, max_tokens=1200)

    def _call_llm_with_json_retry(self, prompt: str, max_retries=4, temperature: float = 0.2, max_tokens: int = 2000, model_override: str = None) -> dict:
        """Calls the LLM with robust JSON parsing and retry logic."""
        # Enhanced JSON prompt with clearer, simpler instructions
        json_prompt = f"""{prompt}

CRITICAL: Your response must be ONLY valid JSON. No explanations, no markdown, no code blocks.
Start your response with {{ and end with }}"""
        
        last_response = ""
        for attempt in range(max_retries):
            # Use JSON mode on first attempt for compatible models
            use_json_mode = (attempt == 0)
            response_str = self._call_llm(json_prompt, temperature=temperature, max_tokens=max_tokens, model_override=model_override, json_mode=use_json_mode)
            last_response = response_str
            
            # Skip if we got an error from the API
            if response_str.startswith("Error:"):
                print(f"API error on attempt {attempt + 1}: {response_str}")
                continue
            
            # Debug: Show full response on failures
            if attempt > 0:
                print(f"\\n=== ATTEMPT {attempt + 1} FULL RESPONSE ===")
                print(response_str)
                print("=== END RESPONSE ===\\n")
                
            # Multiple parsing strategies with detailed error logging
            for strategy_name, strategy in [("direct", self._parse_json_direct), 
                                          ("extract", self._parse_json_extract), 
                                          ("fix", self._parse_json_fix)]:
                try:
                    result = strategy(response_str)
                    if result and isinstance(result, dict):
                        print(f"Success with {strategy_name} strategy on attempt {attempt + 1}")
                        return result
                except Exception as e:
                    print(f"{strategy_name} strategy failed: {e}")
                    continue
            
            # Log failure details with more context
            preview = (response_str or "")[:500].replace('\\n', ' ')
            print(f"All strategies failed on attempt {attempt + 1}. Preview: {preview}")
            
            # More specific retry prompts based on the error
            if attempt < max_retries - 1:
                if "```" in response_str:
                    json_prompt = f"""Remove all markdown formatting and return only the JSON object:
                    {response_str}"""
                elif not response_str.strip().startswith(("{", "[")):
                    json_prompt = f"""Extract and return only the JSON object from this text:
                    {response_str}"""
                else:
                    json_prompt = f"""Fix the JSON syntax errors in this response:
                    {response_str[:1500]}
                    
                    Return only valid JSON with proper syntax."""
        
        # Final fallback: try to construct a minimal valid response
        print(f"All attempts failed. Last response was: {last_response[:200]}")
        return {"error": f"Failed to get valid JSON after {max_retries} attempts", "last_response": last_response[:500]}
    
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
        
        # Handle truncated JSON arrays
        if fixed.startswith('[') and not fixed.endswith(']'):
            # Try to complete the truncated array
            fixed = self._complete_truncated_json_array(fixed)
        
        # Try to extract just the JSON part
        match = re.search(r'\{.*\}', fixed, re.DOTALL)
        if match:
            return json.loads(match.group())
        
        # Try array format
        match = re.search(r'\[.*\]', fixed, re.DOTALL)
        if match:
            return json.loads(match.group())
            
        raise json.JSONDecodeError("Could not fix JSON", text, 0)
    
    def _complete_truncated_json_array(self, text: str) -> str:
        """Attempt to complete a truncated JSON array."""
        try:
            # Count complete objects
            brace_count = 0
            complete_objects = []
            current_obj = ""
            in_string = False
            escape_next = False
            
            for char in text[1:]:  # Skip opening [
                if escape_next:
                    escape_next = False
                    current_obj += char
                    continue
                    
                if char == '\\':
                    escape_next = True
                    current_obj += char
                    continue
                    
                if char == '"' and not escape_next:
                    in_string = not in_string
                    
                current_obj += char
                
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            # Complete object found
                            complete_objects.append(current_obj.strip().rstrip(','))
                            current_obj = ""
            
            if complete_objects:
                # Return array with complete objects only
                return '[' + ','.join(complete_objects) + ']'
            else:
                # No complete objects, return empty array
                return '[]'
                
        except Exception:
            return '[]'

    def blueprint_step_1_strategic_assessment(self, resume: Resume, job_description: JobDescription):
        """Generates the strategic assessment part of the blueprint."""
        # Extract skill names safely with maximum defensive programming
        skill_names = []
        try:
            # Check if resume has skills attribute at all
            if hasattr(resume, 'skills') and resume.skills:
                # Handle different possible types for skills
                if isinstance(resume.skills, list):
                    for skill in resume.skills:
                        try:
                            if hasattr(skill, 'name') and skill.name:
                                skill_names.append(str(skill.name))
                            elif isinstance(skill, str):
                                skill_names.append(skill)
                            else:
                                skill_names.append(str(skill))
                        except Exception as skill_error:
                            print(f"Error processing individual skill: {skill_error}")
                            continue
                elif isinstance(resume.skills, str):
                    # Handle case where skills might be a single string
                    skill_names.append(resume.skills)
                else:
                    # Try to convert whatever it is to a string
                    skill_names.append(str(resume.skills))
        except Exception as e:
            print(f"Error extracting skills from resume: {e}")
            print(f"Resume skills type: {type(getattr(resume, 'skills', None))}")
            skill_names = []
        
        prompt = f"""You are a Senior ATS Optimization Specialist analyzing resume-job alignment.

RESUME PROFILE:
- Summary: {resume.basics.summary or 'No summary provided'}
- Core Skills: {', '.join(skill_names[:10]) if skill_names else 'No skills listed'}
- Experience: {len(resume.work)} professional positions

JOB REQUIREMENTS:
- Key Requirements: {', '.join(job_description.responsibilities[:5]) if job_description.responsibilities else 'None listed'}
- Technical Skills: {job_description.skills[:200] if job_description.skills else 'None specified'}
- Qualifications: {', '.join(job_description.qualifications[:3]) if job_description.qualifications else 'None listed'}

TASK: Calculate alignment score (0-100%) and identify exactly 3 specific improvement opportunities.

REQUIRED JSON FORMAT (respond with ONLY this JSON, no other text):
{{
  "alignment_score": "75%",
  "overall_fitness": "Strong technical match with room for optimization",
  "key_opportunities": [
    "Add specific metrics to quantify achievements",
    "Incorporate more job-specific keywords",
    "Highlight relevant certifications"
  ]
}}
"""
        return self._call_llm_with_json_retry(prompt, temperature=0.1, max_tokens=800, model_override=self.fast_model)

    def blueprint_step_2_keyword_table(self, resume: Resume, job_description: JobDescription):
        """DEPRECATED: Use blueprint_step_2_semantic_keyword_analysis(). Kept for backward compatibility."""
        warnings.warn(
            "blueprint_step_2_keyword_table() is deprecated; use blueprint_step_2_semantic_keyword_analysis()",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.blueprint_step_2_semantic_keyword_analysis(resume, job_description)

    def blueprint_step_3_summary(self, resume: Resume, job_description: JobDescription):
        """Rewrites the professional summary."""
        prompt = f"""
<role>Executive Resume Writer specializing in C-suite and senior-level positioning</role>

<task>Rewrite professional summary for maximum impact and ATS optimization</task>

<current_summary>
{resume.basics.summary}
</current_summary>

<target_requirements>
{job_description.responsibilities[:3]}
</target_requirements>

<key_skills_to_integrate>
{job_description.skills}
</key_skills_to_integrate>

<writing_framework>
1. Lead with years of experience and core expertise area
2. Highlight 2-3 quantified achievements that align with job requirements
3. Include 3-4 high-priority keywords naturally
4. End with value proposition statement
</writing_framework>

<style_guidelines>
- Use active voice and strong action verbs
- Include specific metrics where possible
- Maintain professional, confident tone
- Keep to 3-4 impactful sentences
- Optimize for both human readers and ATS
</style_guidelines>

Return only the rewritten professional summary text.
        """
        return self._call_fast_llm(prompt, temperature=0.3, max_tokens=400)

    def blueprint_step_4_achievements(self, highlight: str, work_title: str, job_description: JobDescription):
        """Rewrites a single work experience highlight using the STAR-D method."""
        prompt = f"""
<role>Senior Resume Optimization Specialist with expertise in achievement-based positioning</role>

<task>Transform a resume bullet point using STAR-D methodology for maximum impact</task>

<original_bullet>
{highlight}
</original_bullet>

<role_context>
{work_title}
</role_context>

<target_job_context>
{job_description.responsibilities + job_description.qualifications}
</target_job_context>

<star_d_framework>
- Situation: Brief context or challenge
- Task: Specific responsibility or objective
- Action: What you did (use strong action verbs)
- Result: Quantified outcome or impact
- Detail: Additional context that adds credibility
</star_d_framework>

<optimization_rules>
1. Start with strong action verb
2. Include specific metrics (create realistic placeholders if needed)
3. Show business impact, not just activities
4. Use keywords from target job description
5. Keep under 2 lines for readability
</optimization_rules>

<placeholder_guidance>
If metrics are missing, create realistic placeholders in brackets:
- "[~15-20%]" for percentage improvements
- "[approx. $250K]" for budget/revenue figures
- "[25+ team members]" for team sizes
</placeholder_guidance>

<output_format>
{{
  "original_bullet": "Original text",
  "optimized_bullet": "STAR-D optimized version",
  "rationale": "Brief explanation of changes and impact"
}}
</output_format>

Return only the JSON object.
        """
        resp = self._call_llm_with_json_retry(prompt)
        # Normalize and harden output: ensure required keys exist
        safe: dict = {}
        try:
            if isinstance(resp, dict):
                safe["original_bullet"] = resp.get("original_bullet") or highlight
                safe["optimized_bullet"] = resp.get("optimized_bullet") or highlight
                safe["rationale"] = resp.get("rationale") or "Optimized using STAR-D principles based on the target role."
            else:
                # Non-dict response, fall back
                safe = {
                    "original_bullet": highlight,
                    "optimized_bullet": highlight,
                    "rationale": "Optimized using STAR-D principles based on the target role."
                }
        except Exception:
            safe = {
                "original_bullet": highlight,
                "optimized_bullet": highlight,
                "rationale": "Optimized using STAR-D principles based on the target role."
            }
        return safe

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
        DEPRECATED: Use structure_job_description_schema_v1() + enrich_job_description_schema_v1(),
        then read the 'skills' array from the enriched object.
        Returns {"skills": ", "-joined string} for backward compatibility.
        """
        warnings.warn(
            "infer_skills() is deprecated; use structure_job_description_schema_v1() + enrich_job_description_schema_v1() and collect 'skills'.",
            DeprecationWarning,
            stacklevel=2,
        )
        structured = self.structure_job_description_schema_v1(raw_text)
        enriched = self.enrich_job_description_schema_v1(structured, raw_text)
        skills_list = []
        for s in enriched.get("skills") or []:
            try:
                if isinstance(s, dict):
                    name = (s.get("name") or "").strip()
                    if name:
                        skills_list.append(name)
                    for kw in (s.get("keywords") or []):
                        kw_s = str(kw).strip()
                        if kw_s:
                            skills_list.append(kw_s)
                else:
                    item = str(s).strip()
                    if item:
                        skills_list.append(item)
            except Exception:
                continue
        seen = set()
        flat = []
        for item in skills_list:
            k = item.lower()
            if k not in seen:
                seen.add(k)
                flat.append(item)
        return {"skills": ", ".join(flat)}
        prompt = f"""
<role>Senior Talent Acquisition Specialist with expertise in skill gap analysis</role>

<task>Infer implicit skills and competencies required for this role based on responsibilities and context</task>

<analysis_framework>
1. Technical skills implied by tools, platforms, or methodologies mentioned
2. Soft skills required for described responsibilities
3. Industry-standard competencies for this type of role
4. Cross-functional skills needed for collaboration
</analysis_framework>

<job_description>
{raw_text[:2000]}
</job_description>

<inference_examples>
- "Managing cross-functional teams" → "Leadership, Project Management, Stakeholder Management"
- "Data analysis and reporting" → "SQL, Excel, Data Visualization, Statistical Analysis"
- "Client presentations" → "Public Speaking, PowerPoint, Communication Skills"
</inference_examples>

<output_format>
{{
  "skills": "comma-separated list of inferred skills"
}}
</output_format>

Return only the JSON object with 8-12 relevant inferred skills.
        """
        response_str = self._call_llm(prompt, temperature=0.3, max_tokens=300)
        try:
            if response_str.startswith('```json'):
                response_str = response_str[7:-4].strip()
            return json.loads(response_str)
        except (json.JSONDecodeError, TypeError):
            return {"skills": ""}

    def generate_blueprint_parallel(self, resume: Resume, job_description: JobDescription) -> Dict:
        """
        Generates blueprint components in parallel for improved performance.
        Uses fast models for structured tasks and premium models for complex analysis.
        """
        def run_step_1():
            return self.blueprint_step_1_strategic_assessment(resume, job_description)
        
        def run_step_2():
            return self.blueprint_step_2_semantic_keyword_analysis(resume, job_description)
        
        def run_step_3():
            return self.blueprint_step_3_summary(resume, job_description)
        
        # Run steps 1, 2, and 3 in parallel (they don't depend on each other)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_step_1 = executor.submit(run_step_1)
            future_step_2 = executor.submit(run_step_2)
            future_step_3 = executor.submit(run_step_3)
            
            # Collect results
            try:
                strategic_assessment = future_step_1.result(timeout=30)
                keyword_table = future_step_2.result(timeout=30)
                summary = future_step_3.result(timeout=30)
                
                return {
                    "strategic_assessment": strategic_assessment,
                    "keyword_table": keyword_table,
                    "optimized_summary": summary,
                    "performance_mode": "parallel_fast_models"
                }
            except concurrent.futures.TimeoutError:
                return {
                    "error": "Blueprint generation timed out. Try using individual steps.",
                    "performance_mode": "timeout_fallback"
                }
            except Exception as e:
                return {
                    "error": f"Blueprint generation failed: {str(e)}",
                    "performance_mode": "error_fallback"
                }

    def _get_job_hash(self, raw_text: str) -> str:
        """Generate a hash for job description caching."""
        return hashlib.md5(raw_text.encode()).hexdigest()

    def extract_job_details_cached(self, raw_text: str) -> Dict:
        """
        DEPRECATED: Cached wrapper for extract_job_details().
        Prefer structure_job_description_schema_v1() + enrich_job_description_schema_v1() with your own caching.
        """
        job_hash = self._get_job_hash(raw_text)
        
        # Check cache first
        if job_hash in self._job_cache:
            print(f"Using cached job details for hash: {job_hash[:8]}...")
            return self._job_cache[job_hash]
        
        # Extract and cache
        result = self.extract_job_details(raw_text)
        self._job_cache[job_hash] = result
        
        return result

    def configure_performance_mode(self, mode: str = "balanced"):
        """
        Configure performance settings for different use cases.
        
        Args:
            mode: "speed", "balanced", or "quality"
        """
        if mode == "speed":
            self.fast_model = "gpt-4o-mini"
            self.premium_model = "gpt-4o-mini"
            print("⚡ Speed mode: Using gpt-4o-mini for all tasks")
        elif mode == "quality":
            self.fast_model = "gpt-4-turbo-preview"
            self.premium_model = "gpt-4-turbo-preview"
            print("🎯 Quality mode: Using gpt-4-turbo-preview for all tasks")
        else:  # balanced
            self.fast_model = "gpt-4o-mini"
            self.premium_model = "gpt-4-turbo-preview"
            print("⚖️ Balanced mode: Using gpt-4o-mini for structured tasks, gpt-4-turbo-preview for complex tasks")

    def get_performance_stats(self) -> Dict:
        """Get current performance configuration and cache stats."""
        return {
            "current_model": self.model_name,
            "fast_model": self.fast_model,
            "premium_model": self.premium_model,
            "cached_jobs": len(self._job_cache),
            "cache_keys": list(self._job_cache.keys())[:5]  # Show first 5 cache keys
        }

    def compare_resume_improvements(self, old_analysis: Dict, new_analysis: Dict) -> Dict:
        """
        Compare two analysis results to show improvement metrics.
        
        Args:
            old_analysis: Analysis results before changes
            new_analysis: Analysis results after changes
            
        Returns:
            Dictionary with improvement metrics and insights
        """
        try:
            # Extract scores
            old_score = float(old_analysis.get('overall_score', '0%').rstrip('%')) / 100
            new_score = float(new_analysis.get('overall_score', '0%').rstrip('%')) / 100
            
            improvement = new_score - old_score
            improvement_pct = (improvement / old_score * 100) if old_score > 0 else 0
            
            # Analyze match improvements
            old_matches = old_analysis.get('match_results', [])
            new_matches = new_analysis.get('match_results', [])
            
            improved_matches = 0
            declined_matches = 0
            
            for i, (old_match, new_match) in enumerate(zip(old_matches, new_matches)):
                old_conf = old_match.get('confidence_score', 0)
                new_conf = new_match.get('confidence_score', 0)
                
                if new_conf > old_conf:
                    improved_matches += 1
                elif new_conf < old_conf:
                    declined_matches += 1
            
            # Determine overall status
            if improvement > 0.05:
                status = "significant_improvement"
                message = "🎉 Significant improvement! Your resume is much better aligned."
                color = "success"
            elif improvement > 0:
                status = "minor_improvement"
                message = "✅ Good progress! Your resume alignment has improved."
                color = "success"
            elif improvement == 0:
                status = "no_change"
                message = "➡️ No change detected. Consider applying more suggestions."
                color = "info"
            else:
                status = "declined"
                message = "⚠️ Score decreased. Review your changes carefully."
                color = "warning"
            
            return {
                "status": status,
                "message": message,
                "color": color,
                "old_score": f"{old_score:.1%}",
                "new_score": f"{new_score:.1%}",
                "improvement": f"{improvement:+.1%}",
                "improvement_percentage": f"{improvement_pct:+.1f}%",
                "improved_matches": improved_matches,
                "declined_matches": declined_matches,
                "total_matches": len(old_matches),
                "recommendation": self._generate_improvement_recommendation(improvement, improved_matches, len(old_matches))
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Could not compare results: {str(e)}",
                "color": "error"
            }
    
    def _generate_improvement_recommendation(self, improvement: float, improved_matches: int, total_matches: int) -> str:
        """Generate actionable recommendation based on improvement analysis."""
        if improvement > 0.1:
            return "Excellent work! Consider generating your final resume and cover letter."
        elif improvement > 0.05:
            return "Great progress! Review remaining blueprint suggestions for further optimization."
        elif improvement > 0:
            return "You're on the right track. Apply more blueprint suggestions to increase alignment."
        elif improvement == 0:
            return "Try applying the professional summary and achievement suggestions from the blueprint."
        else:
            return "Review your changes. Ensure you're incorporating keywords and skills from the job description."

    def _extract_skills_from_job_description(self, job_description: JobDescription) -> List[str]:
        """Extract and normalize skills from job description using multiple sources."""
        skills = []
        
        # Extract from explicit skills field
        if job_description.skills:
            explicit_skills = [s.strip() for s in job_description.skills.split(',') if s.strip()]
            skills.extend(explicit_skills)
        
        # Extract from responsibilities and qualifications using regex patterns
        skill_patterns = [
            r'\b(?:experience with|proficiency in|knowledge of|skilled in|expertise in)\s+([^,.;]+)',
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:programming|development|framework|library|database|platform)',
            r'\b(Python|JavaScript|Java|React|Angular|Vue|SQL|MongoDB|AWS|Azure|Docker|Kubernetes|Git|Jenkins|Terraform|Ansible)\b',
            r'\b([A-Z]{2,}(?:\.[A-Z]{2,})*)\b',  # Acronyms like API, REST, etc.
        ]
        
        text_sources = (job_description.responsibilities or []) + (job_description.qualifications or [])
        
        for text in text_sources:
            for pattern in skill_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0] if match[0] else match[1]
                    if len(match.strip()) > 2:  # Filter out very short matches
                        skills.append(match.strip())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_skills = []
        for skill in skills:
            skill_lower = skill.lower()
            if skill_lower not in seen and len(skill) > 2:
                seen.add(skill_lower)
                unique_skills.append(skill)
        
        return unique_skills[:12]  # Return top 12 skills

    def _extract_skills_from_resume(self, resume: Resume) -> List[Dict[str, str]]:
        """Extract skills and experiences from resume with context."""
        resume_skills = []
        
        # Extract from explicit skills section
        if hasattr(resume, 'skills') and resume.skills:
            if isinstance(resume.skills, list):
                for skill in resume.skills:
                    skill_name = skill.name if hasattr(skill, 'name') else str(skill)
                    resume_skills.append({
                        'skill': skill_name,
                        'context': 'Listed in skills section',
                        'source': 'skills'
                    })
        
        # Extract from work experience
        for work in resume.work:
            work_context = f"{work.position} at {work.name}"
            
            # From job title and summary
            if work.position:
                resume_skills.append({
                    'skill': work.position,
                    'context': work_context,
                    'source': 'job_title'
                })
            
            # From highlights/achievements
            if work.highlights:
                for highlight in work.highlights:
                    # Extract technical terms and tools
                    tech_terms = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|[A-Z]{2,}(?:\.[A-Z]{2,})*)\b', highlight)
                    for term in tech_terms:
                        if len(term) > 2:
                            resume_skills.append({
                                'skill': term,
                                'context': f"{work_context}: {highlight[:100]}...",
                                'source': 'experience'
                            })
        
        # Extract from summary
        if resume.basics and resume.basics.summary:
            tech_terms = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|[A-Z]{2,}(?:\.[A-Z]{2,})*)\b', resume.basics.summary)
            for term in tech_terms:
                if len(term) > 2:
                    resume_skills.append({
                        'skill': term,
                        'context': f"Professional summary: {resume.basics.summary[:100]}...",
                        'source': 'summary'
                    })
        
        return resume_skills

    def _calculate_semantic_similarity(self, job_skill: str, resume_skill: str) -> float:
        """Calculate semantic similarity between job skill and resume skill."""
        try:
            # Create embeddings
            job_embedding = self.semantic_model.encode([job_skill], convert_to_tensor=True)
            resume_embedding = self.semantic_model.encode([resume_skill], convert_to_tensor=True)
            
            # Calculate cosine similarity
            similarity = util.cos_sim(job_embedding, resume_embedding)[0][0].item()
            return similarity
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0.0

    def _find_best_skill_matches(self, job_skills: List[str], resume_skills: List[Dict[str, str]]) -> List[Dict]:
        """Find best semantic matches between job skills and resume skills."""
        matches = []
        
        for job_skill in job_skills:
            best_match = {
                'job_skill': job_skill,
                'resume_skill': None,
                'similarity_score': 0.0,
                'context': '',
                'source': '',
                'found': False
            }
            
            # Check for exact matches first
            for resume_skill in resume_skills:
                if job_skill.lower() == resume_skill['skill'].lower():
                    best_match.update({
                        'resume_skill': resume_skill['skill'],
                        'similarity_score': 1.0,
                        'context': resume_skill['context'],
                        'source': resume_skill['source'],
                        'found': True
                    })
                    break
            
            # If no exact match, find best semantic match
            if not best_match['found']:
                for resume_skill in resume_skills:
                    similarity = self._calculate_semantic_similarity(job_skill, resume_skill['skill'])
                    if similarity > best_match['similarity_score']:
                        best_match.update({
                            'resume_skill': resume_skill['skill'],
                            'similarity_score': similarity,
                            'context': resume_skill['context'],
                            'source': resume_skill['source'],
                            'found': similarity > 0.7  # Threshold for "found"
                        })
            
            matches.append(best_match)
        
        return matches

    def _generate_skill_recommendations(self, match: Dict) -> str:
        """Generate actionable recommendations based on skill match analysis."""
        score = match['similarity_score']
        job_skill = match['job_skill']
        resume_skill = match['resume_skill']
        found = match['found']
        
        if found and score >= 0.9:
            return f"Perfect match! Ensure '{resume_skill}' is prominently featured"
        elif found and score >= 0.7:
            return f"Good match with '{resume_skill}'. Consider using exact term '{job_skill}'"
        elif score >= 0.5:
            return f"Related skill '{resume_skill}' found. Highlight connection to '{job_skill}'"
        else:
            return f"Missing skill. Consider adding '{job_skill}' if you have experience"

    def blueprint_step_2_semantic_keyword_analysis(self, resume: Resume, job_description: JobDescription) -> List[Dict]:
        """
        Advanced semantic keyword analysis using NLP and comparative analysis.
        Replaces the old keyword table with sophisticated skill matching.
        """
        try:
            # Extract skills from both sources
            job_skills = self._extract_skills_from_job_description(job_description)
            resume_skills = self._extract_skills_from_resume(resume)
            
            if not job_skills:
                return [{
                    "keyword": "No skills detected",
                    "found": False,
                    "priority": "High",
                    "confidence": 0,
                    "similarity_score": 0.0,
                    "action": "Review job description for technical requirements"
                }]
            
            # Find semantic matches
            matches = self._find_best_skill_matches(job_skills, resume_skills)
            
            # Convert to the expected format with enhanced information
            keyword_analysis = []
            for match in matches:
                # Determine priority based on skill importance and match quality
                priority = "High" if match['similarity_score'] < 0.5 else "Medium" if match['similarity_score'] < 0.8 else "Low"
                confidence = int(match['similarity_score'] * 100)
                
                keyword_analysis.append({
                    "keyword": match['job_skill'],
                    "found": match['found'],
                    "priority": priority,
                    "confidence": confidence,
                    "similarity_score": round(match['similarity_score'], 3),
                    "matched_skill": match['resume_skill'],
                    "context": match['context'][:80] + "..." if len(match['context']) > 80 else match['context'],
                    "source": match['source'],
                    "action": self._generate_skill_recommendations(match)
                })
            
            # Sort by priority (High first) then by similarity score (low first for gaps)
            priority_order = {"High": 0, "Medium": 1, "Low": 2}
            keyword_analysis.sort(key=lambda x: (priority_order[x['priority']], x['similarity_score']))
            
            return keyword_analysis[:8]  # Return top 8 most important matches
            
        except Exception as e:
            print(f"Error in semantic keyword analysis: {e}")
            return [{
                "keyword": "Analysis Error",
                "found": False,
                "priority": "High",
                "confidence": 0,
                "similarity_score": 0.0,
                "action": f"Error occurred: {str(e)[:50]}..."
            }]
