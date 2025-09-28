import requests
from bs4 import BeautifulSoup
from .data_agent import JobDescription
# The generation_agent will be used for advanced parsing.
# from .generation_agent import GenerationAgent

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

