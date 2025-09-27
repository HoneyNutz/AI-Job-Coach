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

    def parse_job_description_with_llm(self, text: str) -> JobDescription:
        """
        Uses an LLM to parse raw text into a structured JobDescription object.
        
        NOTE: This is a placeholder. The actual implementation will call the GenerationAgent.
        
        Args:
            text: The raw text of the job description.

        Returns:
            A JobDescription object.
        """
        # Placeholder logic:
        # In the full implementation, this will make a call to the GenerationAgent
        # to extract entities like position, company, summary, and highlights.
        # For example:
        # extracted_data = self.generation_agent.extract_job_details(text)
        # return JobDescription(**extracted_data)
        
        return JobDescription(summary=text)

    def process_job_url(self, url: str) -> JobDescription:
        """
        Orchestrates the scraping and parsing of a job description from a URL.

        Args:
            url: The URL of the job posting.

        Returns:
            A structured JobDescription object.
        """
        raw_text = self.scrape_job_description(url)
        if raw_text:
            return self.parse_job_description_with_llm(raw_text)
        return JobDescription()

    def process_raw_text(self, text: str) -> JobDescription:
        """
        Processes raw job description text directly.

        Args:
            text: The raw text of the job description.

        Returns:
            A structured JobDescription object.
        """
        if text:
            return self.parse_job_description_with_llm(text)
        return JobDescription()

    def scrape_company_homepage(self, url: str) -> str:
        """
        Scrapes the primary text content from a company's homepage.
        """
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            # A simple heuristic to get main content, avoiding navs, footers, etc.
            main_content = soup.find('main') or soup.find('body')
            if main_content:
                return ' '.join(main_content.get_text(separator=' ', strip=True).split()[:1000]) # Limit to ~1000 words
            return ""
        except requests.exceptions.RequestException as e:
            print(f"Error fetching company homepage: {e}")
            return ""
