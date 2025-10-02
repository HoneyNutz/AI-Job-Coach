import requests
from bs4 import BeautifulSoup
from .data_agent import JobDescription
from typing import Dict, Tuple, Optional

class ScraperAgent:
    def __init__(self):
        # In the future, we might initialize the GenerationAgent here
        # self.generation_agent = GenerationAgent()
        pass

    def scrape_job_description(self, url: str) -> str:
        """
        Scrapes the job description text from a given URL.

        Args:
            url: The URL of the job posting.

        Returns:
            The raw text of the job description, or an empty string if scraping fails.
        """
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()  # Raise an exception for bad status codes
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # A simple heuristic to find the main job description content.
            # This can be improved with more sophisticated selectors.
            text_elements = soup.find_all(['p', 'li', 'h1', 'h2', 'h3', 'div'])
            job_text = ' '.join(element.get_text(separator=' ', strip=True) for element in text_elements)
            
            # A more robust approach might try to find a specific container
            # for job descriptions, which varies by site.
            # For example: job_container = soup.find('div', class_='job-description')

            return job_text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL: {e}")
            return ""

    def structure_from_text(self, text: str, generation_agent) -> Dict:
        """
        Structures a raw job description text into the enhanced schema via GenerationAgent.

        Note: Pass an initialized GenerationAgent instance. We avoid importing it here to prevent cycles.
        """
        if not text or not text.strip():
            return {}
        try:
            return generation_agent.structure_job_description_schema_v1(text)
        except Exception as e:
            print(f"Error structuring job description text: {e}")
            return {}

    def structure_from_url(self, url: str, generation_agent) -> Tuple[str, Dict]:
        """
        Fetches a job posting from a URL and returns a tuple of (raw_text, structured_json).

        - raw_text: combined extracted text from the page
        - structured_json: output of GenerationAgent.structure_job_description_schema_v1(raw_text)
        """
        raw = self.scrape_job_description(url)
        structured = {}
        if raw:
            try:
                structured = generation_agent.structure_job_description_schema_v1(raw)
            except Exception as e:
                print(f"Error structuring job description from URL: {e}")
        return raw, structured

