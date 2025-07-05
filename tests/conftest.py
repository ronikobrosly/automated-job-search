"""Test configuration and fixtures for automated job search pipeline."""

import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.sites.sites_config import SiteConfig
from src.database.connection import DatabaseManager
from src.database.models.job import Base, Job
from src.database.operations import JobOperations


@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test database engine using in-memory SQLite.

    Returns:
        Engine: SQLAlchemy engine connected to in-memory SQLite.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create a test database session with rollback after each test.

    Args:
        test_db_engine: Test database engine fixture.

    Yields:
        Session: Database session that rolls back after test.
    """
    Session = sessionmaker(bind=test_db_engine)
    session = Session()

    # Create tables for each test
    Base.metadata.create_all(test_db_engine)

    yield session

    # Rollback and close session after test
    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def test_db_manager():
    """Create a test database manager with temporary file.

    Yields:
        DatabaseManager: Test database manager with temporary SQLite file.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp_file:
        db_path = tmp_file.name

    try:
        manager = DatabaseManager(db_path)
        manager.create_tables()
        yield manager
    finally:
        # Clean up temporary database file
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.fixture
def sample_job_data():
    """Sample job data for testing.

    Returns:
        Dict: Sample job data dictionary.
    """
    return {
        "job_id": "test-job-123",
        "job_website": "test-site",
        "role_title": "Senior Python Developer",
        "company_name": "Tech Corp",
        "location": "Remote",
        "job_url": "https://example.com/job/123",
        "salary_range": "$100,000 - $120,000",
        "job_description": "We are looking for a Senior Python Developer to join our team.",
        "requirements": "- 5+ years Python experience\n- Experience with Django/Flask",
        "additional_data": {
            "benefits": "- Health insurance\n- 401k matching",
            "job_type": "Full-time",
            "experience_level": "Senior",
            "company_size": "50-100 employees",
            "work_type": "Remote",
        },
    }


@pytest.fixture
def sample_job_instance(test_db_session, sample_job_data):
    """Create a sample job instance in the database.

    Args:
        test_db_session: Test database session.
        sample_job_data: Sample job data fixture.

    Returns:
        Job: Job instance created in the test database.
    """
    job = Job(**sample_job_data)
    test_db_session.add(job)
    test_db_session.commit()
    return job


@pytest.fixture
def multiple_jobs_data():
    """Multiple job data samples for testing.

    Returns:
        List[Dict]: List of job data dictionaries.
    """
    base_data = {
        "job_website": "test-site",
        "company_name": "Tech Corp",
        "location": "Remote",
        "job_description": "Test job description",
        "additional_data": {"job_type": "Full-time"},
    }

    jobs = []
    for i in range(5):
        job_data = base_data.copy()
        job_data.update(
            {
                "job_id": f"test-job-{i}",
                "role_title": f"Developer {i}",
                "job_url": f"https://example.com/job/{i}",
                "salary_range": f"${80000 + i * 10000} - ${90000 + i * 10000}",
            }
        )
        jobs.append(job_data)

    return jobs


@pytest.fixture
def test_site_config():
    """Sample site configuration for testing.

    Returns:
        SiteConfig: Test site configuration.
    """
    return SiteConfig(
        name="test-site",
        enabled=True,
        base_url="https://test-site.com",
        search_url="https://test-site.com/jobs",
        max_pages=5,
        delay_range=(1, 3),
        headers={"User-Agent": "Test Agent"},
    )


@pytest.fixture
def mock_requests_session():
    """Mock requests session for testing HTTP requests.

    Yields:
        Mock: Mocked requests session instance.
    """
    with patch("requests.Session") as mock_session:
        mock_instance = Mock()
        mock_session.return_value = mock_instance

        # Default successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test content</body></html>"
        mock_response.content = b"<html><body>Test content</body></html>"
        mock_response.headers = {"Content-Type": "text/html"}
        mock_instance.get.return_value = mock_response

        yield mock_instance


@pytest.fixture
def mock_beautiful_soup():
    """Mock Beautiful Soup for testing HTML parsing.

    Yields:
        Mock: Mocked BeautifulSoup instance.
    """
    with patch("bs4.BeautifulSoup") as mock_soup:
        mock_instance = Mock()
        mock_soup.return_value = mock_instance

        # Default mock soup structure
        mock_instance.find_all.return_value = []
        mock_instance.find.return_value = None
        mock_instance.get_text.return_value = "Test text"

        yield mock_instance


@pytest.fixture
def mock_datetime():
    """Mock datetime for testing time-dependent functions.

    Yields:
        Mock: Mocked datetime class.
    """
    test_time = datetime(2024, 1, 15, 12, 0, 0)
    with patch("datetime.datetime") as mock_dt:
        mock_dt.now.return_value = test_time
        mock_dt.utcnow.return_value = test_time
        mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        yield mock_dt


@pytest.fixture
def sample_html_content():
    """Sample HTML content for testing scrapers.

    Returns:
        str: HTML content with job listings.
    """
    return """
    <html>
        <body>
            <div class="job-listing">
                <h2 class="job-title">Senior Python Developer</h2>
                <div class="company-name">Tech Corp</div>
                <div class="location">Remote</div>
                <div class="salary">$100,000 - $120,000</div>
                <div class="description">
                    We are looking for a Senior Python Developer...
                </div>
                <a href="/job/123" class="job-link">View Job</a>
            </div>
            <div class="job-listing">
                <h2 class="job-title">Junior Developer</h2>
                <div class="company-name">StartupCo</div>
                <div class="location">San Francisco</div>
                <div class="salary">$70,000 - $85,000</div>
                <div class="description">
                    Entry-level position for new graduates...
                </div>
                <a href="/job/124" class="job-link">View Job</a>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def sample_job_detail_html():
    """Sample detailed job HTML content.

    Returns:
        str: HTML content for job detail page.
    """
    return """
    <html>
        <body>
            <div class="job-detail">
                <h1>Senior Python Developer</h1>
                <div class="company-info">
                    <h2>Tech Corp</h2>
                    <p>Company Size: 50-100 employees</p>
                </div>
                <div class="job-description">
                    <h3>Job Description</h3>
                    <p>We are looking for a Senior Python Developer to join our team...</p>
                </div>
                <div class="requirements">
                    <h3>Requirements</h3>
                    <ul>
                        <li>5+ years Python experience</li>
                        <li>Experience with Django/Flask</li>
                    </ul>
                </div>
                <div class="benefits">
                    <h3>Benefits</h3>
                    <ul>
                        <li>Health insurance</li>
                        <li>401k matching</li>
                    </ul>
                </div>
                <div class="job-meta">
                    <p>Experience Level: Senior</p>
                    <p>Job Type: Full-time</p>
                    <p>Work Type: Remote</p>
                </div>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def temp_log_file():
    """Create a temporary log file for testing.

    Yields:
        str: Path to temporary log file.
    """
    with tempfile.NamedTemporaryFile(
        mode="w+", suffix=".log", delete=False
    ) as tmp_file:
        tmp_file.write("Test log content\n")
        tmp_file.flush()
        yield tmp_file.name

    # Clean up
    if os.path.exists(tmp_file.name):
        os.unlink(tmp_file.name)


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset any singleton instances between tests.

    Yields:
        None: Fixture runs automatically before each test.
    """
    yield
    # Add any singleton reset logic here if needed


# Additional fixtures for new test modules


@pytest.fixture
def job_instance_with_hash():
    """Create a job instance with pre-computed content hash for testing."""
    from src.database.models.job import Job

    job = Job(
        job_id="test-hash-job",
        job_website="test-site",
        role_title="Data Scientist",
        company_name="AI Corp",
        location="San Francisco, CA",
        salary_range="$120,000 - $150,000",
        job_description="Build ML models and analyze data.",
        requirements="PhD in CS or related field",
        additional_data={"benefits": "Health, Dental", "work_type": "Remote"},
    )
    job.content_hash = job.generate_content_hash()
    return job


@pytest.fixture
def invalid_job_data():
    """Sample invalid job data for testing error cases."""
    return {
        # Missing required fields
        "company_name": "Test Company",
        "location": "Test Location",
        # Missing job_id, role_title, job_website
    }


@pytest.fixture
def mock_selenium_driver():
    """Mock Selenium WebDriver for testing scraper functionality."""
    with patch("selenium.webdriver.Chrome") as mock_chrome:
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        # Mock basic driver methods
        mock_driver.get.return_value = None
        mock_driver.quit.return_value = None
        mock_driver.page_source = "<html><body>Test content</body></html>"
        mock_driver.set_window_size.return_value = None
        mock_driver.execute_script.return_value = None

        yield mock_driver


@pytest.fixture
def mock_user_agent():
    """Mock UserAgent for testing anti-detection features."""
    with patch("fake_useragent.UserAgent") as mock_ua:
        mock_instance = Mock()
        mock_instance.random = "Mozilla/5.0 (Test Browser) Test/1.0"
        mock_ua.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def hirebase_sample_html():
    """Sample HTML content that matches Hirebase structure."""
    return """
    <html>
        <body>
            <div class="mb-4">
                <div class="bg-white rounded-xl p-6">
                    <a class="group" href="/company/techcorp/jobs/123">
                        <h2>Senior Data Scientist</h2>
                    </a>
                    <a href="/company/techcorp">
                        <h3>TechCorp</h3>
                    </a>
                    <div class="flex items-center gap-1">
                        <svg class="lucide-map-pin"></svg>
                        <span>San Francisco, CA</span>
                    </div>
                    <div class="job-salary">$120,000 - $150,000</div>
                    <h4>About</h4>
                    <p>We are looking for a data scientist to join our team.</p>
                    <h4>Requirements</h4>
                    <p>5+ years of experience with Python and ML.</p>
                </div>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def hirebase_detail_html():
    """Sample HTML content for Hirebase job detail page."""
    return """
    <html>
        <body>
            <div class="job-detail">
                <h1>Senior Data Scientist</h1>
                <h3>About the Company</h3>
                <p>TechCorp is a leading AI company with 100-500 employees.</p>
                
                <h3>Job Description</h3>
                <div class="prose">
                    <p>We are seeking a Senior Data Scientist to lead our ML initiatives.</p>
                    <h2>Requirements</h2>
                    <ul>
                        <li>5+ years Python experience</li>
                        <li>PhD in Computer Science</li>
                    </ul>
                </div>
                
                <h3>Job Details</h3>
                <div>
                    <p>Work Type: Remote</p>
                    <p>Employment Type: Full-time</p>
                </div>
                
                <div class="benefits">
                    <h3>Benefits</h3>
                    <ul>
                        <li>Health insurance</li>
                        <li>401k matching</li>
                    </ul>
                </div>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def mock_config_site():
    """Mock SiteConfig for testing scrapers."""
    from config.sites.sites_config import SiteConfig

    return SiteConfig(
        name="test-site",
        base_url="https://test-site.com",
        search_url="https://test-site.com/jobs?page={page}",
        enabled=True,
        max_pages=3,
        delay_range=(0.1, 0.2),  # Short delays for testing
        timeout=5,
        pagination_param="page",
        pagination_start=1,
    )


@pytest.fixture
def empty_soup():
    """BeautifulSoup object with no job listings for testing edge cases."""
    from bs4 import BeautifulSoup

    return BeautifulSoup("<html><body></body></html>", "html.parser")


@pytest.fixture
def job_data_variations():
    """Various job data samples for comprehensive testing."""
    return [
        # Complete job data
        {
            "job_id": "complete-job-1",
            "job_website": "test-site",
            "role_title": "Software Engineer",
            "company_name": "Tech Corp",
            "location": "Remote",
            "job_url": "https://example.com/job/1",
            "salary_range": "$80,000 - $100,000",
            "job_description": "Build web applications",
            "requirements": "2+ years experience",
            "additional_data": {"benefits": "Health insurance"},
        },
        # Minimal required fields only
        {
            "job_id": "minimal-job-2",
            "job_website": "test-site",
            "role_title": "Developer",
        },
        # Job with special characters
        {
            "job_id": "special-job-3",
            "job_website": "test-site",
            "role_title": "Senior Engineer (Python/ML)",
            "company_name": "AI & Data Co.",
            "location": "San Francisco, CA",
            "salary_range": "$150K-$200K",
            "job_description": "Work with cutting-edge ML/AI technologies & big data.",
        },
    ]


# AIDEV-NOTE: Test configuration provides comprehensive fixtures for:
# - Database testing with in-memory SQLite
# - Mock HTTP requests and HTML parsing
# - Sample data for various test scenarios
# - Time mocking for consistent test results
# - Temporary file management for file system tests
# - Selenium WebDriver mocking for scraper tests
# - Job model testing with various data scenarios
# - Site-specific HTML samples for scraper validation
