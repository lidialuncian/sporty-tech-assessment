import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from config import settings


def pytest_html_results_table_row(report, cells):
    """Remove passing and skipped tests from the HTML report — failures only."""
    if report.passed or report.skipped:
        del cells[:]


def build_chrome_driver():
    options = Options()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


@pytest.fixture(scope="function")
def driver():
    """Provides a Chrome WebDriver instance, tears it down after each test."""
    chrome = build_chrome_driver()
    chrome.implicitly_wait(settings.IMPLICIT_WAIT)
    chrome.set_page_load_timeout(settings.PAGE_LOAD_TIMEOUT)
    yield chrome
    chrome.quit()


@pytest.fixture(scope="function")
def app(driver):
    """Opens the app and returns a PlaceSingleBetPage ready to use."""
    from pages.place_single_bet_page import PlaceSingleBetPage

    page = PlaceSingleBetPage(driver)
    page.open()
    return page
