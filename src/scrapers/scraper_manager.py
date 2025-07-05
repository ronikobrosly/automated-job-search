"""
Scraper orchestration and management system.
Handles coordination of multiple scrapers and database integration.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from config.sites import SiteConfig, get_enabled_sites
from ..database import JobOperations, get_db_session
from .sites.hirebase_scraper import HirebaseScraper


class ScraperManager:
    """Manages multiple scrapers and coordinates their execution.

    Orchestrates the scraping process across multiple job sites,
    manages database integration, and provides statistics.
    """

    def __init__(self) -> None:
        """Initialize the scraper manager with empty scrapers and stats."""
        self.logger = logging.getLogger("scraper_manager")
        self.scrapers = {}
        self.stats = {
            "total_jobs_scraped": 0,
            "total_new_jobs": 0,
            "total_errors": 0,
            "sites_processed": 0,
        }

        # Initialize scrapers for enabled sites
        self._initialize_scrapers()

    def _initialize_scrapers(self) -> None:
        """Initialize scrapers for all enabled sites."""
        enabled_sites = get_enabled_sites()

        for site_name, site_config in enabled_sites.items():
            try:
                scraper = self._create_scraper(site_name, site_config)
                if scraper:
                    self.scrapers[site_name] = scraper
                    self.logger.info(f"Initialized scraper for {site_name}")
                else:
                    self.logger.warning(
                        f"No scraper implementation found for {site_name}"
                    )
            except Exception as e:
                self.logger.error(
                    f"Failed to initialize scraper for {site_name}: {str(e)}"
                )

    def _create_scraper(self, site_name: str, site_config: SiteConfig):
        """Factory method to create appropriate scraper instance.

        Args:
            site_name: Name of the site to create scraper for.
            site_config: Configuration for the site.

        Returns:
            Scraper instance if available, None otherwise.
        """
        scraper_mapping = {
            "hirebase": HirebaseScraper,
            # Add other scrapers here as they're implemented
            # 'linkedin': LinkedInScraper,
            # 'indeed': IndeedScraper,
        }

        scraper_class = scraper_mapping.get(site_name)
        if scraper_class:
            return scraper_class(site_config)
        return None

    def scrape_all_sites(self) -> Dict[str, Any]:
        """Scrape all enabled sites and return summary statistics.

        Returns:
            Dict[str, Any]: Summary of scraping results and statistics.
        """
        self.logger.info("Starting scrape of all enabled sites")
        start_time = datetime.now()

        site_results = {}

        for site_name, scraper in self.scrapers.items():
            try:
                self.logger.info(f"Starting scrape of {site_name}")
                site_stats = self._scrape_site(site_name, scraper)
                site_results[site_name] = site_stats

                # Update overall stats
                self.stats["sites_processed"] += 1
                self.stats["total_jobs_scraped"] += site_stats.get("jobs_scraped", 0)
                self.stats["total_new_jobs"] += site_stats.get("new_jobs", 0)
                self.stats["total_errors"] += site_stats.get("errors", 0)

            except Exception as e:
                self.logger.error(f"Failed to scrape {site_name}: {str(e)}")
                site_results[site_name] = {
                    "status": "failed",
                    "error": str(e),
                    "jobs_scraped": 0,
                    "new_jobs": 0,
                    "errors": 1,
                }
                self.stats["total_errors"] += 1

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        summary = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "overall_stats": self.stats,
            "site_results": site_results,
        }

        self.logger.info(
            f"Scraping completed in {duration:.2f} seconds. "
            f"Total jobs: {self.stats['total_jobs_scraped']}, "
            f"New jobs: {self.stats['total_new_jobs']}"
        )

        return summary

    def _scrape_site(self, site_name: str, scraper) -> Dict[str, Any]:
        """Scrape a single site and save results to database.

        Args:
            site_name: Name of the site being scraped.
            scraper: Scraper instance for the site.

        Returns:
            Dict[str, Any]: Site-specific scraping statistics.
        """
        site_stats = {
            "status": "success",
            "jobs_scraped": 0,
            "new_jobs": 0,
            "updated_jobs": 0,
            "errors": 0,
            "pages_scraped": 0,
        }

        try:
            # Get database session
            session = next(get_db_session())

            try:
                # Scrape all pages from the site
                for job_batch in scraper.scrape_all_pages():
                    if not job_batch:
                        continue

                    # Process each job in the batch
                    for job_data in job_batch:
                        try:
                            result = self._process_job(session, job_data)

                            if result == "new":
                                site_stats["new_jobs"] += 1
                            elif result == "updated":
                                site_stats["updated_jobs"] += 1

                            site_stats["jobs_scraped"] += 1

                        except Exception as e:
                            self.logger.error(
                                f"Error processing job from {site_name}: {str(e)}"
                            )
                            site_stats["errors"] += 1

                # Get scraper statistics
                scraper_stats = scraper.get_stats()
                site_stats["pages_scraped"] = scraper_stats.get("pages_scraped", 0)
                site_stats["errors"] += scraper_stats.get("errors", 0)

            finally:
                session.close()

        except Exception as e:
            self.logger.error(f"Database error for {site_name}: {str(e)}")
            site_stats["status"] = "failed"
            site_stats["error"] = str(e)

        return site_stats

    def _process_job(self, session: Session, job_data: Dict) -> str:
        """Process a single job - create new or update existing.

        Args:
            session: Database session.
            job_data: Dictionary containing job information.

        Returns:
            str: Status of job processing ('new', 'updated', or 'existing').
        """
        job_id = job_data.get("job_id")
        job_website = job_data.get("job_website")

        if not job_id or not job_website:
            raise ValueError("Job data missing required fields: job_id or job_website")

        # Check if job already exists
        existing_job = JobOperations.get_job_by_id_and_website(
            session, job_id, job_website
        )

        if existing_job:
            # Update last_seen timestamp
            JobOperations.update_job_last_seen(session, existing_job)

            # Check if content has changed
            new_content_hash = existing_job.generate_content_hash()
            if existing_job.content_hash != new_content_hash:
                # Update job data if content changed
                for key, value in job_data.items():
                    if hasattr(existing_job, key) and key not in ["id", "created_at"]:
                        setattr(existing_job, key, value)

                existing_job.content_hash = new_content_hash
                existing_job.updated_at = datetime.now()
                session.commit()

                self.logger.debug(f"Updated job: {job_id}")
                return "updated"

            return "existing"
        else:
            # Create new job
            job_data["is_new"] = True
            job_data["when_scraped"] = datetime.now()
            job_data["last_seen"] = datetime.now()

            new_job = JobOperations.create_job(session, job_data)

            self.logger.debug(f"Created new job: {job_id}")
            return "new"

    def get_scraper_stats(self) -> Dict[str, Any]:
        """Get overall scraper statistics.

        Returns:
            Dict[str, Any]: Copy of overall scraping statistics.
        """
        return self.stats.copy()

    def get_new_jobs_since(self, since_datetime: datetime) -> List[Dict]:
        """Get new jobs since specified datetime.

        Args:
            since_datetime: Datetime to filter jobs from.

        Returns:
            List[Dict]: List of new jobs with basic information.
        """
        session = next(get_db_session())
        try:
            new_jobs = JobOperations.get_new_jobs_since(session, since_datetime)
            return [
                {
                    "id": job.id,
                    "job_id": job.job_id,
                    "role_title": job.role_title,
                    "company_name": job.company_name,
                    "job_website": job.job_website,
                    "job_url": job.job_url,
                    "location": job.location,
                    "when_scraped": (
                        job.when_scraped.isoformat() if job.when_scraped else None
                    ),
                }
                for job in new_jobs
            ]
        finally:
            session.close()
