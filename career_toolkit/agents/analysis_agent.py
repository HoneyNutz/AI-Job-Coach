from sentence_transformers import SentenceTransformer, util
from .data_agent import Resume, JobDescription
from typing import Dict, Any, List

class AnalysisAgent:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initializes the AnalysisAgent with a sentence-transformer model.
        """
        self.model = SentenceTransformer(model_name)

    def analyze(self, resume: Resume, job_description: JobDescription) -> Dict[str, Any]:
        """
        Performs a semantic analysis of the resume against the job description.

        Args:
            resume: The user's resume as a Pydantic object.
            job_description: The job description as a Pydantic object.

            A dictionary containing the analysis results, including scores and recommendations.
        """
        if not resume or not job_description:
            return {"error": "Resume or Job Description not provided."}

        # 1. Vectorize Resume Experiences and Job Requirements
        # Create a structured list of resume experiences with their text and source
        resume_experiences = []
        if resume.basics and resume.basics.summary:
            resume_experiences.append({
                "source": "Overall Summary",
                "text": resume.basics.summary
            })
        for work in resume.work:
            text = f"{work.position} at {work.name}. {work.summary or ''} Highlights: {' '.join(work.highlights or [])}"
            resume_experiences.append({
                "source": f"{work.position} at {work.name}",
                "text": text.strip()
            })

        # Flatten all job requirements into a single list
        job_requirements = (
            job_description.responsibilities + 
            job_description.qualifications + 
            job_description.educationRequirements + 
            job_description.experienceRequirements
        )
        if job_description.skills:
            job_requirements.append(f"Key skills include: {job_description.skills}")

        if not resume_experiences or not job_requirements:
            return {"error": "Not enough content to perform analysis."}

        # 2. Generate embeddings for all items
        resume_texts = [exp['text'] for exp in resume_experiences]
        resume_embeddings = self.model.encode(resume_texts, convert_to_tensor=True)
        job_embeddings = self.model.encode(job_requirements, convert_to_tensor=True)

        # 3. For each job requirement, find the best matching resume experience
        cosine_scores = util.cos_sim(job_embeddings, resume_embeddings)

        match_results = []
        total_score = 0
        for i, req in enumerate(job_requirements):
            best_match_score, best_match_idx = cosine_scores[i].max(dim=0)
            best_match_score = best_match_score.item()
            best_match_idx = best_match_idx.item()
            
            matched_experience = resume_experiences[best_match_idx]

            recommendation = self._generate_recommendation(req, matched_experience['text'], best_match_score)

            match_results.append({
                "job_requirement": req,
                "best_resume_match": matched_experience['text'],
                "nearest_experience": matched_experience['source'],
                "confidence_score": best_match_score,
                "recommendation": recommendation
            })
            total_score += best_match_score
        
        overall_score = (total_score / len(job_requirements)) if job_requirements else 0

        return {
            "overall_score": f"{overall_score:.2%}",
            "match_results": sorted(match_results, key=lambda x: x['confidence_score'])
        }

    def _generate_recommendation(self, requirement: str, resume_text: str, score: float) -> str:
        """Generates a targeted recommendation based on the match score."""
        if score > 0.75:
            return "Strong match. Ensure this experience is highlighted prominently."
        elif score > 0.5:
            return f"Good match. Consider tailoring the language in your resume to more closely mirror the keywords in the requirement: '{requirement[:50]}...'"
        else:
            return f"Weak match. This is a potential gap. Consider adding a project or highlighting a different aspect of your experience that addresses: '{requirement[:50]}...'"
