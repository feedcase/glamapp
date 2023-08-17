from enum import Enum
from functools import lru_cache, wraps
from types import CoroutineType
from typing import List, Optional

import asyncio
from fastapi_cache.decorator import cache
from pydantic import AnyUrl, BaseModel
from starlette.config import Config
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common import by
from selenium.webdriver.remote.webelement import WebElement
from webdriver_manager.chrome import ChromeDriverManager

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


class InstagramLinksModel(BaseModel):
    """Instagram links model"""
    urls: List[Optional[AnyUrl]] = []


class InstagramMediaTypesSelectors(Enum):
    """
    Instagram media types selectors

    :returns: CSS selectors as value for needed media types
    """
    PHOTO = "img[style='object-fit: cover;']"
    CLIP = "video[type='video/mp4']"
    CAROUSEL = ""


async def anext(ait):
    return await ait.__anext__()


def waiter_wrapper(top_attempts=10, sleep_time=1, exp_exc=()):
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
def get_config() -> Config:
    """Gets env config"""
    config = Config(".env")
    return config


async def create_driver() -> webdriver.Chrome:
    """Creates Chrome driver"""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.headless = True
    chrome_options.add_experimental_option("prefs", prefs)
    with webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                          options=chrome_options) as chrome_driver:
        yield chrome_driver


async def find_element(driver: webdriver.Chrome, by: by.By, value: str) -> Optional[WebElement]:
    """
    Finds element by selector on active driver page

    :param driver: driver
    :param by: selector type
    :param value: selector value

    :returns: Needed element if exists
    """
    element = None
    try:
        element = await waiter_wrapper()(driver.find_element)(by=by, value=value)
    except NoSuchElementException:
        pass
    return element


async def find_elements(driver: webdriver.Chrome, by: by.By, value: str) -> List[Optional[WebElement]]:
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


async def get_url(driver: webdriver.Chrome, url: str):
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
    username_field = await find_element(driver=driver, by=by.By.CSS_SELECTOR,
                                        value="input[name='username']")
    password_field = await find_element(driver=driver, by=by.By.CSS_SELECTOR,
                                        value="input[name='password']")
    username_field.clear()
    password_field.clear()
    username_field.send_keys(config("INST_USERNAME"))
    password_field.send_keys(config("INST_PASSWORD"))
    submit_button = await find_element(driver=driver, by=by.By.CSS_SELECTOR,
                                       value="button[type='submit']")
    submit_button.click()
    save_password = await find_element(driver=driver, by=by.By.XPATH,
                                       value="//button[contains(text(), 'Not Now')]")
    if save_password:
        save_password.click()
    notification_popup = await find_element(driver=driver, by=by.By.XPATH,
                                            value="//button[contains(text(), 'Not Now')]")
    if notification_popup:
        notification_popup.click()


async def scroll_page(driver: webdriver.Chrome) -> bool:
    """
    Scrolls current page

    :param driver: driver

    :returns: Page ended or not
    """
    scrolldown = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);"
                                       "var scrolldown=document.body.scrollHeight;return scrolldown;")
    page_end = False
    while not page_end:
        last_count = scrolldown
        await asyncio.sleep(5)
        yield page_end
        scrolldown = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);"
                                           "var scrolldown=document.body.scrollHeight;return scrolldown;")
        if last_count == scrolldown:
            page_end = True
    yield True


async def validate_user(username: str, driver: webdriver.Chrome):
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
    posts_tab = await find_element(driver=driver, by=by.By.XPATH, value="//span[contains(text(), 'Posts')]")
    if posts_tab is None:
        raise UserNotFound(username=username)


async def get_profile(username: str, driver: webdriver.Chrome):
    """
    Opens passed url in current driver page

    :param driver: driver
    :param username: Instagram username
    """
    await validate_user(username=username, driver=driver)
    await get_url(url=f"{INST_URL}/{username}", driver=driver)


@cache(15)
async def get_post_media(post_url: str, media_type: InstagramMediaTypesSelectors,
                         driver: webdriver.Chrome) -> List[Optional[WebElement]]:
    """
    Gets Instagram post media

    :param driver: driver
    :param post_url: page url
    :param media_type: search selector

    :returns: list of elements if exists
    """
    await get_url(url=post_url, driver=driver)
    medias = await find_elements(driver=driver, by=by.By.CSS_SELECTOR, value=media_type.value)
    return medias


@cache(15)
async def validate_post_type(post_url: str, media_type: InstagramMediaTypesSelectors,
                             driver: webdriver.Chrome) -> bool:
    """
    Validates post content type

    :param driver: driver
    :param post_url: driver element
    :param media_type: needed media type

    :returns: post if media type matches with expected
    """
    post_types = {"clip": InstagramMediaTypesSelectors.CLIP,
                  "carousel": InstagramMediaTypesSelectors.CAROUSEL}
    original_url = driver.current_url
    try:
        post_element = await find_element(driver=driver, by=by.By.CSS_SELECTOR,
                                          value="a[href='%s']" % (post_url.replace(INST_URL, "")))
        svg = post_element.find_element(by=by.By.CSS_SELECTOR, value="svg")
        aria_label = svg.get_attribute("aria-label")
        post_type = post_types.get(aria_label.lower())
    except NoSuchElementException:
        post_type = InstagramMediaTypesSelectors.PHOTO
    if post_type == InstagramMediaTypesSelectors.CAROUSEL:
        if media_type == InstagramMediaTypesSelectors.CAROUSEL:
            return True
        medias = await get_post_media(post_url=post_url, media_type=media_type, driver=driver)
        await get_url(url=original_url, driver=driver)
        return bool(medias)

    return media_type == post_type


@cache(expire=15)
async def get_profile_posts_urls(username: str, driver: webdriver.Chrome, max_count: Optional[int] = None,
                                 posts_type: Optional[InstagramMediaTypesSelectors] = None) -> InstagramLinksModel:
    """
    Gets Instagram posts urls

    :param driver: driver
    :param username: Instagram username
    :param max_count: posts max count
    :param posts_type: expected posts media type

    :returns: list of posts urls
    """
    posts = []
    if max_count != 0:
        await get_profile(username=username, driver=driver)
        last_links = []
        page_end = False
        while len(posts) < max_count or not page_end:
            links = await find_elements(driver=driver, by=by.By.TAG_NAME, value="a")
            posts_urls = [post_url for link in links
                          if "/p/" in (post_url := link.get_attribute("href")) and post_url not in last_links]
            for link in posts_urls:
                if await validate_post_type(post_url=link, media_type=posts_type, driver=driver):
                    posts.append(link)
                if max_count == len(posts) or page_end:
                    break
            last_links = posts_urls
            page_end = await scroll_page(driver=driver)
    return InstagramLinksModel(urls=posts)


@cache(expire=15)
async def get_profile_media_urls(username: str, media_type: InstagramMediaTypesSelectors,
                                 driver: webdriver.Chrome, max_count: Optional[int] = None) -> InstagramLinksModel:
    """
    Gets Instagram media urls

    :param driver: driver
    :param username: Instagram username
    :param max_count: posts max count
    :param media_type: expected media type

    :returns: list of media urls
    """
    medias = []
    if max_count != 0:
        posts = await get_profile_posts_urls(username=username, driver=driver,
                                             max_count=max_count, posts_type=media_type)
        for post_url in posts.urls:
            if media := await get_post_media(post_url=post_url, media_type=media_type, driver=driver):
                medias.append(media[0].get_attribute("src"))
    return InstagramLinksModel(urls=medias)
