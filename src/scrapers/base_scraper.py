"""
Base scraper class with anti-detection features and robust error handling.
"""

import logging
import random
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from requests.adapters import HTTPAdapter
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from urllib3.util.retry import Retry
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

from config.sites.sites_config import SiteConfig

class SeleniumMixin:
    """Mixin class for Selenium-based scraping with anti-detection features.
    
    Provides functionality for browser automation with stealth features
    to avoid detection by anti-bot systems.
    """
    
    def __init__(self) -> None:
        """Initialize the Selenium mixin with driver setup."""
        self.driver = None
        self.wait = None
        self.ua = UserAgent()
        self._setup_driver()
    
    def _setup_driver(self, browser: str = 'chrome', headless: bool = True):
        """Set up Selenium WebDriver with anti-detection measures"""
        try:
            if browser.lower() == 'chrome':
                self.driver = self._setup_chrome_driver(headless)
            elif browser.lower() == 'firefox':
                self.driver = self._setup_firefox_driver(headless)
            else:
                raise ValueError(f"Unsupported browser: {browser}")
            
            # Set up WebDriverWait
            self.wait = WebDriverWait(self.driver, 10)
            
            # AIDEV-NOTE: Set window size to avoid detection
            self.driver.set_window_size(1920, 1080)
            
            logging.info(f"Successfully initialized {browser} driver")
            
        except Exception as e:
            logging.error(f"Failed to setup WebDriver: {str(e)}")
            raise
    
    def _setup_chrome_driver(self, headless: bool = True) -> webdriver.Chrome:
        """Set up Chrome WebDriver with anti-detection options"""
        chrome_options = ChromeOptions()
        chrome_options.binary_location = "/usr/bin/google-chrome"
        
        if headless:
            chrome_options.add_argument('--headless=new')  # Use new headless mode
        
        # AIDEV-NOTE: Enhanced anti-detection measures for Chrome
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        # AIDEV-NOTE: Removed --disable-images for React apps that may need images for layout
        # chrome_options.add_argument('--disable-images')  # Faster loading
        
        # Additional stealth options
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--disable-popup-blocking')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-sync')
        chrome_options.add_argument('--disable-translate')
        chrome_options.add_argument('--hide-scrollbars')
        chrome_options.add_argument('--mute-audio')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--no-default-browser-check')
        chrome_options.add_argument('--disable-component-update')
        chrome_options.add_argument('--disable-domain-reliability')
        chrome_options.add_argument('--disable-client-side-phishing-detection')
        
        # Set random user agent
        user_agent = self._get_random_user_agent()
        chrome_options.add_argument(f'--user-agent={user_agent}')
        
        # Additional stealth options
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--disable-features=TranslateUI')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # AIDEV-NOTE: Advanced stealth JavaScript execution to mask automation
        stealth_js = """
        // Hide webdriver property
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        
        // Hide automation indicators
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
        
        // Override permissions API
        const originalQuery = window.navigator.permissions.query;
        return window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Cypress.isDenied }) :
                originalQuery(parameters)
        );
        
        // Hide chrome runtime
        delete window.chrome;
        
        // Mock chrome object
        window.chrome = {
            runtime: {}
        };
        
        // Override console.debug
        const originalDebug = console.debug;
        console.debug = function() {};
        """
        
        try:
            driver.execute_script(stealth_js)
        except Exception as e:
            logging.warning(f"Failed to execute stealth JavaScript: {e}")
        
        return driver
    
    def _setup_firefox_driver(self, headless: bool = True) -> webdriver.Firefox:
        """Set up Firefox WebDriver with anti-detection options"""
        firefox_options = FirefoxOptions()
        
        if headless:
            firefox_options.add_argument('--headless')
        
        # AIDEV-NOTE: Anti-detection measures for Firefox
        firefox_options.add_argument('--disable-gpu')
        firefox_options.add_argument('--no-sandbox')
        
        # Set random user agent
        user_agent = self._get_random_user_agent()
        firefox_options.set_preference('general.useragent.override', user_agent)
        
        # Additional stealth preferences
        firefox_options.set_preference('dom.webdriver.enabled', False)
        firefox_options.set_preference('useAutomationExtension', False)
        firefox_options.set_preference('permissions.default.image', 2)  # Block images
        
        service = FirefoxService(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=firefox_options)
        
        return driver
    
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
    
    def _selenium_get_page(self, url: str, wait_for_element: str = None, wait_time: int = 10) -> Optional[BeautifulSoup]:
        """Load a page with Selenium and return BeautifulSoup object"""
        try:
            logging.info(f"Loading page with Selenium: {url}")
            
            # Navigate to the page
            self.driver.get(url)
            
            # AIDEV-NOTE: Enhanced realistic behavior to avoid detection
            # Random initial wait
            time.sleep(random.uniform(1.5, 3.0))
            
            # Simulate human-like mouse movement
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(self.driver)
                # Move mouse to a random position
                actions.move_by_offset(random.randint(100, 800), random.randint(100, 600))
                actions.perform()
            except Exception:
                pass  # Ignore if ActionChains fails
            
            # Wait for page to stabilize
            time.sleep(random.uniform(1, 2))
            
            # Wait for specific element if provided
            if wait_for_element:
                try:
                    # AIDEV-NOTE: Enhanced waiting for React/SPA applications
                    # First try to wait for the specific element
                    WebDriverWait(self.driver, wait_time).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element))
                    )
                    logging.info(f"Successfully found wait element: {wait_for_element}")
                except TimeoutException:
                    logging.warning(f"Timeout waiting for element: {wait_for_element}")
                    # For React apps, try waiting for common React indicators
                    try:
                        # Wait for React root div to have content
                        WebDriverWait(self.driver, 10).until(
                            lambda driver: driver.execute_script(
                                "return document.querySelector('#root') && document.querySelector('#root').children.length > 0"
                            )
                        )
                        logging.info("React root has content, waiting additional time for job listings")
                        # Additional wait for job content to load
                        time.sleep(5)
                    except TimeoutException:
                        logging.warning("React root check failed, trying generic body wait")
                        # Try waiting for any visible element as fallback
                        try:
                            WebDriverWait(self.driver, 5).until(
                                EC.presence_of_element_located((By.TAG_NAME, "body"))
                            )
                        except TimeoutException:
                            logging.warning("Even body element not found, proceeding anyway")
            
            # Additional wait for JavaScript to complete
            time.sleep(random.uniform(1, 2))
            
            # Get page source and create BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            return soup
            
        except WebDriverException as e:
            logging.error(f"WebDriver error loading {url}: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error loading {url}: {str(e)}")
            return None
    
    def _selenium_random_delay(self, delay_range: tuple):
        """Sleep for a random amount of time within the given range"""
        min_delay, max_delay = delay_range
        delay = random.uniform(min_delay, max_delay)
        logging.info(f"Selenium delay: {delay:.2f} seconds")
        time.sleep(delay)
    
    def _selenium_scroll_page(self, pause_time: float = 1.0):
        """Scroll the page to trigger any lazy loading"""
        try:
            # Scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(pause_time)
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(pause_time)
            
        except Exception as e:
            logging.warning(f"Error scrolling page: {str(e)}")
    
    def close_driver(self):
        """Close the WebDriver instance"""
        if self.driver:
            try:
                self.driver.quit()
                logging.info("WebDriver closed successfully")
            except Exception as e:
                logging.error(f"Error closing WebDriver: {str(e)}")
            finally:
                self.driver = None
                self.wait = None
    
    def __del__(self):
        """Ensure driver is closed when object is destroyed"""
        self.close_driver()


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


class SeleniumBaseScraper(SeleniumMixin, AntiDetectionMixin, ABC):
    """Base scraper class with Selenium support for JavaScript-heavy sites"""
    
    def __init__(self, site_config: SiteConfig):
        SeleniumMixin.__init__(self)
        AntiDetectionMixin.__init__(self)
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
        """Scrape a single page using Selenium and return job listings"""
        url = self.get_page_url(page_number)
        self.logger.info(f"Scraping page {page_number} with Selenium: {url}")
        
        # Random delay before request
        if page_number > 1:  # Don't delay on first page
            self._selenium_random_delay(self.config.delay_range)
        
        # AIDEV-NOTE: Use Selenium to load the page and wait for job elements
        soup = self._selenium_get_page(url, wait_for_element=self._get_wait_element())
        
        if not soup:
            self.stats['errors'] += 1
            return []
        
        try:
            # Optional: Scroll to trigger lazy loading
            self._selenium_scroll_page()
            
            # Re-get page source after scrolling
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
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
                                    self._selenium_random_delay(detail_delay)
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
    
    def _get_wait_element(self) -> str:
        """Return CSS selector for element to wait for - override in subclasses"""
        return "div"  # Default fallback
    
    def scrape_all_pages(self) -> Generator[List[Dict[str, Any]], None, None]:
        """Scrape all pages using Selenium and yield job listings"""
        self.logger.info(f"Starting Selenium scrape of {self.config.name}")
        
        try:
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
        
        finally:
            # Always close the driver when done
            self.close_driver()
        
        self.logger.info(f"Scraping completed. Stats: {self.stats}")
    
    def extract_job_details(self, job_url: str) -> Optional[Dict[str, Any]]:
        """Extract comprehensive details from individual job pages using Selenium"""
        if not self.supports_detail_pages():
            return None
        
        try:
            self.logger.info(f"Extracting details with Selenium from: {job_url}")
            
            # Use Selenium to load the detail page
            soup = self._selenium_get_page(job_url, wait_for_element=self._get_detail_wait_element())
            
            if not soup:
                self.logger.warning(f"Failed to fetch job details from {job_url}")
                return None
            
            # Let subclasses handle the actual detail extraction
            return self._extract_job_details_from_soup(soup)
            
        except Exception as e:
            self.logger.error(f"Error extracting job details from {job_url}: {str(e)}")
            return None
    
    def _get_detail_wait_element(self) -> str:
        """Return CSS selector for element to wait for on detail pages - override in subclasses"""
        return "div"  # Default fallback
    
    def _extract_job_details_from_soup(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract job details from soup - override in subclasses"""
        return None
    
    def get_stats(self) -> Dict[str, int]:
        """Get scraping statistics"""
        return self.stats.copy()
    
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