"""
Configuration for job scraping websites.
This file defines the websites to scrape and their specific parameters.
"""

from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class SiteConfig:
    """Configuration for a job scraping site.
    
    Contains all settings needed to scrape a specific job website,
    including URLs, pagination, delays, and HTTP headers.
    """
    name: str
    base_url: str
    search_url: str
    enabled: bool = True
    max_pages: int = 10
    delay_range: tuple = (2, 5)  # Random delay between requests (min, max seconds)
    detail_delay_range: tuple = None  # Separate delay for detail page requests (defaults to delay_range)
    detail_batch_size: int = 10  # Process details in batches to avoid overwhelming servers
    max_retries: int = 3
    timeout: int = 30
    headers: Optional[Dict[str, str]] = None
    pagination_param: str = "page"
    pagination_start: int = 1
    
    def __post_init__(self) -> None:
        """Initialize default headers and delay ranges after object creation."""
        if self.headers is None:
            self.headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        
        # Set default detail_delay_range if not specified
        if self.detail_delay_range is None:
            # Use longer delays for detail pages by default
            min_delay, max_delay = self.delay_range
            self.detail_delay_range = (min_delay + 2, max_delay + 4)

# Site configurations
SITES_CONFIG = {
    'hirebase': SiteConfig(
        name='Hirebase',
        base_url='https://hirebase.org',
        search_url='https://hirebase.org/search?page={page}&sort_by=relevance&search_type=resume&accuracy=0.7&score_threshold=0.3&top_k=100&include_yoe=true&job_title=Data+Scientist%2CMachine+Learning+Engineer%2CAI+Engineer&q=staff',
        enabled=True,
        max_pages=20,
        delay_range=(3, 8),  # More conservative delays for this site
        detail_delay_range=(5, 12),  # Even more conservative for detail pages
        detail_batch_size=5,  # Process only 5 detail pages at a time
        max_retries=3,
        timeout=30,
        pagination_param='page',
        pagination_start=1
    ),
    
    # Additional sites can be added here
    # 'linkedin': SiteConfig(
    #     name='LinkedIn Jobs',
    #     base_url='https://www.linkedin.com',
    #     search_url='https://www.linkedin.com/jobs/search/?keywords=data%20scientist&start={start}',
    #     enabled=False,  # Disabled by default
    #     pagination_param='start',
    #     pagination_start=0
    # ),
}

def get_enabled_sites() -> Dict[str, SiteConfig]:
    """Get only the enabled sites for scraping.
    
    Returns:
        Dict[str, SiteConfig]: Dictionary of enabled site configurations.
    """
    return {key: config for key, config in SITES_CONFIG.items() if config.enabled}

def get_site_config(site_name: str) -> Optional[SiteConfig]:
    """Get configuration for a specific site.
    
    Args:
        site_name: Name of the site to get configuration for.
        
    Returns:
        SiteConfig: Site configuration if found, None otherwise.
    """
    return SITES_CONFIG.get(site_name)

def get_all_sites() -> Dict[str, SiteConfig]:
    """Get all site configurations.
    
    Returns:
        Dict[str, SiteConfig]: Dictionary of all site configurations.
    """
    return SITES_CONFIG