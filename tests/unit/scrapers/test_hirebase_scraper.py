"""Unit tests for Hirebase scraper."""

from unittest.mock import Mock, patch

import pytest
from bs4 import BeautifulSoup

from src.scrapers.sites.hirebase_scraper import HirebaseScraper


class TestHirebaseScraper:
    """Test cases for the HirebaseScraper class."""

    def _create_scraper(self, mock_config_site):
        """Helper method to create properly mocked HirebaseScraper."""
        with patch(
            "src.scrapers.sites.hirebase_scraper.SeleniumBaseScraper.__init__",
            return_value=None,
        ):
            scraper = HirebaseScraper(mock_config_site)
            # Manually set the required attributes that would be set by parent __init__
            scraper.config = mock_config_site
            scraper.logger = Mock()
            return scraper

    def test_init(self, mock_config_site):
        """Test HirebaseScraper initialization.

        Args:
            mock_config_site: Mock SiteConfig fixture.
        """
        scraper = self._create_scraper(mock_config_site)

        assert scraper.job_card_selector == "div.mb-4 > div.bg-white.rounded-xl.p-6"
        assert scraper.job_title_selector == "a.group h2"
        assert scraper.company_selector == 'a[href^="/company/"] h3'
        assert (
            scraper.location_selector
            == "div.flex.items-center.gap-1:has(svg.lucide-map-pin) span"
        )

    def test_get_job_elements_primary_selector(
        self, mock_config_site, hirebase_sample_html
    ):
        """Test job element extraction with primary selector.

        Args:
            mock_config_site: Mock SiteConfig fixture.
            hirebase_sample_html: Sample Hirebase HTML fixture.
        """
        soup = BeautifulSoup(hirebase_sample_html, "html.parser")

        scraper = self._create_scraper(mock_config_site)
        elements = scraper.get_job_elements(soup)

        assert len(elements) == 1
        assert elements[0].name == "div"
        assert "bg-white" in elements[0].get("class", [])

    def test_get_job_elements_fallback_selectors(self, mock_config_site, empty_soup):
        """Test job element extraction with fallback selectors.

        Args:
            mock_config_site: Mock SiteConfig fixture.
            empty_soup: Empty BeautifulSoup fixture.
        """
        # Add HTML that only matches fallback selectors
        html = """
        <html>
            <body>
                <div class="bg-white rounded-xl">
                    <h2>Engineer</h2>
                    <a href="/company/test/jobs/123">Job Link</a>
                </div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")

        scraper = self._create_scraper(mock_config_site)
        elements = scraper.get_job_elements(soup)

        assert len(elements) >= 1

    def test_get_job_elements_no_jobs_found(self, mock_config_site, empty_soup):
        """Test job element extraction when no jobs are found.

        Args:
            mock_config_site: Mock SiteConfig fixture.
            empty_soup: Empty BeautifulSoup fixture.
        """
        scraper = self._create_scraper(mock_config_site)
        elements = scraper.get_job_elements(empty_soup)

        assert len(elements) == 0

    def test_parse_job_listing_success(self, mock_config_site, hirebase_sample_html):
        """Test successful job listing parsing.

        Args:
            mock_config_site: Mock SiteConfig fixture.
            hirebase_sample_html: Sample Hirebase HTML fixture.
        """
        soup = BeautifulSoup(hirebase_sample_html, "html.parser")
        job_element = soup.select_one("div.bg-white.rounded-xl.p-6")

        scraper = self._create_scraper(mock_config_site)
        job_data = scraper.parse_job_listing(job_element, "https://hirebase.org")

        assert job_data is not None
        assert job_data["role_title"] == "Senior Data Scientist"
        assert job_data["company_name"] == "TechCorp"
        assert job_data["location"] == "San Francisco, CA"
        assert "job_id" in job_data
        assert "job_url" in job_data

    def test_parse_job_listing_empty_element(self, mock_config_site):
        """Test job listing parsing with empty element.

        Args:
            mock_config_site: Mock SiteConfig fixture.
        """
        empty_html = "<div></div>"
        soup = BeautifulSoup(empty_html, "html.parser")
        job_element = soup.find("div")

        scraper = self._create_scraper(mock_config_site)
        job_data = scraper.parse_job_listing(job_element, "https://hirebase.org")

        assert job_data is None

    def test_parse_job_listing_no_title(self, mock_config_site):
        """Test job listing parsing when no title is found.

        Args:
            mock_config_site: Mock SiteConfig fixture.
        """
        html = """
        <div class="bg-white rounded-xl p-6">
            <div>No title here</div>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        job_element = soup.find("div")

        scraper = self._create_scraper(mock_config_site)
        job_data = scraper.parse_job_listing(job_element, "https://hirebase.org")

        assert job_data is None

    def test_extract_job_title_primary_selector(self, mock_config_site):
        """Test job title extraction with primary selector.

        Args:
            mock_config_site: Mock SiteConfig fixture.
        """
        html = """
        <div>
            <a class="group" href="/job/123">
                <h2>Machine Learning Engineer</h2>
            </a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("div")

        scraper = self._create_scraper(mock_config_site)
        title = scraper._extract_job_title(element)

        assert title == "Machine Learning Engineer"

    def test_extract_job_title_fallback_selectors(self, mock_config_site):
        """Test job title extraction with fallback selectors.

        Args:
            mock_config_site: Mock SiteConfig fixture.
        """
        html = """
        <div>
            <a href="/job/123">
                <h2>Data Analyst</h2>
            </a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("div")

        scraper = self._create_scraper(mock_config_site)
        title = scraper._extract_job_title(element)

        assert title == "Data Analyst"

    def test_extract_job_title_no_title_found(self, mock_config_site):
        """Test job title extraction when no title is found.

        Args:
            mock_config_site: Mock SiteConfig fixture.
        """
        html = "<div><p>No title here</p></div>"
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("div")

        scraper = self._create_scraper(mock_config_site)
        title = scraper._extract_job_title(element)

        assert title is None

    def test_looks_like_job_title_valid_titles(self, mock_config_site):
        """Test job title validation with valid titles.

        Args:
            mock_config_site: Mock SiteConfig fixture.
        """
        scraper = self._create_scraper(mock_config_site)

        valid_titles = [
            "Software Engineer",
            "Senior Data Scientist",
            "Machine Learning Specialist",
            "AI Research Director",
            "Backend Developer",
            "DevOps Engineer",
        ]

        for title in valid_titles:
            assert scraper._looks_like_job_title(title) is True

    def test_looks_like_job_title_invalid_titles(self, mock_config_site):
        """Test job title validation with invalid titles.

        Args:
            mock_config_site: Mock SiteConfig fixture.
        """
        scraper = self._create_scraper(mock_config_site)

        invalid_titles = [
            "",  # Empty
            "abc",  # Too short
            "A" * 101,  # Too long
            "About Us",  # Not a job title
            "Contact",  # Not a job title
        ]

        for title in invalid_titles:
            assert scraper._looks_like_job_title(title) is False

    def test_extract_company_name_primary_selector(self, mock_config_site):
        """Test company name extraction with primary selector.

        Args:
            mock_config_site: Mock SiteConfig fixture.
        """
        html = """
        <div>
            <a href="/company/techcorp">
                <h3>TechCorp Inc</h3>
            </a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("div")

        scraper = self._create_scraper(mock_config_site)
        company = scraper._extract_company_name(element)

        assert company == "TechCorp Inc"

    def test_extract_company_name_fallback(self, mock_config_site):
        """Test company name extraction with fallback logic.

        Args:
            mock_config_site: Mock SiteConfig fixture.
        """
        html = """
        <div>
            <h3>Startup Company</h3>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("div")

        scraper = self._create_scraper(mock_config_site)
        company = scraper._extract_company_name(element)

        assert company == "Startup Company"

    def test_extract_company_name_not_found(self, mock_config_site):
        """Test company name extraction when not found.

        Args:
            mock_config_site: Mock SiteConfig fixture.
        """
        html = "<div><p>No company here</p></div>"
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("div")

        scraper = self._create_scraper(mock_config_site)
        company = scraper._extract_company_name(element)

        assert company == "Unknown Company"

    def test_extract_location_primary_selector(self, mock_config_site):
        """Test location extraction with primary selector.

        Args:
            mock_config_site: Mock SiteConfig fixture.
        """
        html = """
        <div>
            <div class="flex items-center gap-1">
                <svg class="lucide-map-pin"></svg>
                <span>Austin, TX</span>
            </div>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("div")

        scraper = self._create_scraper(mock_config_site)
        location = scraper._extract_location(element)

        assert location == "Austin, TX"

    def test_extract_location_pattern_matching(self, mock_config_site):
        """Test location extraction using pattern matching.

        Args:
            mock_config_site: Mock SiteConfig fixture.
        """
        html = """
        <div>
            <p>Located in Seattle, WA, United States</p>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("div")

        scraper = self._create_scraper(mock_config_site)
        location = scraper._extract_location(element)

        assert "Seattle, WA" in location or "Remote" in location

    def test_extract_location_remote(self, mock_config_site):
        """Test location extraction for remote positions.

        Args:
            mock_config_site: Mock SiteConfig fixture.
        """
        html = "<div>Work from anywhere - Remote position</div>"
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("div")

        scraper = self._create_scraper(mock_config_site)
        location = scraper._extract_location(element)

        assert location == "Remote"

    def test_extract_job_url_primary_selector(self, mock_config_site):
        """Test job URL extraction with primary selector.

        Args:
            mock_config_site: Mock SiteConfig fixture.
        """
        html = """
        <div>
            <a class="group" href="/company/techcorp/jobs/123">Job Link</a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("div")

        scraper = self._create_scraper(mock_config_site)
        url = scraper._extract_job_url(element, "https://hirebase.org")

        assert url == "https://test-site.com/company/techcorp/jobs/123"

    def test_extract_job_url_fallback(self, mock_config_site):
        """Test job URL extraction with fallback selector.

        Args:
            mock_config_site: Mock SiteConfig fixture.
        """
        html = """
        <div>
            <a href="/company/startup/jobs/456">Job Link</a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("div")

        scraper = self._create_scraper(mock_config_site)
        url = scraper._extract_job_url(element, "https://hirebase.org")

        assert url == "https://test-site.com/company/startup/jobs/456"

    def test_extract_job_url_not_found(self, mock_config_site):
        """Test job URL extraction when no URL is found.

        Args:
            mock_config_site: Mock SiteConfig fixture.
        """
        html = "<div><p>No links here</p></div>"
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("div")

        scraper = self._create_scraper(mock_config_site)
        url = scraper._extract_job_url(element, "https://hirebase.org")

        assert url is None

    def test_extract_description_with_sections(self, mock_config_site):
        """Test description extraction with About and Requirements sections.

        Args:
            mock_config_site: Mock SiteConfig fixture.
        """
        html = """
        <div>
            <h4>About</h4>
            <p>We are a cutting-edge AI company.</p>
            <h4>Requirements</h4>
            <p>5+ years of Python experience required.</p>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("div")

        scraper = self._create_scraper(mock_config_site)
        description = scraper._extract_description(element)

        assert "About: We are a cutting-edge AI company." in description
        assert "Requirements: 5+ years of Python experience required." in description

    def test_extract_description_fallback(self, mock_config_site):
        """Test description extraction fallback to all text.

        Args:
            mock_config_site: Mock SiteConfig fixture.
        """
        html = "<div><p>General job description without specific sections.</p></div>"
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("div")

        scraper = self._create_scraper(mock_config_site)
        description = scraper._extract_description(element)

        assert "General job description without specific sections." in description

    def test_extract_description_truncation(self, mock_config_site):
        """Test description extraction truncates long text.

        Args:
            mock_config_site: Mock SiteConfig fixture.
        """
        long_text = "A" * 2500  # Longer than 2000 char limit
        html = f"<div><p>{long_text}</p></div>"
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("div")

        scraper = self._create_scraper(mock_config_site)
        description = scraper._extract_description(element)

        assert len(description) <= 2003  # 2000 + "..."
        assert description.endswith("...")

    def test_extract_salary_various_formats(self, mock_config_site):
        """Test salary extraction with various formats.

        Args:
            mock_config_site: Mock SiteConfig fixture.
        """
        salary_tests = [
            ("<div>Salary: $100,000 - $120,000</div>", "$100,000 - $120,000"),
            ("<div>Pay: $90,000+</div>", "$90,000+"),
            ("<div>90k - 110k USD</div>", "90k - 110k"),
            ("<div>Compensation: 100,000 - 150,000 USD</div>", "100,000 - 150,000 USD"),
        ]

        scraper = self._create_scraper(mock_config_site)

        for html, expected in salary_tests:
            soup = BeautifulSoup(html, "html.parser")
            element = soup.find("div")
            salary = scraper._extract_salary(element)
            assert expected in salary if salary else False

    def test_extract_salary_not_found(self, mock_config_site):
        """Test salary extraction when no salary is found.

        Args:
            mock_config_site: Mock SiteConfig fixture.
        """
        html = "<div><p>No salary information</p></div>"
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("div")

        scraper = self._create_scraper(mock_config_site)
        salary = scraper._extract_salary(element)

        assert salary is None

    def test_generate_job_id(self, mock_config_site):
        """Test job ID generation.

        Args:
            mock_config_site: Mock SiteConfig fixture.
        """
        scraper = self._create_scraper(mock_config_site)

        job_id1 = scraper._generate_job_id("test-identifier-1")
        job_id2 = scraper._generate_job_id("test-identifier-2")
        job_id3 = scraper._generate_job_id("test-identifier-1")  # Same as first

        assert len(job_id1) == 12
        assert len(job_id2) == 12
        assert job_id1 != job_id2
        assert job_id1 == job_id3  # Same input = same output

    def test_has_next_page_with_jobs(self, mock_config_site, hirebase_sample_html):
        """Test pagination logic when jobs are found.

        Args:
            mock_config_site: Mock SiteConfig fixture.
            hirebase_sample_html: Sample Hirebase HTML fixture.
        """
        soup = BeautifulSoup(hirebase_sample_html, "html.parser")

        scraper = self._create_scraper(mock_config_site)
        has_next = scraper.has_next_page(soup, 1)

        assert has_next is True  # Page 1 of 3 max, with jobs found

    def test_has_next_page_no_jobs(self, mock_config_site, empty_soup):
        """Test pagination logic when no jobs are found.

        Args:
            mock_config_site: Mock SiteConfig fixture.
            empty_soup: Empty BeautifulSoup fixture.
        """
        scraper = self._create_scraper(mock_config_site)
        has_next = scraper.has_next_page(empty_soup, 1)

        assert has_next is False

    def test_has_next_page_max_pages_reached(
        self, mock_config_site, hirebase_sample_html
    ):
        """Test pagination logic when max pages is reached.

        Args:
            mock_config_site: Mock SiteConfig fixture.
            hirebase_sample_html: Sample Hirebase HTML fixture.
        """
        soup = BeautifulSoup(hirebase_sample_html, "html.parser")

        scraper = self._create_scraper(mock_config_site)
        has_next = scraper.has_next_page(soup, 3)  # At max pages

        assert has_next is False

    def test_supports_detail_pages(self, mock_config_site):
        """Test that Hirebase scraper supports detail pages.

        Args:
            mock_config_site: Mock SiteConfig fixture.
        """
        scraper = self._create_scraper(mock_config_site)

        assert scraper.supports_detail_pages() is True

    def test_get_wait_element(self, mock_config_site):
        """Test wait element selector for React app.

        Args:
            mock_config_site: Mock SiteConfig fixture.
        """
        scraper = self._create_scraper(mock_config_site)
        wait_element = scraper._get_wait_element()

        assert "div.bg-white.rounded-xl" in wait_element
        assert "job-card" in wait_element

    def test_extract_job_details_from_soup(
        self, mock_config_site, hirebase_detail_html
    ):
        """Test detailed job extraction from detail page.

        Args:
            mock_config_site: Mock SiteConfig fixture.
            hirebase_detail_html: Sample detail page HTML fixture.
        """
        soup = BeautifulSoup(hirebase_detail_html, "html.parser")

        scraper = self._create_scraper(mock_config_site)
        details = scraper._extract_job_details_from_soup(soup)

        assert details is not None
        assert "about_company" in details
        assert "detailed_job_description" in details
        assert "benefits" in details
        assert "work_type" in details
        assert "job_type" in details

    def test_extract_company_section(self, mock_config_site):
        """Test company section extraction from detail page.

        Args:
            mock_config_site: Mock SiteConfig fixture.
        """
        html = """
        <div>
            <h3>About the Company</h3>
            <p>We are a innovative startup focused on AI solutions.</p>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")

        scraper = self._create_scraper(mock_config_site)
        company_info = scraper._extract_company_section(soup)

        assert "innovative startup focused on AI solutions" in company_info

    def test_extract_work_type(self, mock_config_site):
        """Test work type extraction.

        Args:
            mock_config_site: Mock SiteConfig fixture.
        """
        work_type_tests = [
            ("<div>This is a remote position</div>", "Remote"),
            ("<div>Hybrid work environment</div>", "Hybrid"),
            ("<div>On-site work required</div>", "On-site"),
            (
                "<div>Remote work with hybrid options</div>",
                "Hybrid",
            ),  # Remote + hybrid = Hybrid
        ]

        scraper = self._create_scraper(mock_config_site)

        for html, expected in work_type_tests:
            soup = BeautifulSoup(html, "html.parser")
            work_type = scraper._extract_work_type(soup)
            assert work_type == expected

    def test_extract_job_type(self, mock_config_site):
        """Test job type extraction.

        Args:
            mock_config_site: Mock SiteConfig fixture.
        """
        job_type_tests = [
            ("<div>Full-time position</div>", "Full-time"),
            ("<div>Part time role</div>", "Part-time"),
            ("<div>Contract work</div>", "Contract"),
            ("<div>Freelance opportunity</div>", "Freelance"),
            ("<div>Internship program</div>", "Internship"),
        ]

        scraper = self._create_scraper(mock_config_site)

        for html, expected in job_type_tests:
            soup = BeautifulSoup(html, "html.parser")
            job_type = scraper._extract_job_type(soup)
            assert job_type == expected

    @patch("time.sleep")
    def test_wait_for_page_load(self, mock_sleep, mock_config_site):
        """Test React app page load waiting.

        Args:
            mock_sleep: Mock sleep function.
            mock_config_site: Mock SiteConfig fixture.
        """
        mock_driver = Mock()
        mock_wait = Mock()

        with patch("selenium.webdriver.support.ui.WebDriverWait") as mock_wait_class:
            mock_wait_class.return_value = mock_wait

            scraper = self._create_scraper(mock_config_site)
            scraper.driver = mock_driver

            # Should not raise exception
            scraper._wait_for_page_load()

            mock_sleep.assert_called()  # Should call sleep for additional waiting
