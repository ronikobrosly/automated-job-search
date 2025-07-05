"""Unit tests for base scraper classes."""

import time
from unittest.mock import Mock, patch, MagicMock

import pytest
import requests
from bs4 import BeautifulSoup

from src.scrapers.base_scraper import AntiDetectionMixin, SeleniumMixin


class TestAntiDetectionMixin:
    """Test cases for the AntiDetectionMixin class."""

    def test_init_creates_session_and_user_agent(self):
        """Test that initialization creates session and user agent."""
        mixin = AntiDetectionMixin()

        assert mixin.session is not None
        assert mixin.ua is not None
        assert hasattr(mixin.session, "get")

    @patch("src.scrapers.base_scraper.UserAgent")
    def test_get_random_user_agent_success(self, mock_ua_class):
        """Test successful user agent generation.

        Args:
            mock_ua_class: Mock UserAgent class.
        """
        mock_ua = Mock()
        mock_ua.random = "Mozilla/5.0 (Test) Browser/1.0"
        mock_ua_class.return_value = mock_ua

        mixin = AntiDetectionMixin()
        user_agent = mixin._get_random_user_agent()

        assert user_agent == "Mozilla/5.0 (Test) Browser/1.0"

    @patch("src.scrapers.base_scraper.UserAgent")
    def test_get_random_user_agent_fallback(self, mock_ua_class):
        """Test user agent fallback when UserAgent fails.

        Args:
            mock_ua_class: Mock UserAgent class.
        """
        mock_ua = Mock()
        mock_ua.random = Mock(side_effect=Exception("UserAgent failed"))
        mock_ua_class.return_value = mock_ua

        mixin = AntiDetectionMixin()
        user_agent = mixin._get_random_user_agent()

        # Should return one of the fallback agents (string, not Mock)
        assert isinstance(user_agent, str)
        assert user_agent.startswith("Mozilla/5.0")
        assert "Chrome" in user_agent or "Firefox" in user_agent

    def test_get_random_headers_with_base_headers(self):
        """Test random header generation with base headers."""
        mixin = AntiDetectionMixin()
        base_headers = {"Custom-Header": "custom-value"}

        headers = mixin._get_random_headers(base_headers)

        assert "Custom-Header" in headers
        assert headers["Custom-Header"] == "custom-value"
        assert "User-Agent" in headers
        assert "Accept-Language" in headers
        assert "Accept-Encoding" in headers

    def test_get_random_headers_without_base_headers(self):
        """Test random header generation without base headers."""
        mixin = AntiDetectionMixin()

        headers = mixin._get_random_headers()

        assert "User-Agent" in headers
        assert "Accept-Language" in headers
        assert "Accept-Encoding" in headers
        # Should have random variations
        assert headers["Accept-Language"] in [
            "en-US,en;q=0.9",
            "en-US,en;q=0.8,es;q=0.7",
            "en-GB,en;q=0.9",
            "en-US,en;q=0.5",
        ]

    @patch("time.sleep")
    def test_random_delay(self, mock_sleep):
        """Test random delay functionality.

        Args:
            mock_sleep: Mock sleep function.
        """
        mixin = AntiDetectionMixin()

        mixin._random_delay((1.0, 2.0))

        mock_sleep.assert_called_once()
        # Verify delay was between 1.0 and 2.0 seconds
        delay_time = mock_sleep.call_args[0][0]
        assert 1.0 <= delay_time <= 2.0

    @patch("requests.Session")
    def test_make_request_success(self, mock_session_class):
        """Test successful HTTP request.

        Args:
            mock_session_class: Mock Session class.
        """
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        mixin = AntiDetectionMixin()
        mixin.session = mock_session

        response = mixin._make_request("https://example.com")

        assert response == mock_response
        mock_session.get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()

    @patch("requests.Session")
    def test_make_request_rate_limited(self, mock_session_class):
        """Test request handling when rate limited.

        Args:
            mock_session_class: Mock Session class.
        """
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 429  # Rate limited
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        mixin = AntiDetectionMixin()
        mixin.session = mock_session

        with patch("time.sleep") as mock_sleep:
            response = mixin._make_request("https://example.com")

        assert response is None
        mock_sleep.assert_called_once()

    @patch("requests.Session")
    def test_make_request_blocked(self, mock_session_class):
        """Test request handling when blocked (403, 503).

        Args:
            mock_session_class: Mock Session class.
        """
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 403  # Forbidden
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        mixin = AntiDetectionMixin()
        mixin.session = mock_session

        response = mixin._make_request("https://example.com")

        assert response is None

    @patch("requests.Session")
    def test_make_request_exception(self, mock_session_class):
        """Test request handling when exception occurs.

        Args:
            mock_session_class: Mock Session class.
        """
        mock_session = Mock()
        mock_session.get.side_effect = requests.exceptions.RequestException(
            "Network error"
        )
        mock_session_class.return_value = mock_session

        mixin = AntiDetectionMixin()
        mixin.session = mock_session

        response = mixin._make_request("https://example.com")

        assert response is None

    def test_make_detail_request_with_delay(self):
        """Test detail request with delay functionality."""
        mixin = AntiDetectionMixin()

        with (
            patch.object(mixin, "_random_delay") as mock_delay,
            patch.object(mixin, "_make_request") as mock_request,
        ):
            mock_request.return_value = Mock()

            response = mixin._make_detail_request(
                "https://example.com/job/123", (1.0, 2.0)
            )

            mock_delay.assert_called_once_with((1.0, 2.0))
            mock_request.assert_called_once_with("https://example.com/job/123")

    def test_make_detail_request_without_delay(self):
        """Test detail request without delay."""
        mixin = AntiDetectionMixin()

        with (
            patch.object(mixin, "_random_delay") as mock_delay,
            patch.object(mixin, "_make_request") as mock_request,
        ):
            mock_request.return_value = Mock()

            response = mixin._make_detail_request("https://example.com/job/123")

            mock_delay.assert_not_called()
            mock_request.assert_called_once_with("https://example.com/job/123")


class TestSeleniumMixin:
    """Test cases for the SeleniumMixin class."""

    @patch("src.scrapers.base_scraper.UserAgent")
    @patch("src.scrapers.base_scraper.webdriver.Chrome")
    @patch("src.scrapers.base_scraper.ChromeDriverManager")
    def test_init_creates_driver(self, mock_driver_manager, mock_chrome, mock_ua_class):
        """Test that initialization creates WebDriver.

        Args:
            mock_driver_manager: Mock ChromeDriverManager.
            mock_chrome: Mock Chrome WebDriver.
            mock_ua_class: Mock UserAgent class.
        """
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        mock_driver_manager.return_value.install.return_value = "/path/to/chromedriver"

        mixin = SeleniumMixin()

        assert mixin.driver == mock_driver
        assert mixin.wait is not None
        mock_driver.set_window_size.assert_called_with(1920, 1080)

    @patch("src.scrapers.base_scraper.UserAgent")
    @patch("src.scrapers.base_scraper.webdriver.Firefox")
    @patch("src.scrapers.base_scraper.GeckoDriverManager")
    def test_setup_firefox_driver(
        self, mock_driver_manager, mock_firefox, mock_ua_class
    ):
        """Test Firefox driver setup.

        Args:
            mock_driver_manager: Mock GeckoDriverManager.
            mock_firefox: Mock Firefox WebDriver.
            mock_ua_class: Mock UserAgent class.
        """
        mock_driver = Mock()
        mock_firefox.return_value = mock_driver
        mock_driver_manager.return_value.install.return_value = "/path/to/geckodriver"

        with patch.object(SeleniumMixin, "_setup_driver"):
            mixin = SeleniumMixin()
            firefox_driver = mixin._setup_firefox_driver()

        assert firefox_driver == mock_driver
        mock_firefox.assert_called_once()

    @patch("src.scrapers.base_scraper.UserAgent")
    def test_get_random_user_agent_selenium(self, mock_ua_class):
        """Test user agent generation in Selenium context.

        Args:
            mock_ua_class: Mock UserAgent class.
        """
        mock_ua = Mock()
        mock_ua.random = "Mozilla/5.0 (Selenium) Test/1.0"
        mock_ua_class.return_value = mock_ua

        with patch.object(SeleniumMixin, "_setup_driver"):
            mixin = SeleniumMixin()
            user_agent = mixin._get_random_user_agent()

        assert user_agent == "Mozilla/5.0 (Selenium) Test/1.0"

    @patch("src.scrapers.base_scraper.UserAgent")
    def test_get_random_user_agent_selenium_fallback(self, mock_ua_class):
        """Test user agent fallback in Selenium context.

        Args:
            mock_ua_class: Mock UserAgent class.
        """
        mock_ua = Mock()
        mock_ua.random = Mock(side_effect=Exception("UserAgent failed"))
        mock_ua_class.return_value = mock_ua

        with patch.object(SeleniumMixin, "_setup_driver"):
            mixin = SeleniumMixin()
            user_agent = mixin._get_random_user_agent()

        # Should return one of the fallback agents
        assert user_agent.startswith("Mozilla/5.0")

    @patch("time.sleep")
    def test_selenium_random_delay(self, mock_sleep):
        """Test Selenium-specific random delay.

        Args:
            mock_sleep: Mock sleep function.
        """
        with patch.object(SeleniumMixin, "_setup_driver"):
            mixin = SeleniumMixin()

            mixin._selenium_random_delay((0.5, 1.5))

            mock_sleep.assert_called_once()
            delay_time = mock_sleep.call_args[0][0]
            assert 0.5 <= delay_time <= 1.5

    @patch("src.scrapers.base_scraper.BeautifulSoup")
    def test_selenium_get_page_success(self, mock_soup_class):
        """Test successful page loading with Selenium.

        Args:
            mock_soup_class: Mock BeautifulSoup class.
        """
        mock_driver = Mock()
        mock_driver.page_source = "<html><body>Test</body></html>"
        mock_soup = Mock()
        mock_soup_class.return_value = mock_soup

        with (
            patch.object(SeleniumMixin, "_setup_driver"),
            patch("time.sleep"),
            patch("selenium.webdriver.common.action_chains.ActionChains"),
        ):
            mixin = SeleniumMixin()
            mixin.driver = mock_driver

            result = mixin._selenium_get_page("https://example.com")

            assert result == mock_soup
            mock_driver.get.assert_called_with("https://example.com")
            mock_soup_class.assert_called_with(
                "<html><body>Test</body></html>", "html.parser"
            )

    def test_selenium_get_page_with_wait_element(self):
        """Test page loading with wait element."""
        mock_driver = Mock()
        mock_driver.page_source = "<html><body>Test</body></html>"
        mock_wait = Mock()

        with (
            patch.object(SeleniumMixin, "_setup_driver"),
            patch("time.sleep"),
            patch("selenium.webdriver.common.action_chains.ActionChains"),
            patch("src.scrapers.base_scraper.BeautifulSoup") as mock_soup_class,
            patch("selenium.webdriver.support.ui.WebDriverWait") as mock_wait_class,
        ):
            mock_wait_class.return_value = mock_wait
            mock_soup = Mock()
            mock_soup_class.return_value = mock_soup

            mixin = SeleniumMixin()
            mixin.driver = mock_driver

            result = mixin._selenium_get_page(
                "https://example.com", wait_for_element=".job-card"
            )

            mock_wait.until.assert_called()

    def test_selenium_scroll_page(self):
        """Test page scrolling functionality."""
        mock_driver = Mock()

        with patch.object(SeleniumMixin, "_setup_driver"), patch("time.sleep"):
            mixin = SeleniumMixin()
            mixin.driver = mock_driver

            mixin._selenium_scroll_page(0.5)

            # Should call execute_script twice (scroll down, scroll up)
            assert mock_driver.execute_script.call_count == 2

    def test_close_driver_success(self):
        """Test successful driver closure."""
        mock_driver = Mock()

        with patch.object(SeleniumMixin, "_setup_driver"):
            mixin = SeleniumMixin()
            mixin.driver = mock_driver

            mixin.close_driver()

            mock_driver.quit.assert_called_once()
            assert mixin.driver is None
            assert mixin.wait is None

    def test_close_driver_exception(self):
        """Test driver closure when exception occurs."""
        mock_driver = Mock()
        mock_driver.quit.side_effect = Exception("Driver quit failed")

        with patch.object(SeleniumMixin, "_setup_driver"):
            mixin = SeleniumMixin()
            mixin.driver = mock_driver

            # Should not raise exception
            mixin.close_driver()

            assert mixin.driver is None
            assert mixin.wait is None

    def test_close_driver_no_driver(self):
        """Test driver closure when no driver exists."""
        with patch.object(SeleniumMixin, "_setup_driver"):
            mixin = SeleniumMixin()
            mixin.driver = None

            # Should not raise exception
            mixin.close_driver()

    def test_del_method_calls_close_driver(self):
        """Test that __del__ method calls close_driver."""
        with (
            patch.object(SeleniumMixin, "_setup_driver"),
            patch.object(SeleniumMixin, "close_driver") as mock_close,
        ):
            mixin = SeleniumMixin()
            mixin.__del__()

            mock_close.assert_called_once()

    @patch("src.scrapers.base_scraper.webdriver.Chrome")
    @patch("src.scrapers.base_scraper.ChromeDriverManager")
    def test_setup_chrome_driver_headless(self, mock_driver_manager, mock_chrome):
        """Test Chrome driver setup in headless mode.

        Args:
            mock_driver_manager: Mock ChromeDriverManager.
            mock_chrome: Mock Chrome WebDriver.
        """
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        mock_driver_manager.return_value.install.return_value = "/path/to/chromedriver"

        with (
            patch.object(SeleniumMixin, "_setup_driver"),
            patch.object(
                SeleniumMixin, "_get_random_user_agent", return_value="test-agent"
            ),
        ):
            mixin = SeleniumMixin()
            chrome_driver = mixin._setup_chrome_driver(headless=True)

            assert chrome_driver == mock_driver
            mock_chrome.assert_called_once()

    @patch("src.scrapers.base_scraper.webdriver.Chrome")
    @patch("src.scrapers.base_scraper.ChromeDriverManager")
    def test_setup_chrome_driver_non_headless(self, mock_driver_manager, mock_chrome):
        """Test Chrome driver setup in non-headless mode.

        Args:
            mock_driver_manager: Mock ChromeDriverManager.
            mock_chrome: Mock Chrome WebDriver.
        """
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        mock_driver_manager.return_value.install.return_value = "/path/to/chromedriver"

        with (
            patch.object(SeleniumMixin, "_setup_driver"),
            patch.object(
                SeleniumMixin, "_get_random_user_agent", return_value="test-agent"
            ),
        ):
            mixin = SeleniumMixin()
            chrome_driver = mixin._setup_chrome_driver(headless=False)

            assert chrome_driver == mock_driver
            mock_chrome.assert_called_once()
