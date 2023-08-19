import os
from enum import Enum
from functools import lru_cache, wraps
from types import CoroutineType
from typing import List, Optional, Union

import asyncio
from fastapi_cache.decorator import cache
from pydantic import AnyUrl, BaseModel
from pydantic_settings import BaseSettings
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

INST_URL = "https://www.instagram.com"


class UserNotFound(Exception):
    """User not found exception"""
    message = ""
    reason = "User not found"

    def __init__(self, *args, **kwargs):
        args = list(args)
        if len(args) > 0:
            self.message = str(args.pop(0))
        for key in list(kwargs.keys()):
            setattr(self, key, kwargs.pop(key))
        if not self.message:
            self.message = "{title} {body}".format(
                title=getattr(self, "reason", "Unknown"),
                body=getattr(self, "error_type", vars(self)),
            )
        super().__init__(self.message, *args, **kwargs)


class AppSettings(BaseSettings):
    DEBUG: bool = False
    ENVIRONMENT: str = "local"
    INST_USERNAME: str
    INST_PASSWORD: str
    REDIS_HOST: str
    REDIS_PORT: int


class InstagramLinksModel(BaseModel):
    """Instagram links model"""
    urls: List[Optional[AnyUrl]] = []


class InstagramMediaTypesSelectors(Enum):
    """
    Instagram media types selectors

    :returns: CSS selectors as value for needed media types
    """
    PHOTO = "//div[@role='button']//img[@style='object-fit: cover;']"
    CLIP = "//div//video"
    CAROUSEL = ""


class InstagramNextButtonSelectors(Enum):
    """
    Instagram Next button selectors

    :returns: CSS selectors as value for needed element type
    """
    POST = "svg[aria-label*='Next']"
    SLIDE = "button[aria-label*='Next']"


def waiter_wrapper(top_attempts: int = 10,
                   sleep_time: int = 1,
                   exp_exc: Optional[list] = None):
    """
    Tries to get result for top_attempts times

    :param top_attempts: max count of tries
    :param sleep_time: waiting time between attempts
    :param exp_exc: error to be ignored

    :returns:
    """
    exp_exc = exp_exc or []

    def wrapper(func):
        @wraps(func)
        async def inner(*args, **kwargs):
            attempts = 0
            while True:
                attempts += 1
                try:
                    result = func(*args, **kwargs)
                    if isinstance(result, CoroutineType):
                        result = await result
                except Exception as e:
                    if attempts >= top_attempts or type(e) in exp_exc:
                        raise e
                    await asyncio.sleep(sleep_time)
                    continue
                else:
                    return result

        return inner

    return wrapper


@lru_cache
def get_config() -> AppSettings:
    """Gets env config"""
    config = AppSettings()
    return config


async def create_driver() -> webdriver.Chrome:
    """Creates Chrome driver"""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1366,768")
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.headless = True
    chrome_options.add_experimental_option("prefs", prefs)
    with webdriver.Chrome(service=Service(os.path.join(os.getcwd(), "chromedriver/chromedriver")),
                          options=chrome_options) as chrome_driver:
        yield chrome_driver


async def find_element(driver: Union[webdriver.Chrome, WebElement],
                       by: By, value: str,
                       tries: int = 10) -> Optional[WebElement]:
    """
    Finds element by selector on active driver page

    :param driver: driver
    :param by: selector type
    :param value: selector value
    :param tries: number of tries

    :returns: Needed element if exists
    """
    element = None
    try:
        element = await waiter_wrapper(top_attempts=tries)(driver.find_element)(by=by, value=value)
    except NoSuchElementException:
        pass
    return element


async def find_elements(driver: webdriver.Chrome,
                        by: By,
                        value: str) -> List[Optional[WebElement]]:
    """
    Finds elements by selector on active driver page

    :param driver: driver
    :param by: selector type
    :param value: selector value

    :returns: Needed elements if exists
    """
    elements = []
    try:
        elements = await waiter_wrapper()(driver.find_elements)(by=by, value=value)
    except NoSuchElementException:
        pass
    return elements


async def get_url(driver: webdriver.Chrome,
                  url: str):
    """
    Opens passed url in current driver page

    :param driver: driver
    :param url: page url
    """
    driver.get(url=url)


async def login_instagram(driver: webdriver.Chrome):
    """
    Login instagram

    :param driver: driver
    """
    await get_url(url=INST_URL, driver=driver)
    config = get_config()
    username_field = await find_element(driver=driver, by=By.CSS_SELECTOR,
                                        value="input[name='username']")
    password_field = await find_element(driver=driver, by=By.CSS_SELECTOR,
                                        value="input[name='password']")
    username_field.clear()
    password_field.clear()
    username_field.send_keys(config.INST_USERNAME)
    password_field.send_keys(config.INST_PASSWORD)
    submit_button = await find_element(driver=driver, by=By.CSS_SELECTOR,
                                       value="button[type='submit']")
    submit_button.click()
    save_password = await find_element(driver=driver, by=By.XPATH,
                                       value="//button[contains(text(), 'Not Now')]")
    if save_password:
        save_password.click()
    notification_popup = await find_element(driver=driver, by=By.XPATH,
                                            value="//button[contains(text(), 'Not Now')]")
    if notification_popup:
        notification_popup.click()


async def validate_user(username: str,
                        driver: webdriver.Chrome):
    """
    Validates user existence

    :param username: Instagram username
    :param driver: driver

    :raises UserNotFound: if user page not exists 
    """
    try:
        await login_instagram(driver=driver)
    except NoSuchElementException:
        pass
    await get_url(url=f"{INST_URL}/{username}", driver=driver)
    posts_tab = await find_element(driver=driver, by=By.XPATH, value="//span[contains(text(), 'Posts')]")
    if posts_tab is None:
        raise UserNotFound(username=username)


async def get_profile(username: str,
                      driver: webdriver.Chrome):
    """
    Opens passed url in current driver page

    :param driver: driver
    :param username: Instagram username
    """
    await validate_user(username=username, driver=driver)
    await get_url(url=f"{INST_URL}/{username}", driver=driver)


@cache(15)
async def get_post_type(driver: webdriver.Chrome) -> InstagramMediaTypesSelectors:
    """
    Gets post content type

    :param driver: driver

    :returns: post media type
    """
    if "?img_index" in driver.current_url:
        post_type = InstagramMediaTypesSelectors.CAROUSEL
    else:
        post_type = InstagramMediaTypesSelectors.PHOTO if await find_element(
            driver=driver, by=By.XPATH,
            value=InstagramMediaTypesSelectors.PHOTO.value) else InstagramMediaTypesSelectors.CLIP
    return post_type


async def next_element(driver: webdriver.Chrome,
                       button_selector: InstagramNextButtonSelectors,
                       tries: int = 1) -> bool:
    """
    Switches to next element if button exists

    :param driver: driver
    :param button_selector: Next button selector
    :param tries: max tries

    :returns: is last element
    """
    end = True
    for _ in range(tries):
        next_button = await find_element(driver=driver, by=By.CSS_SELECTOR,
                                         value=button_selector.value)
        if next_button:
            try:
                next_button.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", next_button)
            end = False
            break
    return end


async def get_carousel_media(driver: webdriver.Chrome,
                             media_type: InstagramMediaTypesSelectors,
                             max_count: int = 1) -> InstagramLinksModel:
    """
    Gets carousel media urls

    :param driver: driver
    :param max_count: posts max count
    :param media_type: expected media type

    :returns:
    """
    carousel_media_links = []
    last_slide = False
    while not last_slide and len(carousel_media_links) < max_count:
        carousel_element = await find_element(
            driver=driver, by=By.XPATH,
            value=f"//div[@role='presentation']/"
                  f"/ul/li[contains(@tabindex, '1')][last(){-1 if not last_slide else ''}]")
        slide_media = await find_element(driver=carousel_element, by=By.XPATH, value=media_type.value)
        if slide_media:
            carousel_media_links.append(slide_media.get_attribute("src"))
        last_slide = await next_element(
            driver=driver, button_selector=InstagramNextButtonSelectors.SLIDE, tries=3)
    return InstagramLinksModel(urls=carousel_media_links)


@cache(expire=15)
async def get_profile_media_urls(username: str,
                                 media_type: InstagramMediaTypesSelectors,
                                 driver: webdriver.Chrome,
                                 max_count: Optional[int] = None) -> InstagramLinksModel:
    """
    Gets Instagram media urls

    :param driver: driver
    :param username: Instagram username
    :param max_count: posts max count
    :param media_type: expected media type

    :returns: list of media urls
    """
    medias = []
    await get_profile(username=username, driver=driver)
    if max_count != 0:
        latest_post = await find_element(driver=driver, by=By.CSS_SELECTOR, value="a[href*='/p/']")
        if latest_post:
            latest_post.click()
            last_post = False
            while len(medias) < max_count and not last_post:
                post_type = await get_post_type(driver=driver)
                if post_type == media_type:
                    medias.append((await find_element(driver=driver, by=By.XPATH,
                                                      value=media_type.value)).get_attribute("src"))
                if post_type == InstagramMediaTypesSelectors.CAROUSEL:
                    carousel_media = await get_carousel_media(driver=driver, media_type=media_type, max_count=1)
                    if carousel_media.urls:
                        medias.append(carousel_media.urls[0])
                last_post = await next_element(driver=driver, button_selector=InstagramNextButtonSelectors.POST)

    return InstagramLinksModel(urls=medias)
