from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict

from .data_agent import Resume, JobDescription


class BlueprintOrchestrator:
    """
    Coordinates blueprint generation steps using the existing GenerationAgent.
    Steps 1-3 run in parallel; step 4 processes achievements per bullet.
    """

    def __init__(self, generation_agent):
        self.gen = generation_agent

    def generate_blueprint(
        self,
        resume: Resume,
        job_description: JobDescription,
        progress: Callable[[str], None] | None = None,
    ) -> Dict:
        parts: Dict = {
            "assessment": {},
            "keyword_table": [],
            "editable_summary": "",
            "achievements": {},
        }

        def notify(msg: str):
            if progress:
                try:
                    progress(msg)
                except Exception:
                    pass

        # Steps 1-3 in parallel
        notify("Step 1/4: Performing strategic assessment...")
        notify("Step 2/4: Performing semantic skill analysis...")
        notify("Step 3/4: Rewriting professional summary...")

        with ThreadPoolExecutor(max_workers=3) as ex:
            fut1 = ex.submit(self.gen.blueprint_step_1_strategic_assessment, resume, job_description)
            fut2 = ex.submit(self.gen.blueprint_step_2_semantic_keyword_analysis, resume, job_description)
            fut3 = ex.submit(self.gen.blueprint_step_3_summary, resume, job_description)

            for fut in as_completed([fut1, fut2, fut3]):
                if fut is fut1:
                    parts["assessment"] = fut.result()
                elif fut is fut2:
                    parts["keyword_table"] = fut.result()
                else:
                    parts["editable_summary"] = fut.result()

        # Step 4: achievements per bullet
        notify("Step 4/4: Rewriting achievement bullet points...")
        if resume.work:
            for i, work_item in enumerate(resume.work):
                if not getattr(work_item, "highlights", None):
                    continue
                for j, highlight in enumerate(work_item.highlights):
                    key = f"{i}_{j}"
                    result = self.gen.blueprint_step_4_achievements(highlight, work_item.name, job_description)
                    if isinstance(result, dict) and 'error' not in result:
                        parts["achievements"][key] = {
                            "original_bullet": result.get("original_bullet") or highlight,
                            "optimized_bullet": result.get("optimized_bullet") or highlight,
                            "rationale": result.get("rationale") or "Optimized using STAR-D principles based on the target role.",
                        }

        return parts
