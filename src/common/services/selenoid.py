import logging
from typing import Optional, List

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from src.common.utils.decorators import waiter_wrapper


class SelenoidBrowser:
    def __init__(
            self,
            options: Options,
            host_ip=None,
            hub_port=None,
            **kwargs,
    ):
        self.web_browser: Optional[webdriver.Chrome] = None
        self.options: Options = options
        self.host_ip = host_ip
        self.hub_port = hub_port
        self.executor_url = f'http://{self.host_ip}:{self.hub_port}/wd/hub'
        self.kwargs = kwargs

    def __enter__(self):
        logging.info(f'Starting selenoid_session on "{self.executor_url}"...')
        try:
            self.web_browser = webdriver.Remote(
                command_executor=self.executor_url,
                options=self.options,
                keep_alive=True,
                **self.kwargs,
            )
            logging.info(f'Selenoid session successfully started!\n'
                         f'Session: {self.web_browser.session_id}')
            return self
        except Exception as e:
            logging.error(f'Failed to start selenoid session: {e}')
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.info('Stopping selenoid session...')
        if self.web_browser:
            try:
                self.web_browser.quit()
                logging.info('Selenoid session successfully stopped!')
            except Exception as e:
                logging.error(f'Failed to stop selenoid session: {e}')
        logging.warning('Selenoid session is already closed!')

    async def find_element(self, by: By, value: str, tries: int = 10,
                           element: Optional[WebElement] = None) -> Optional[WebElement]:
        """
        Finds element by selector on active driver page

        :param by: selector type
        :param value: selector value
        :param tries: number of tries
        :param element: WebElement instance for search

        :returns: Needed element if exists
        """
        result_element = None
        driver = element or self.web_browser
        try:
            result_element = await (waiter_wrapper(top_attempts=tries)
                                    (driver.find_element)
                                    (by=by, value=value))
        except NoSuchElementException:
            pass
        return result_element

    async def find_elements(self, by: By, value: str) -> List[Optional[WebElement]]:
        """
        Finds elements by selector on active driver page

        :param by: selector type
        :param value: selector value

        :returns: Needed elements if exists
        """
        elements = []
        try:
            elements = await (waiter_wrapper()
                              (self.web_browser.find_elements)
                              (by=by, value=value))
        except NoSuchElementException:
            pass
        return elements

    async def get_url(self, url: str):
        """
        Opens passed url in current driver page

        :param url: page url
        """
        self.web_browser.get(url=url)
