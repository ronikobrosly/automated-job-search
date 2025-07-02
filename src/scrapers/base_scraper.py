"""
Base scraper class with anti-detection features and robust error handling.
"""

import time
import random
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Generator
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.sites import SiteConfig

class AntiDetectionMixin:
    """Mixin class for anti-detection features"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = None
        self._setup_session()
    
    def _setup_session(self):
        """Set up a requests session with retry strategy and anti-detection features"""
        self.session = requests.Session()
        
        # Retry strategy with exponential backoff
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=2,  # Exponential backoff: 2, 4, 8 seconds
            raise_on_status=False
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def _get_random_user_agent(self) -> str:
        """Get a random user agent string"""
        try:
            return self.ua.random
        except Exception:
            # Fallback user agents if fake_useragent fails
            fallback_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0'
            ]
            return random.choice(fallback_agents)
    
    def _get_random_headers(self, base_headers: Dict[str, str] = None) -> Dict[str, str]:
        """Generate randomized headers to avoid detection"""
        headers = base_headers.copy() if base_headers else {}
        
        # Always randomize user agent
        headers['User-Agent'] = self._get_random_user_agent()
        
        # Add some random variation to other headers
        accept_languages = [
            'en-US,en;q=0.9',
            'en-US,en;q=0.8,es;q=0.7',
            'en-GB,en;q=0.9',
            'en-US,en;q=0.5'
        ]
        headers['Accept-Language'] = random.choice(accept_languages)
        
        # Random accept encoding
        encodings = [
            'gzip, deflate, br',
            'gzip, deflate',
            'identity'
        ]
        headers['Accept-Encoding'] = random.choice(encodings)
        
        return headers
    
    def _random_delay(self, delay_range: tuple):
        """Sleep for a random amount of time within the given range"""
        min_delay, max_delay = delay_range
        delay = random.uniform(min_delay, max_delay)
        logging.info(f"Sleeping for {delay:.2f} seconds")
        time.sleep(delay)
    
    def _make_request(self, url: str, headers: Dict[str, str] = None, timeout: int = 30) -> Optional[requests.Response]:
        """Make a request with error handling and retries"""
        try:
            response = self.session.get(
                url,
                headers=self._get_random_headers(headers),
                timeout=timeout,
                allow_redirects=True
            )
            
            # Check for rate limiting or blocking
            if response.status_code == 429:
                logging.warning(f"Rate limited on {url}. Status: {response.status_code}")
                # Exponential backoff for rate limiting
                backoff_time = random.uniform(30, 60)
                logging.info(f"Backing off for {backoff_time:.2f} seconds")
                time.sleep(backoff_time)
                return None
            
            if response.status_code in [403, 429, 503]:
                logging.warning(f"Potential blocking detected on {url}. Status: {response.status_code}")
                return None
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for {url}: {str(e)}")
            return None
    
    def _make_detail_request(self, url: str, delay_range: tuple = None) -> Optional[requests.Response]:
        """Make a request for job detail page with appropriate delays"""
        if delay_range:
            self._random_delay(delay_range)
        return self._make_request(url)

class BaseScraper(AntiDetectionMixin, ABC):
    """Base scraper class with common scraping functionality"""
    
    def __init__(self, site_config: SiteConfig):
        super().__init__()
        self.config = site_config
        self.logger = logging.getLogger(f"scraper.{self.config.name.lower()}")
        
        # Track scraping statistics
        self.stats = {
            'pages_scraped': 0,
            'jobs_found': 0,
            'errors': 0,
            'rate_limited': 0
        }
    
    @abstractmethod
    def parse_job_listing(self, job_element, page_url: str) -> Optional[Dict[str, Any]]:
        """Parse a single job listing element into structured data"""
        pass
    
    @abstractmethod
    def get_job_elements(self, soup: BeautifulSoup) -> List[Any]:
        """Extract job listing elements from the page soup"""
        pass
    
    @abstractmethod
    def has_next_page(self, soup: BeautifulSoup, current_page: int) -> bool:
        """Determine if there are more pages to scrape"""
        pass
    
    def supports_detail_pages(self) -> bool:
        """Override to return True if scraper can extract detailed job pages"""
        return False
    
    def extract_job_details(self, job_url: str) -> Optional[Dict[str, Any]]:
        """Override to extract comprehensive details from individual job pages"""
        if not self.supports_detail_pages():
            return None
        raise NotImplementedError("Implement if supports_detail_pages returns True")
    
    def get_page_url(self, page_number: int) -> str:
        """Generate URL for a specific page"""
        if '{page}' in self.config.search_url:
            return self.config.search_url.format(page=page_number)
        elif '{start}' in self.config.search_url:
            # For sites that use start offset instead of page number
            start = (page_number - 1) * 10  # Assuming 10 results per page
            return self.config.search_url.format(start=start)
        else:
            # Fallback: append page parameter
            separator = '&' if '?' in self.config.search_url else '?'
            return f"{self.config.search_url}{separator}{self.config.pagination_param}={page_number}"
    
    def scrape_page(self, page_number: int) -> List[Dict[str, Any]]:
        """Scrape a single page and return job listings"""
        url = self.get_page_url(page_number)
        self.logger.info(f"Scraping page {page_number}: {url}")
        
        # Random delay before request
        if page_number > 1:  # Don't delay on first page
            self._random_delay(self.config.delay_range)
        
        response = self._make_request(url, self.config.headers, self.config.timeout)
        
        if not response:
            self.stats['errors'] += 1
            return []
        
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            job_elements = self.get_job_elements(soup)
            
            jobs = []
            for job_element in job_elements:
                try:
                    job_data = self.parse_job_listing(job_element, url)
                    if job_data:
                        job_data['job_website'] = self.config.name.lower()
                        job_data['scraped_from_url'] = url
                        
                        # Extract detailed job information if supported
                        if self.supports_detail_pages() and 'job_url' in job_data:
                            try:
                                detail_delay = getattr(self.config, 'detail_delay_range', self.config.delay_range)
                                details = self.extract_job_details(job_data['job_url'])
                                if details:
                                    job_data['additional_data'] = details
                                    # Add delay after detail extraction
                                    self._random_delay(detail_delay)
                            except Exception as e:
                                self.logger.warning(f"Failed to extract details for {job_data.get('job_url', 'unknown')}: {e}")
                                # Continue with basic job data
                        
                        jobs.append(job_data)
                except Exception as e:
                    self.logger.error(f"Error parsing job element: {str(e)}")
                    continue
            
            self.stats['pages_scraped'] += 1
            self.stats['jobs_found'] += len(jobs)
            self.logger.info(f"Found {len(jobs)} jobs on page {page_number}")
            
            return jobs
            
        except Exception as e:
            self.logger.error(f"Error parsing page {page_number}: {str(e)}")
            self.stats['errors'] += 1
            return []
    
    def scrape_all_pages(self) -> Generator[List[Dict[str, Any]], None, None]:
        """Scrape all pages and yield job listings"""
        self.logger.info(f"Starting scrape of {self.config.name}")
        
        current_page = self.config.pagination_start
        max_pages = self.config.max_pages
        
        while current_page <= max_pages:
            try:
                jobs = self.scrape_page(current_page)
                
                if not jobs:
                    self.logger.warning(f"No jobs found on page {current_page}, stopping")
                    break
                
                yield jobs
                
                # Check if we should continue to next page
                # This is a simple approach - some scrapers might need more sophisticated logic
                if len(jobs) == 0:
                    break
                
                current_page += 1
                
            except KeyboardInterrupt:
                self.logger.info("Scraping interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error on page {current_page}: {str(e)}")
                self.stats['errors'] += 1
                current_page += 1
                
                # Stop if too many consecutive errors
                if self.stats['errors'] > 5:
                    self.logger.error("Too many errors, stopping scrape")
                    break
        
        self.logger.info(f"Scraping completed. Stats: {self.stats}")
    
    def get_stats(self) -> Dict[str, int]:
        """Get scraping statistics"""
        return self.stats.copy()