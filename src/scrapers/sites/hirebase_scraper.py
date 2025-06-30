"""
Hirebase.org specific scraper implementation.
"""

import re
import logging
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin, urlparse

from ..base_scraper import BaseScraper
from config.sites import SiteConfig

class HirebaseScraper(BaseScraper):
    """Scraper for hirebase.org job listings"""
    
    def __init__(self, site_config: SiteConfig):
        super().__init__(site_config)
        self.logger = logging.getLogger("scraper.hirebase")
    
    def get_job_elements(self, soup: BeautifulSoup) -> List[Tag]:
        """Extract job listing elements from the page soup"""
        # Look for common job listing containers on hirebase.org
        # These selectors might need adjustment based on actual site structure
        job_selectors = [
            'div[class*="job"]',
            'div[class*="listing"]',
            'div[class*="card"]',
            'div[class*="result"]',
            'article',
            '.job-item',
            '.job-listing',
            '.search-result'
        ]
        
        job_elements = []
        for selector in job_selectors:
            elements = soup.select(selector)
            if elements:
                self.logger.debug(f"Found {len(elements)} elements with selector: {selector}")
                job_elements.extend(elements)
                break  # Use first successful selector
        
        # If no specific selectors work, try to find elements with job-related text
        if not job_elements:
            # Look for divs containing job-related keywords
            all_divs = soup.find_all('div')
            for div in all_divs:
                text = div.get_text().lower()
                if any(keyword in text for keyword in ['engineer', 'scientist', 'developer', 'analyst', 'manager']):
                    # Check if this looks like a job listing (has company name, title, etc.)
                    if len(text.split()) > 10 and len(text) < 2000:  # Reasonable job listing length
                        job_elements.append(div)
        
        self.logger.info(f"Found {len(job_elements)} potential job elements")
        return job_elements
    
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
        """Extract job title from element"""
        # Try different approaches to find job title
        
        # Look for common title selectors
        title_selectors = ['h1', 'h2', 'h3', '.title', '.job-title', '[class*="title"]']
        for selector in title_selectors:
            title_elem = element.select_one(selector)
            if title_elem and title_elem.get_text(strip=True):
                return title_elem.get_text(strip=True)
        
        # Look for strong/bold text that might be a title
        strong_elements = element.find_all(['strong', 'b'])
        for strong in strong_elements:
            text = strong.get_text(strip=True)
            if text and self._looks_like_job_title(text):
                return text
        
        # Look for links that might be job titles
        links = element.find_all('a')
        for link in links:
            text = link.get_text(strip=True)
            if text and self._looks_like_job_title(text):
                return text
        
        # Fallback: look for text patterns that look like job titles
        text_content = element.get_text()
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        for line in lines[:5]:  # Check first few lines
            if self._looks_like_job_title(line):
                return line
        
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
        """Extract company name from element"""
        # Look for company-related selectors
        company_selectors = ['.company', '.company-name', '[class*="company"]']
        for selector in company_selectors:
            company_elem = element.select_one(selector)
            if company_elem and company_elem.get_text(strip=True):
                return company_elem.get_text(strip=True)
        
        # Look for text patterns
        text_content = element.get_text()
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        
        # Company name often appears after job title
        for i, line in enumerate(lines[1:4], 1):  # Check lines 2-4
            if line and not self._looks_like_job_title(line) and len(line) < 50:
                # Simple heuristic: if it's not too long and doesn't look like a title
                if not re.match(r'^\$|^\d+|^[A-Z]{2,3}$', line):  # Exclude salary, numbers, state codes
                    return line
        
        return "Unknown Company"
    
    def _extract_location(self, element: Tag) -> Optional[str]:
        """Extract location from element"""
        # Look for location-related selectors
        location_selectors = ['.location', '[class*="location"]', '.address']
        for selector in location_selectors:
            location_elem = element.select_one(selector)
            if location_elem and location_elem.get_text(strip=True):
                return location_elem.get_text(strip=True)
        
        # Look for text patterns that look like locations
        text_content = element.get_text()
        
        # Common location patterns
        location_patterns = [
            r'\b[A-Z][a-z]+,\s*[A-Z]{2}\b',  # City, ST
            r'\b[A-Z][a-z\s]+,\s*[A-Z][a-z\s]+\b',  # City, State/Country
            r'\bRemote\b',
            r'\bNew York\b|\bSan Francisco\b|\bLos Angeles\b|\bChicago\b|\bBoston\b|\bSeattle\b|\bAustin\b'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text_content)
            if match:
                return match.group().strip()
        
        return None
    
    def _extract_job_url(self, element: Tag, page_url: str) -> Optional[str]:
        """Extract job URL from element"""
        # Look for links within the job element
        links = element.find_all('a', href=True)
        
        for link in links:
            href = link.get('href')
            if href:
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    return urljoin(self.config.base_url, href)
                elif href.startswith('http'):
                    return href
        
        return None
    
    def _extract_description(self, element: Tag) -> str:
        """Extract job description from element"""
        # Get all text content, but try to clean it up
        text_content = element.get_text(separator=' ', strip=True)
        
        # Remove excessive whitespace
        text_content = re.sub(r'\s+', ' ', text_content)
        
        # Limit length to avoid storing too much data
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
    
    def _generate_job_id(self, identifier: str) -> str:
        """Generate a consistent job ID from identifier"""
        # Create a hash-like ID that's deterministic
        import hashlib
        return hashlib.md5(identifier.encode()).hexdigest()[:12]
    
    def has_next_page(self, soup: BeautifulSoup, current_page: int) -> bool:
        """Determine if there are more pages to scrape"""
        # For hirebase, we'll use a simple approach:
        # Continue until we hit max_pages or find no jobs
        
        # Look for pagination elements
        pagination_selectors = [
            '.pagination',
            '.pager',
            '[class*="page"]',
            'a[href*="page"]'
        ]
        
        for selector in pagination_selectors:
            pagination = soup.select(selector)
            if pagination:
                # If we find pagination elements with "next" or page numbers > current_page
                for elem in pagination:
                    text = elem.get_text().lower()
                    if 'next' in text or str(current_page + 1) in text:
                        return True
        
        # Simple fallback: continue up to max_pages if we found jobs on this page
        return current_page < self.config.max_pages