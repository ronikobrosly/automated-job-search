"""
Hirebase.org specific scraper implementation.
"""

import re
import logging
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin, urlparse

from ..base_scraper import SeleniumBaseScraper
from config.sites.sites_config import SiteConfig

class HirebaseScraper(SeleniumBaseScraper):
    """Scraper for hirebase.org job listings"""
    
    def __init__(self, site_config: SiteConfig):
        super().__init__(site_config)
        self.logger = logging.getLogger("scraper.hirebase")
        
        # AIDEV-NOTE: Hirebase-specific configuration for Selenium
        self.job_card_selector = 'div.mb-4 > div.bg-white.rounded-xl.p-6'
        self.job_title_selector = 'a.group h2'
        self.company_selector = 'a[href^="/company/"] h3'
        self.location_selector = 'div.flex.items-center.gap-1:has(svg.lucide-map-pin) span'
    
    def get_job_elements(self, soup: BeautifulSoup) -> List[Tag]:
        """Extract job listing elements from the page soup"""
        # AIDEV-NOTE: Hirebase uses specific structure: div.mb-4 > div.bg-white.rounded-xl for job containers
        job_elements = soup.select(self.job_card_selector)
        
        if not job_elements:
            # Fallback: try broader selector for the job cards
            job_elements = soup.select('div.bg-white.rounded-xl:has(h2)')
        
        if not job_elements:
            # Second fallback: look for any white rounded cards that contain job titles
            job_elements = soup.select('div.bg-white:has(a[href*="/company/"][href*="/jobs/"])')
        
        if not job_elements:
            # Third fallback: try even broader selectors for job cards
            job_elements = soup.select('div.bg-white.rounded-xl, div.bg-white.rounded, div[class*="job"], div[class*="card"]')
        
        if not job_elements:
            # Fourth fallback: look for any divs with job-related content
            job_elements = soup.select('div:contains("engineer"), div:contains("developer"), div:contains("manager")')
        
        self.logger.info(f"Found {len(job_elements)} job elements using Hirebase-specific selectors")
        return job_elements
    
    def _wait_for_page_load(self):
        """Wait for the React app to fully load with job content"""
        try:
            # AIDEV-NOTE: Enhanced waiting specifically for Hirebase React app
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By
            
            # Wait for React to finish loading
            WebDriverWait(self.driver, 15).until(
                lambda driver: driver.execute_script(
                    "return document.readyState === 'complete' && "
                    "document.querySelector('#root') && "
                    "document.querySelector('#root').children.length > 0"
                )
            )
            self.logger.info("React app loaded, waiting for job content...")
            
            # Wait a bit more for job content to load
            import time
            time.sleep(3)
            
            # Try to wait for job cards to appear
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.bg-white.rounded-xl, [data-testid="job-card"], .job-card'))
                )
                self.logger.info("Job cards found!")
            except:
                self.logger.warning("Job cards not found with standard selectors, proceeding anyway")
                
        except Exception as e:
            self.logger.warning(f"Error waiting for page load: {e}")
            import time
            time.sleep(5)  # Fallback wait
    
    def parse_job_listing(self, job_element: Tag, page_url: str) -> Optional[Dict[str, Any]]:
        """Parse a single job listing element into structured data"""
        try:
            job_data = {}
            
            # Extract text content for analysis
            text_content = job_element.get_text(strip=True)
            
            if not text_content or len(text_content) < 20:
                return None
            
            # Try to find job title - look for common patterns
            job_title = self._extract_job_title(job_element)
            if not job_title:
                return None
            
            job_data['role_title'] = job_title
            
            # Extract company name
            company_name = self._extract_company_name(job_element)
            job_data['company_name'] = company_name
            
            # Extract location
            location = self._extract_location(job_element)
            job_data['location'] = location
            
            # Extract job URL
            job_url = self._extract_job_url(job_element, page_url)
            job_data['job_url'] = job_url
            
            # Use job URL or a combination of fields as job_id
            if job_url:
                job_data['job_id'] = self._generate_job_id(job_url)
            else:
                job_data['job_id'] = self._generate_job_id(f"{company_name}_{job_title}")
            
            # Extract job description/requirements
            description = self._extract_description(job_element)
            job_data['job_description'] = description
            job_data['requirements'] = description  # For now, same as description
            
            # Extract salary if available
            salary = self._extract_salary(job_element)
            job_data['salary_range'] = salary
            
            self.logger.debug(f"Parsed job: {job_title} at {company_name}")
            return job_data
            
        except Exception as e:
            self.logger.error(f"Error parsing job element: {str(e)}")
            return None
    
    def _extract_job_title(self, element: Tag) -> Optional[str]:
        """Extract job title from element using Hirebase-specific structure"""
        # AIDEV-NOTE: Hirebase uses a.group h2 for job titles
        title_elem = element.select_one('a.group h2')
        if title_elem and title_elem.get_text(strip=True):
            return title_elem.get_text(strip=True)
        
        # Fallback: try any h2 in a link
        title_elem = element.select_one('a h2')
        if title_elem and title_elem.get_text(strip=True):
            return title_elem.get_text(strip=True)
        
        # Second fallback: try any h2
        title_elem = element.select_one('h2')
        if title_elem and title_elem.get_text(strip=True):
            return title_elem.get_text(strip=True)
        
        return None
    
    def _looks_like_job_title(self, text: str) -> bool:
        """Check if text looks like a job title"""
        if not text or len(text) < 5 or len(text) > 100:
            return False
        
        # Common job title keywords
        job_keywords = [
            'engineer', 'scientist', 'developer', 'analyst', 'manager', 'director',
            'specialist', 'consultant', 'architect', 'lead', 'senior', 'junior',
            'data', 'machine learning', 'ai', 'artificial intelligence', 'ml',
            'software', 'backend', 'frontend', 'fullstack', 'devops', 'cloud'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in job_keywords)
    
    def _extract_company_name(self, element: Tag) -> Optional[str]:
        """Extract company name from element using Hirebase-specific structure"""
        # AIDEV-NOTE: Hirebase uses a[href^="/company/"] h3 for company names
        company_elem = element.select_one('a[href^="/company/"] h3')
        if company_elem and company_elem.get_text(strip=True):
            return company_elem.get_text(strip=True)
        
        # Fallback: try any h3 that looks like a company name
        h3_elements = element.select('h3')
        for h3 in h3_elements:
            text = h3.get_text(strip=True)
            if text and not self._looks_like_job_title(text):
                return text
        
        return "Unknown Company"
    
    def _extract_location(self, element: Tag) -> Optional[str]:
        """Extract location from element using Hirebase-specific structure"""
        # AIDEV-NOTE: Hirebase uses div.flex.items-center.gap-1:has(svg.lucide-map-pin) span for location
        location_elem = element.select_one('div.flex.items-center.gap-1:has(svg.lucide-map-pin) span')
        if location_elem and location_elem.get_text(strip=True):
            return location_elem.get_text(strip=True)
        
        # Fallback: look for any span near a map pin icon
        map_pin_parent = element.select_one('svg.lucide-map-pin')
        if map_pin_parent:
            parent_div = map_pin_parent.find_parent('div')
            if parent_div:
                location_span = parent_div.find('span')
                if location_span:
                    return location_span.get_text(strip=True)
        
        # Second fallback: search for location patterns in text
        text_content = element.get_text()
        location_patterns = [
            r'\b[A-Z][a-z]+,\s*[A-Z][a-z\s]+,\s*[A-Z][a-z\s]+\b',  # City, State, Country
            r'\b[A-Z][a-z]+,\s*[A-Z]{2}\b',  # City, ST
            r'\bRemote\b',
            r'\bHybrid\b'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text_content)
            if match:
                return match.group().strip()
        
        return None
    
    def _extract_job_url(self, element: Tag, page_url: str) -> Optional[str]:
        """Extract job URL from element using Hirebase-specific structure"""
        # AIDEV-NOTE: Hirebase uses a.group[href^="/company/"] for job detail links
        job_link = element.select_one('a.group[href^="/company/"]')
        if job_link and job_link.get('href'):
            href = job_link.get('href')
            return urljoin(self.config.base_url, href)
        
        # Fallback: look for any link to company job pages
        job_links = element.select('a[href*="/company/"][href*="/jobs/"]')
        for link in job_links:
            href = link.get('href')
            if href:
                return urljoin(self.config.base_url, href)
        
        return None
    
    def _extract_description(self, element: Tag) -> str:
        """Extract job description from element using Hirebase-specific structure"""
        # AIDEV-NOTE: Hirebase has About and Requirements sections in job listings
        description_parts = []
        
        # Extract About section
        about_header = element.find('h4', string=lambda text: 'About' in text if text else False)
        if about_header:
            about_elem = about_header.find_next_sibling('p')
            if about_elem:
                description_parts.append(f"About: {about_elem.get_text(strip=True)}")
        
        # Extract Requirements section
        req_header = element.find('h4', string=lambda text: 'Requirements' in text if text else False)
        if req_header:
            req_elem = req_header.find_next_sibling('p')
            if req_elem:
                description_parts.append(f"Requirements: {req_elem.get_text(strip=True)}")
        
        if description_parts:
            return ' | '.join(description_parts)
        
        # Fallback: get all text content
        text_content = element.get_text(separator=' ', strip=True)
        text_content = re.sub(r'\s+', ' ', text_content)
        
        if len(text_content) > 2000:
            text_content = text_content[:2000] + "..."
        
        return text_content
    
    def _extract_salary(self, element: Tag) -> Optional[str]:
        """Extract salary information from element"""
        text_content = element.get_text()
        
        # Common salary patterns
        salary_patterns = [
            r'\$[\d,]+\s*-\s*\$[\d,]+',  # $100,000 - $150,000
            r'\$[\d,]+\+?',  # $100,000 or $100,000+
            r'[\d,]+\s*-\s*[\d,]+\s*USD',  # 100,000 - 150,000 USD
            r'[\d,]+k\s*-\s*[\d,]+k',  # 100k - 150k
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                return match.group().strip()
        
        return None
    
    def scrape_page(self, page_number: int) -> List[Dict[str, Any]]:
        """Override to add custom waiting for Hirebase React app"""
        url = self.get_page_url(page_number)
        self.logger.info(f"Scraping Hirebase page {page_number} with Selenium: {url}")
        
        # Random delay before request
        if page_number > 1:  # Don't delay on first page
            self._random_delay(self.config.delay_range)
        
        # AIDEV-NOTE: Use Selenium to load the page with enhanced waiting
        soup = self._selenium_get_page(url, wait_for_element=self._get_wait_element())
        
        if not soup:
            self.stats['errors'] += 1
            return []
        
        # Additional waiting for React app to load
        self._wait_for_page_load()
        
        # Re-get page source after waiting
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
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
            self.logger.info(f"Found {len(jobs)} jobs on Hirebase page {page_number}")
            
            return jobs
            
        except Exception as e:
            self.logger.error(f"Error parsing Hirebase page {page_number}: {str(e)}")
            self.stats['errors'] += 1
            return []
    
    def _generate_job_id(self, identifier: str) -> str:
        """Generate a consistent job ID from identifier"""
        # Create a hash-like ID that's deterministic
        import hashlib
        return hashlib.md5(identifier.encode()).hexdigest()[:12]
    
    def has_next_page(self, soup: BeautifulSoup, current_page: int) -> bool:
        """Determine if there are more pages to scrape for Hirebase"""
        # AIDEV-NOTE: Check if we found any jobs on current page and haven't hit max_pages
        job_elements = self.get_job_elements(soup)
        
        # If no jobs found on current page, stop pagination
        if not job_elements:
            self.logger.info(f"No jobs found on page {current_page}, stopping pagination")
            return False
        
        # Continue if we haven't hit max_pages and found jobs
        if current_page < self.config.max_pages:
            self.logger.info(f"Found {len(job_elements)} jobs on page {current_page}, continuing to next page")
            return True
        
        self.logger.info(f"Reached max pages ({self.config.max_pages}), stopping pagination")
        return False
    
    def supports_detail_pages(self) -> bool:
        """Hirebase supports detailed job page extraction"""
        return True
    
    def _get_wait_element(self) -> str:
        """Return CSS selector for job elements to wait for"""
        # AIDEV-NOTE: Wait for React app to load and render job cards
        # Since hirebase is a React SPA, we need to wait for the actual job content to load
        return 'div.bg-white.rounded-xl, [data-testid="job-card"], .job-card, main'
    
    def _get_detail_wait_element(self) -> str:
        """Return CSS selector for detail page elements to wait for"""
        return '.prose, h3, .job-description'  # Wait for main content
    
    def _extract_job_details_from_soup(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract comprehensive details from individual Hirebase job pages"""
        try:
            details = {}
            
            # Extract About the Company section
            details['about_company'] = self._extract_company_section(soup)
            
            # Extract detailed Job Description
            details['detailed_job_description'] = self._extract_detailed_description(soup)
            
            # Extract Requirements
            details['detailed_requirements'] = self._extract_requirements_section(soup)
            
            # Extract Benefits
            details['benefits'] = self._extract_benefits_section(soup)
            
            # Extract Work Type (remote/hybrid/onsite)
            details['work_type'] = self._extract_work_type(soup)
            
            # Extract detailed Salary Range
            details['detailed_salary_range'] = self._extract_detailed_salary(soup)
            
            # Extract any additional fields specific to Hirebase
            details['company_size'] = self._extract_company_size(soup)
            details['experience_level'] = self._extract_experience_level(soup)
            details['job_type'] = self._extract_job_type(soup)  # Full-time, Contract, etc.
            
            self.logger.debug(f"Extracted details from soup: {len(details)} fields")
            return details
            
        except Exception as e:
            self.logger.error(f"Error extracting job details from soup: {str(e)}")
            return None
    
    def _extract_company_section(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract About the Company section from Hirebase job detail page"""
        # AIDEV-NOTE: Hirebase detail pages have specific structure for company info
        # Look for the "About the Company" section
        about_header = soup.find('h3', string=lambda text: 'About the Company' in text if text else False)
        if about_header:
            # Find the next paragraph or div with company description
            next_elem = about_header.find_next_sibling(['p', 'div'])
            if next_elem and next_elem.get_text(strip=True):
                return next_elem.get_text(strip=True)[:1000]
        
        # Alternative: look in the sidebar "About [Company]" section
        about_company_header = soup.find('h3', string=lambda text: text and 'About' in text)
        if about_company_header:
            next_elem = about_company_header.find_next_sibling('p')
            if next_elem and next_elem.get_text(strip=True):
                return next_elem.get_text(strip=True)[:1000]
        
        return None
    
    def _extract_detailed_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract detailed job description from Hirebase job detail page"""
        # AIDEV-NOTE: Hirebase detail pages have "Job Description" section
        job_desc_header = soup.find('h3', string=lambda text: 'Job Description' in text if text else False)
        if job_desc_header:
            # Find the content div after the header
            next_elem = job_desc_header.find_next_sibling('div')
            if next_elem and next_elem.get_text(strip=True):
                text = next_elem.get_text(separator='\n', strip=True)
                text = re.sub(r'\n\s*\n', '\n\n', text)
                return text[:3000] if len(text) > 3000 else text
        
        # Alternative: look for prose content in main area
        prose_elem = soup.select_one('.prose')
        if prose_elem and prose_elem.get_text(strip=True):
            text = prose_elem.get_text(separator='\n', strip=True)
            text = re.sub(r'\n\s*\n', '\n\n', text)
            return text[:3000] if len(text) > 3000 else text
        
        return None
    
    def _extract_requirements_section(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract requirements/qualifications section from Hirebase job detail page"""
        # AIDEV-NOTE: Hirebase detail pages often have requirements in the job description div with h2 headers
        requirements_header = soup.find('h2', string=lambda text: 'Requirements' in text if text else False)
        if requirements_header:
            # Find the next ul element or div with requirements
            next_elem = requirements_header.find_next_sibling(['ul', 'div'])
            if next_elem and next_elem.get_text(strip=True):
                return next_elem.get_text(separator='\n', strip=True)[:2000]
        
        # Alternative: look for any text block that contains requirement keywords
        prose_elem = soup.select_one('.prose')
        if prose_elem:
            req_text = prose_elem.get_text()
            # Look for requirements patterns
            req_patterns = [
                r'Requirements:?[^.]*(?:\.[^.]*){0,10}',
                r'Qualifications:?[^.]*(?:\.[^.]*){0,10}',
                r'Must have:?[^.]*(?:\.[^.]*){0,5}'
            ]
            
            for pattern in req_patterns:
                match = re.search(pattern, req_text, re.IGNORECASE | re.DOTALL)
                if match:
                    return match.group().strip()[:2000]
        
        return None
    
    def _extract_benefits_section(self, soup: BeautifulSoup) -> Optional[List[str]]:
        """Extract benefits section as a list"""
        benefits_selectors = [
            '.benefits',
            '.perks',
            '.job-benefits',
            '[class*="benefit"]',
            '[class*="perk"]',
            'section:contains("Benefits")',
            'div:contains("Perks")',
            'ul:contains("Benefits")'
        ]
        
        for selector in benefits_selectors:
            try:
                if ':contains(' in selector:
                    search_term = selector.split(':contains("')[1].split('")')[0]
                    elements = soup.find_all(text=re.compile(search_term, re.IGNORECASE))
                    for element in elements:
                        parent = element.parent
                        if parent:
                            # Look for list items
                            list_items = parent.find_all('li')
                            if list_items:
                                return [li.get_text(strip=True) for li in list_items[:10]]  # Limit to 10 benefits
                            # Or just return the text content
                            text = parent.get_text(strip=True)
                            if text:
                                return [text[:500]]  # Return as single item list
                else:
                    element = soup.select_one(selector)
                    if element:
                        list_items = element.find_all('li')
                        if list_items:
                            return [li.get_text(strip=True) for li in list_items[:10]]
                        text = element.get_text(strip=True)
                        if text:
                            return [text[:500]]
            except Exception:
                continue
        
        return None
    
    def _extract_work_type(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract work type from Hirebase job detail page"""
        # AIDEV-NOTE: Hirebase shows work type in the "Job Details" section
        job_details_section = soup.find('h3', string=lambda text: 'Job Details' in text if text else False)
        if job_details_section:
            # Look for Work Type field
            parent_div = job_details_section.find_parent('div')
            if parent_div:
                work_type_pattern = re.search(r'Work Type[^\w]*([^\n]+)', parent_div.get_text())
                if work_type_pattern:
                    return work_type_pattern.group(1).strip()
        
        # Alternative: look for specific work type indicators
        text_content = soup.get_text().lower()
        
        if 'remote' in text_content:
            if 'hybrid' in text_content:
                return 'Hybrid'
            else:
                return 'Remote'
        elif 'on-site' in text_content or 'onsite' in text_content:
            return 'On-site'
        
        return None
    
    def _extract_detailed_salary(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract detailed salary information from job page"""
        # Look for salary sections
        salary_selectors = [
            '.salary',
            '.compensation',
            '.pay',
            '[class*="salary"]',
            '[class*="compensation"]',
            '[class*="pay"]'
        ]
        
        for selector in salary_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                # Look for salary patterns in the detailed text
                salary = self._extract_salary_from_text(text)
                if salary:
                    return salary
        
        # Fallback: search entire page text for salary patterns
        return self._extract_salary_from_text(soup.get_text())
    
    def _extract_salary_from_text(self, text: str) -> Optional[str]:
        """Extract salary from text using patterns"""
        salary_patterns = [
            r'\$[\d,]+\s*-\s*\$[\d,]+\s*(?:per\s+year|annually|/year)?',
            r'\$[\d,]+\+?\s*(?:per\s+year|annually|/year)?',
            r'[\d,]+\s*-\s*[\d,]+\s*USD\s*(?:per\s+year|annually|/year)?',
            r'[\d,]+k\s*-\s*[\d,]+k\s*(?:per\s+year|annually|/year)?',
            r'Salary:\s*\$?[\d,]+(?:\s*-\s*\$?[\d,]+)?'
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group().strip()
        
        return None
    
    def _extract_company_size(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract company size information"""
        text_content = soup.get_text()
        
        size_patterns = [
            r'(\d+)\s*-\s*(\d+)\s*employees',
            r'(\d+)\+?\s*employees',
            r'(startup|small|medium|large|enterprise)\s*company',
            r'company\s*size:\s*([^.\n]+)'
        ]
        
        for pattern in size_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                return match.group().strip()
        
        return None
    
    def _extract_experience_level(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract experience level requirements"""
        text_content = soup.get_text().lower()
        
        experience_keywords = [
            ('entry level', 'Entry Level'),
            ('junior', 'Junior'),
            ('mid level', 'Mid Level'),
            ('senior', 'Senior'),
            ('lead', 'Lead'),
            ('principal', 'Principal'),
            ('staff', 'Staff'),
            ('director', 'Director')
        ]
        
        for keyword, level in experience_keywords:
            if keyword in text_content:
                return level
        
        # Look for years of experience patterns
        years_pattern = r'(\d+)\+?\s*years?\s*(?:of\s*)?experience'
        match = re.search(years_pattern, text_content)
        if match:
            years = int(match.group(1))
            if years <= 2:
                return 'Entry Level'
            elif years <= 5:
                return 'Mid Level'
            else:
                return 'Senior'
        
        return None
    
    def _extract_job_type(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract job type from Hirebase job detail page"""
        # AIDEV-NOTE: Hirebase shows employment type in the "Job Details" section
        job_details_section = soup.find('h3', string=lambda text: 'Job Details' in text if text else False)
        if job_details_section:
            parent_div = job_details_section.find_parent('div')
            if parent_div:
                emp_type_pattern = re.search(r'Employment Type[^\w]*([^\n]+)', parent_div.get_text())
                if emp_type_pattern:
                    return emp_type_pattern.group(1).strip()
        
        # Fallback: look for job type keywords in text
        text_content = soup.get_text().lower()
        
        job_type_keywords = [
            ('full-time', 'Full-time'),
            ('full time', 'Full-time'),
            ('part-time', 'Part-time'),
            ('part time', 'Part-time'),
            ('contract', 'Contract'),
            ('freelance', 'Freelance'),
            ('temporary', 'Temporary'),
            ('internship', 'Internship')
        ]
        
        for keyword, job_type in job_type_keywords:
            if keyword in text_content:
                return job_type
        
        return None