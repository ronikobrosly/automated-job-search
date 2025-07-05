"""Unit tests for scraper manager."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.scrapers.scraper_manager import ScraperManager


class TestScraperManager:
    """Test cases for the ScraperManager class."""

    @patch("src.scrapers.scraper_manager.get_enabled_sites")
    def test_init_initializes_scrapers(self, mock_get_sites):
        """Test that initialization creates scrapers for enabled sites.

        Args:
            mock_get_sites: Mock get_enabled_sites function.
        """
        mock_site_config = Mock()
        mock_site_config.name = "test-site"
        mock_get_sites.return_value = {"test-site": mock_site_config}

        with patch.object(ScraperManager, "_create_scraper") as mock_create:
            mock_scraper = Mock()
            mock_create.return_value = mock_scraper

            manager = ScraperManager()

            assert "test-site" in manager.scrapers
            assert manager.scrapers["test-site"] == mock_scraper
            mock_create.assert_called_once_with("test-site", mock_site_config)

    @patch("src.scrapers.scraper_manager.get_enabled_sites")
    def test_init_handles_scraper_creation_failure(self, mock_get_sites):
        """Test initialization handles scraper creation failures gracefully.

        Args:
            mock_get_sites: Mock get_enabled_sites function.
        """
        mock_site_config = Mock()
        mock_get_sites.return_value = {"failing-site": mock_site_config}

        with patch.object(ScraperManager, "_create_scraper") as mock_create:
            mock_create.side_effect = Exception("Scraper creation failed")

            manager = ScraperManager()

            # Should not have the failing scraper
            assert "failing-site" not in manager.scrapers
            assert manager.stats["total_errors"] == 0  # Errors tracked separately

    def test_create_scraper_hirebase(self):
        """Test creating HirebaseScraper instance."""
        from config.sites.sites_config import SiteConfig

        site_config = SiteConfig(
            name="hirebase",
            base_url="https://hirebase.org",
            search_url="https://hirebase.org/search",
        )

        with patch("src.scrapers.scraper_manager.get_enabled_sites", return_value={}):
            manager = ScraperManager()
            scraper = manager._create_scraper("hirebase", site_config)

        # Should return HirebaseScraper instance
        assert scraper is not None
        assert scraper.__class__.__name__ == "HirebaseScraper"

    def test_create_scraper_unknown_site(self):
        """Test creating scraper for unknown site returns None."""
        from config.sites.sites_config import SiteConfig

        site_config = SiteConfig(
            name="unknown-site",
            base_url="https://unknown.com",
            search_url="https://unknown.com/jobs",
        )

        with patch("src.scrapers.scraper_manager.get_enabled_sites", return_value={}):
            manager = ScraperManager()
            scraper = manager._create_scraper("unknown-site", site_config)

        assert scraper is None

    @patch("src.scrapers.scraper_manager.get_enabled_sites")
    def test_scrape_all_sites_success(self, mock_get_sites):
        """Test successful scraping of all sites.

        Args:
            mock_get_sites: Mock get_enabled_sites function.
        """
        mock_get_sites.return_value = {}

        # Create manager with mock scraper
        manager = ScraperManager()
        mock_scraper = Mock()
        manager.scrapers = {"test-site": mock_scraper}

        with patch.object(manager, "_scrape_site") as mock_scrape_site:
            mock_scrape_site.return_value = {
                "status": "success",
                "jobs_scraped": 5,
                "new_jobs": 3,
                "errors": 0,
            }

            results = manager.scrape_all_sites()

            assert "start_time" in results
            assert "end_time" in results
            assert "duration_seconds" in results
            assert "overall_stats" in results
            assert "site_results" in results

            # Check stats were updated
            assert results["overall_stats"]["total_jobs_scraped"] == 5
            assert results["overall_stats"]["total_new_jobs"] == 3
            assert results["overall_stats"]["sites_processed"] == 1

    @patch("src.scrapers.scraper_manager.get_enabled_sites")
    def test_scrape_all_sites_with_failure(self, mock_get_sites):
        """Test scraping with one site failing.

        Args:
            mock_get_sites: Mock get_enabled_sites function.
        """
        mock_get_sites.return_value = {}

        manager = ScraperManager()
        mock_scraper = Mock()
        manager.scrapers = {"failing-site": mock_scraper}

        with patch.object(manager, "_scrape_site") as mock_scrape_site:
            mock_scrape_site.side_effect = Exception("Scrape failed")

            results = manager.scrape_all_sites()

            assert results["site_results"]["failing-site"]["status"] == "failed"
            assert "error" in results["site_results"]["failing-site"]
            assert results["overall_stats"]["total_errors"] == 1

    @patch("src.scrapers.scraper_manager.get_db_session")
    def test_scrape_site_success(self, mock_get_session):
        """Test successful site scraping.

        Args:
            mock_get_session: Mock get_db_session function.
        """
        # Setup mock session
        mock_session = Mock()
        mock_get_session.return_value.__next__ = Mock(return_value=mock_session)

        # Setup mock scraper
        mock_scraper = Mock()
        mock_scraper.scrape_all_pages.return_value = [
            [{"job_id": "1", "job_website": "test-site", "role_title": "Engineer"}],
            [{"job_id": "2", "job_website": "test-site", "role_title": "Developer"}],
        ]
        mock_scraper.get_stats.return_value = {"pages_scraped": 2, "errors": 0}

        with patch("src.scrapers.scraper_manager.get_enabled_sites", return_value={}):
            manager = ScraperManager()

            with patch.object(manager, "_process_job") as mock_process:
                mock_process.side_effect = ["new", "new"]

                results = manager._scrape_site("test-site", mock_scraper)

                assert results["status"] == "success"
                assert results["jobs_scraped"] == 2
                assert results["new_jobs"] == 2
                assert results["pages_scraped"] == 2
                assert mock_process.call_count == 2

    @patch("src.scrapers.scraper_manager.get_db_session")
    def test_scrape_site_database_error(self, mock_get_session):
        """Test site scraping with database error.

        Args:
            mock_get_session: Mock get_db_session function.
        """
        mock_get_session.side_effect = SQLAlchemyError("Database connection failed")

        mock_scraper = Mock()

        with patch("src.scrapers.scraper_manager.get_enabled_sites", return_value={}):
            manager = ScraperManager()

            results = manager._scrape_site("test-site", mock_scraper)

            assert results["status"] == "failed"
            assert "error" in results

    @patch("src.scrapers.scraper_manager.JobOperations")
    def test_process_job_new_job(self, mock_job_ops):
        """Test processing a new job.

        Args:
            mock_job_ops: Mock JobOperations class.
        """
        mock_session = Mock()
        job_data = {
            "job_id": "new-job-1",
            "job_website": "test-site",
            "role_title": "Software Engineer",
        }

        # Mock job doesn't exist
        mock_job_ops.get_job_by_id_and_website.return_value = None
        mock_job_ops.create_job.return_value = Mock()

        with patch("src.scrapers.scraper_manager.get_enabled_sites", return_value={}):
            manager = ScraperManager()

            result = manager._process_job(mock_session, job_data)

            assert result == "new"
            mock_job_ops.create_job.assert_called_once()
            # Verify job_data was modified with required fields
            create_call_args = mock_job_ops.create_job.call_args[0][1]
            assert create_call_args["is_new"] is True
            assert "when_scraped" in create_call_args
            assert "last_seen" in create_call_args

    @patch("src.scrapers.scraper_manager.JobOperations")
    def test_process_job_existing_unchanged(self, mock_job_ops):
        """Test processing an existing job with no changes.

        Args:
            mock_job_ops: Mock JobOperations class.
        """
        mock_session = Mock()
        job_data = {
            "job_id": "existing-job",
            "job_website": "test-site",
            "role_title": "Engineer",
        }

        # Mock existing job
        mock_existing_job = Mock()
        mock_existing_job.content_hash = "existing_hash"
        mock_existing_job.generate_content_hash.return_value = "existing_hash"
        mock_job_ops.get_job_by_id_and_website.return_value = mock_existing_job

        with patch("src.scrapers.scraper_manager.get_enabled_sites", return_value={}):
            manager = ScraperManager()

            result = manager._process_job(mock_session, job_data)

            assert result == "existing"
            mock_job_ops.update_job_last_seen.assert_called_once_with(
                mock_session, mock_existing_job
            )

    @patch("src.scrapers.scraper_manager.JobOperations")
    @patch("src.scrapers.scraper_manager.datetime")
    def test_process_job_existing_updated(self, mock_datetime, mock_job_ops):
        """Test processing an existing job with changes.

        Args:
            mock_datetime: Mock datetime module.
            mock_job_ops: Mock JobOperations class.
        """
        mock_session = Mock()
        job_data = {
            "job_id": "updated-job",
            "job_website": "test-site",
            "role_title": "Senior Engineer",  # Changed title
            "job_description": "Updated description",
        }

        # Mock existing job with different hash
        mock_existing_job = Mock()
        mock_existing_job.content_hash = "old_hash"
        mock_existing_job.generate_content_hash.return_value = "new_hash"
        mock_job_ops.get_job_by_id_and_website.return_value = mock_existing_job

        mock_now = datetime(2024, 1, 15, 12, 0, 0)
        mock_datetime.now.return_value = mock_now

        with patch("src.scrapers.scraper_manager.get_enabled_sites", return_value={}):
            manager = ScraperManager()

            result = manager._process_job(mock_session, job_data)

            assert result == "updated"
            mock_job_ops.update_job_last_seen.assert_called_once()
            assert mock_existing_job.content_hash == "new_hash"
            assert mock_existing_job.updated_at == mock_now

    def test_process_job_missing_required_fields(self):
        """Test processing job with missing required fields raises error."""
        mock_session = Mock()

        # Missing job_id
        invalid_job_data = {"job_website": "test-site", "role_title": "Engineer"}

        with patch("src.scrapers.scraper_manager.get_enabled_sites", return_value={}):
            manager = ScraperManager()

            with pytest.raises(ValueError, match="Job data missing required fields"):
                manager._process_job(mock_session, invalid_job_data)

    def test_get_scraper_stats(self):
        """Test getting scraper statistics."""
        with patch("src.scrapers.scraper_manager.get_enabled_sites", return_value={}):
            manager = ScraperManager()
            manager.stats = {
                "total_jobs_scraped": 10,
                "total_new_jobs": 5,
                "total_errors": 1,
                "sites_processed": 2,
            }

            stats = manager.get_scraper_stats()

            assert stats == manager.stats
            # Ensure it returns a copy
            stats["total_jobs_scraped"] = 999
            assert manager.stats["total_jobs_scraped"] == 10

    @patch("src.scrapers.scraper_manager.get_db_session")
    @patch("src.scrapers.scraper_manager.JobOperations")
    def test_get_new_jobs_since(self, mock_job_ops, mock_get_session):
        """Test getting new jobs since a specific datetime.

        Args:
            mock_job_ops: Mock JobOperations class.
            mock_get_session: Mock get_db_session function.
        """
        mock_session = Mock()
        mock_get_session.return_value.__next__ = Mock(return_value=mock_session)

        # Mock job instances
        mock_job1 = Mock()
        mock_job1.id = 1
        mock_job1.job_id = "job-1"
        mock_job1.role_title = "Engineer"
        mock_job1.company_name = "Company A"
        mock_job1.job_website = "site-1"
        mock_job1.job_url = "https://example.com/job/1"
        mock_job1.location = "Remote"
        mock_job1.when_scraped = datetime(2024, 1, 15, 10, 0, 0)

        mock_job2 = Mock()
        mock_job2.id = 2
        mock_job2.job_id = "job-2"
        mock_job2.role_title = "Developer"
        mock_job2.company_name = "Company B"
        mock_job2.job_website = "site-2"
        mock_job2.job_url = "https://example.com/job/2"
        mock_job2.location = "San Francisco"
        mock_job2.when_scraped = datetime(2024, 1, 15, 11, 0, 0)

        mock_job_ops.get_new_jobs_since.return_value = [mock_job1, mock_job2]

        with patch("src.scrapers.scraper_manager.get_enabled_sites", return_value={}):
            manager = ScraperManager()

            since_datetime = datetime(2024, 1, 15, 9, 0, 0)
            jobs = manager.get_new_jobs_since(since_datetime)

            assert len(jobs) == 2
            assert jobs[0]["id"] == 1
            assert jobs[0]["job_id"] == "job-1"
            assert jobs[0]["role_title"] == "Engineer"
            assert jobs[0]["when_scraped"] == "2024-01-15T10:00:00"

            assert jobs[1]["id"] == 2
            assert jobs[1]["role_title"] == "Developer"

            mock_job_ops.get_new_jobs_since.assert_called_once_with(
                mock_session, since_datetime
            )

    @patch("src.scrapers.scraper_manager.get_db_session")
    @patch("src.scrapers.scraper_manager.JobOperations")
    def test_get_new_jobs_since_none_when_scraped(self, mock_job_ops, mock_get_session):
        """Test getting new jobs handles None when_scraped gracefully.

        Args:
            mock_job_ops: Mock JobOperations class.
            mock_get_session: Mock get_db_session function.
        """
        mock_session = Mock()
        mock_get_session.return_value.__next__ = Mock(return_value=mock_session)

        mock_job = Mock()
        mock_job.id = 1
        mock_job.job_id = "job-1"
        mock_job.role_title = "Engineer"
        mock_job.company_name = "Company A"
        mock_job.job_website = "site-1"
        mock_job.job_url = "https://example.com/job/1"
        mock_job.location = "Remote"
        mock_job.when_scraped = None  # None value

        mock_job_ops.get_new_jobs_since.return_value = [mock_job]

        with patch("src.scrapers.scraper_manager.get_enabled_sites", return_value={}):
            manager = ScraperManager()

            jobs = manager.get_new_jobs_since(datetime.now())

            assert len(jobs) == 1
            assert jobs[0]["when_scraped"] is None

    @patch("src.scrapers.scraper_manager.get_enabled_sites")
    def test_scrape_site_empty_job_batches(self, mock_get_sites):
        """Test scraping site with empty job batches.

        Args:
            mock_get_sites: Mock get_enabled_sites function.
        """
        mock_get_sites.return_value = {}

        mock_scraper = Mock()
        mock_scraper.scrape_all_pages.return_value = [[], []]  # Empty batches
        mock_scraper.get_stats.return_value = {"pages_scraped": 2, "errors": 0}

        with patch("src.scrapers.scraper_manager.get_db_session") as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value.__next__ = Mock(return_value=mock_session)

            manager = ScraperManager()
            results = manager._scrape_site("test-site", mock_scraper)

            assert results["status"] == "success"
            assert results["jobs_scraped"] == 0
            assert results["new_jobs"] == 0

    @patch("src.scrapers.scraper_manager.get_enabled_sites")
    def test_scrape_site_job_processing_error(self, mock_get_sites):
        """Test scraping site with job processing errors.

        Args:
            mock_get_sites: Mock get_enabled_sites function.
        """
        mock_get_sites.return_value = {}

        mock_scraper = Mock()
        mock_scraper.scrape_all_pages.return_value = [
            [{"job_id": "1", "job_website": "test-site", "role_title": "Engineer"}]
        ]
        mock_scraper.get_stats.return_value = {"pages_scraped": 1, "errors": 0}

        with patch("src.scrapers.scraper_manager.get_db_session") as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value.__next__ = Mock(return_value=mock_session)

            manager = ScraperManager()

            with patch.object(manager, "_process_job") as mock_process:
                mock_process.side_effect = Exception("Processing failed")

                results = manager._scrape_site("test-site", mock_scraper)

                assert results["status"] == "success"  # Still success overall
                assert results["errors"] == 1  # But error recorded
