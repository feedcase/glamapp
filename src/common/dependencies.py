from selenium import webdriver

from src.common.services.selenoid import SelenoidBrowser
from src.config import get_settings


async def create_driver() -> SelenoidBrowser:
    """Creates Chrome driver"""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1366,768")
    chrome_options.add_argument("--headless")
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    settings = get_settings()
    with SelenoidBrowser(options=chrome_options,
                         host_ip=settings.SELENOID_HOST,
                         hub_port=settings.SELENOID_PORT) as chrome_driver:
        yield chrome_driver
