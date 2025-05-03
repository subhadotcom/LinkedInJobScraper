"""
LinkedIn Job Scraper module - Core scraping functionality
"""
import logging
import time
import random
import re
from urllib.parse import quote
from typing import List, Dict, Any, Optional

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from config import USER_AGENTS, RETRY_COUNT, DELAY_MIN, DELAY_MAX, LINKEDIN_BASE_URL
from utils import retry_with_backoff


class LinkedInJobScraper:
    """LinkedIn Job Scraper class for extracting job listings"""
    
    def __init__(self):
        """Initialize the scraper"""
        self.session = requests.Session()
        self.driver = None
        self.logger = logging.getLogger(__name__)
    
    def _setup_selenium(self):
        """Set up Selenium WebDriver with appropriate options"""
        if self.driver:
            self.logger.info("Reusing existing WebDriver")
            return
        
        self.logger.info("Setting up Selenium WebDriver")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_window_size(1920, 1080)
    
    def _close_selenium(self):
        """Close Selenium WebDriver"""
        if self.driver:
            self.logger.info("Closing Selenium WebDriver")
            self.driver.quit()
            self.driver = None
    
    def _rotate_user_agent(self):
        """Rotate user agent for requests"""
        user_agent = random.choice(USER_AGENTS)
        self.session.headers.update({'User-Agent': user_agent})
        self.logger.debug(f"Rotated user agent: {user_agent}")
        return user_agent
    
    @retry_with_backoff
    def _fetch_page(self, url: str) -> str:
        """Fetch a page using Selenium"""
        self._setup_selenium()
        self._rotate_user_agent()
        
        self.logger.info(f"Fetching page: {url}")
        
        # Add random delay to avoid detection
        delay = random.uniform(DELAY_MIN, DELAY_MAX)
        self.logger.debug(f"Waiting for {delay:.2f} seconds before request")
        time.sleep(delay)
        
        self.driver.get(url)
        
        # Wait for the job listings to load
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "jobs-search__results-list"))
            )
        except TimeoutException:
            self.logger.warning("Timeout waiting for job listings to load")
        
        return self.driver.page_source
    
    def _build_search_url(self, keywords: str, location: str = "", page: int = 0) -> str:
        """Build LinkedIn job search URL with parameters"""
        base_url = f"{LINKEDIN_BASE_URL}/jobs/search"
        
        # Format parameters
        params = []
        if keywords:
            params.append(f"keywords={quote(keywords)}")
        if location:
            params.append(f"location={quote(location)}")
        
        # Add pagination parameter (LinkedIn uses start instead of page)
        if page > 0:
            start = page * 25  # LinkedIn shows 25 jobs per page
            params.append(f"start={start}")
        
        # Combine URL parts
        url = f"{base_url}?{'&'.join(params)}"
        self.logger.debug(f"Built search URL: {url}")
        return url
    
    def _extract_job_listings(self, html: str) -> List[Dict[str, Any]]:
        """Extract job listings from HTML content"""
        self.logger.info("Extracting job listings from HTML")
        soup = BeautifulSoup(html, 'html.parser')
        job_cards = soup.select(".jobs-search__results-list li")
        
        self.logger.info(f"Found {len(job_cards)} job cards")
        jobs = []
        
        for card in job_cards:
            try:
                # Extract primary fields
                job_title_elem = card.select_one(".base-search-card__title")
                company_elem = card.select_one(".base-search-card__subtitle")
                location_elem = card.select_one(".job-search-card__location")
                link_elem = card.select_one("a.base-card__full-link")
                
                if not all([job_title_elem, company_elem, location_elem, link_elem]):
                    continue
                
                job_id = None
                job_url = link_elem.get('href', '')
                # Extract job ID from URL
                job_id_match = re.search(r'/view/(\d+)/', job_url)
                if job_id_match:
                    job_id = job_id_match.group(1)
                
                # Create job object
                job = {
                    'id': job_id,
                    'title': job_title_elem.text.strip(),
                    'company': company_elem.text.strip(),
                    'location': location_elem.text.strip(),
                    'url': job_url,
                    'description': '',  # Will be filled by detailed scraping
                    'date_posted': '',
                    'job_type': '',
                    'seniority_level': '',
                    'scraped_at': time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Extract date if available
                date_elem = card.select_one(".job-search-card__listdate")
                if date_elem:
                    job['date_posted'] = date_elem.get('datetime', '')
                
                jobs.append(job)
                
            except Exception as e:
                self.logger.error(f"Error extracting job listing: {str(e)}")
                continue
        
        return jobs
    
    @retry_with_backoff
    def _scrape_job_details(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape detailed job information"""
        if not job['url']:
            return job
        
        self.logger.info(f"Scraping job details for: {job['title']} at {job['company']}")
        
        try:
            self._setup_selenium()
            # Add random delay between requests
            delay = random.uniform(DELAY_MIN, DELAY_MAX)
            self.logger.debug(f"Waiting for {delay:.2f} seconds before request")
            time.sleep(delay)
            
            self.driver.get(job['url'])
            
            # Wait for job description to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "jobs-description__content"))
                )
            except TimeoutException:
                self.logger.warning("Timeout waiting for job description to load")
            
            # Extract job description
            try:
                description_elem = self.driver.find_element(By.CLASS_NAME, "jobs-description__content")
                job['description'] = description_elem.text.strip()
            except NoSuchElementException:
                self.logger.warning("Could not find job description element")
            
            # Extract additional details
            try:
                criteria_elements = self.driver.find_elements(By.CSS_SELECTOR, ".job-criteria__item")
                for criteria in criteria_elements:
                    try:
                        label = criteria.find_element(By.CSS_SELECTOR, ".job-criteria__subheader").text.strip()
                        value = criteria.find_element(By.CSS_SELECTOR, ".job-criteria__text").text.strip()
                        
                        if "seniority" in label.lower():
                            job['seniority_level'] = value
                        elif "type" in label.lower():
                            job['job_type'] = value
                    except NoSuchElementException:
                        continue
            except NoSuchElementException:
                self.logger.warning("Could not find job criteria elements")
            
        except WebDriverException as e:
            self.logger.error(f"Selenium error scraping job details: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error scraping job details: {str(e)}")
        
        return job
    
    def scrape_jobs(self, keywords: str, location: str = "", pages: int = 1, status_callback=None) -> List[Dict[str, Any]]:
        """
        Scrape job listings from LinkedIn
        
        Args:
            keywords: Search keywords
            location: Job location
            pages: Number of pages to scrape
            status_callback: Callback function to update scraping status
            
        Returns:
            List of job listings
        """
        self.logger.info(f"Starting job scraping for '{keywords}' in '{location}'")
        all_jobs = []
        
        try:
            self._setup_selenium()
            
            # Iterate through pages
            for page in range(pages):
                self.logger.info(f"Scraping page {page+1} of {pages}")
                url = self._build_search_url(keywords, location, page)
                
                # Update status if callback is provided
                if status_callback:
                    status_callback(page+1, len(all_jobs))
                
                # Fetch page and extract listings
                html = self._fetch_page(url)
                page_jobs = self._extract_job_listings(html)
                self.logger.info(f"Found {len(page_jobs)} jobs on page {page+1}")
                
                # Get detailed information for each job
                for i, job in enumerate(page_jobs):
                    self.logger.info(f"Getting details for job {i+1} of {len(page_jobs)} on page {page+1}")
                    detailed_job = self._scrape_job_details(job)
                    all_jobs.append(detailed_job)
                    
                    # Update status if callback is provided
                    if status_callback:
                        status_callback(page+1, len(all_jobs))
                
                # Check if we need to continue to the next page
                if len(page_jobs) < 24:  # LinkedIn typically shows 25 results per page
                    self.logger.info(f"Found less than 25 jobs on page {page+1}, stopping pagination")
                    break
        
        finally:
            self._close_selenium()
        
        self.logger.info(f"Completed scraping. Total jobs found: {len(all_jobs)}")
        return all_jobs
