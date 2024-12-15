from typing import Optional

from fastapi_cache.decorator import cache
from selenium.common import ElementClickInterceptedException
from selenium.webdriver.common.by import By

from src.common.services.selenoid import SelenoidBrowser
from src.config import get_settings
from src.media.constants import INST_URL
from src.media.enums import InstagramLoginSelectors, InstagramMediaTypesSelectors, InstagramNextButtonSelectors
from src.media.exceptions import UserNotFound
from src.media.schemas import InstagramLinksSchema


class InstagramDriver:
    def __init__(self, driver: SelenoidBrowser, url: str | None = None):
        self.driver: SelenoidBrowser = driver
        self.url = url or INST_URL

    async def login_instagram(self):
        """
        Login instagram
        """
        await self.driver.get_url(url=self.url)
        settings = get_settings()
        username_field = await self.driver.find_element(by=By.CSS_SELECTOR,
                                                        value=InstagramLoginSelectors.USERNAME.value())
        password_field = await self.driver.find_element(by=By.CSS_SELECTOR,
                                                        value=InstagramLoginSelectors.PASSWORD.value())
        username_field.clear()
        password_field.clear()
        username_field.send_keys(settings.INST_USERNAME)
        password_field.send_keys(settings.INST_PASSWORD)
        submit_button = await self.driver.find_element(by=By.CSS_SELECTOR,
                                                       value=InstagramLoginSelectors.SUBMIT_BUTTON.value())
        submit_button.click()
        save_password_button = await self.driver.find_element(by=By.XPATH,
                                                              value=InstagramLoginSelectors.NOT_NOW_BUTTON.value())
        if save_password_button:
            save_password_button.click()
        notification_popup_button = await self.driver.find_element(by=By.XPATH,
                                                                   value=InstagramLoginSelectors.NOT_NOW_BUTTON.value())
        if notification_popup_button:
            notification_popup_button.click()

    async def validate_user(self, username: str):
        """
        Validates user existence

        :param username: Instagram username

        :raises UserNotFound: if user page not exists
        """
        account_url = f"{self.url}/{username}"
        await self.driver.get_url(url=account_url)
        posts_tab = await self.driver.find_element(by=By.XPATH,
                                                   value=InstagramLoginSelectors.POST_TAB.value())
        if posts_tab is None:
            raise UserNotFound(username=username)

    async def get_profile(self, username: str):
        """
        Opens passed url in current driver page

        :param username: Instagram username
        """
        await self.validate_user(username=username)
        account_url = f"{self.url}/{username}"
        await self.driver.get_url(url=account_url)

    @cache(15)
    async def get_post_type(self) -> InstagramMediaTypesSelectors:
        """
        Gets post content type

        :returns: post media type
        """
        if "?img_index" in self.driver.web_browser.current_url:
            post_type = InstagramMediaTypesSelectors.CAROUSEL
        else:
            post_type = InstagramMediaTypesSelectors.CLIP
            if await self.driver.find_element(by=By.XPATH,
                                              value=InstagramMediaTypesSelectors.PHOTO.value):
                post_type = InstagramMediaTypesSelectors.PHOTO
        return post_type

    async def next_element(self, button_selector: InstagramNextButtonSelectors,
                           tries: int = 1) -> bool:
        """
        Switches to next element if button exists

        :param button_selector: Next button selector
        :param tries: max tries

        :returns: is last element
        """
        end = True
        for _ in range(tries):
            next_button = await self.driver.find_element(by=By.CSS_SELECTOR,
                                                         value=button_selector.value)
            if next_button:
                try:
                    next_button.click()
                except ElementClickInterceptedException:
                    self.driver.web_browser.execute_script(
                        "arguments[0].click();", next_button)
                end = False
                break
        return end

    async def get_carousel_media(self, media_type: InstagramMediaTypesSelectors,
                                 max_count: int = 1) -> InstagramLinksSchema:
        """
        Gets carousel media urls

        :param max_count: posts max count
        :param media_type: expected media type

        :returns:
        """
        carousel_media_links = []
        last_slide = False
        while not last_slide and len(carousel_media_links) < max_count:
            carousel_element = await self.driver.find_element(by=By.XPATH,
                                                              value="//div[@role='presentation']/"
                                                                    "/ul/li[contains(@tabindex, '1')]"
                                                                    f"[last(){-1 if not last_slide else ''}]")
            slide_media = await self.driver.find_element(by=By.XPATH,
                                                         value=media_type.value,
                                                         element=carousel_element)
            if slide_media:
                carousel_media_links.append(slide_media.get_attribute("src"))
            last_slide = await self.next_element(button_selector=InstagramNextButtonSelectors.SLIDE,
                                                 tries=3)
        return InstagramLinksSchema(urls=carousel_media_links)

    @cache(expire=15)
    async def get_profile_media_urls(self, username: str, media_type: InstagramMediaTypesSelectors,
                                     max_count: Optional[int] = None) -> InstagramLinksSchema:
        """
        Gets Instagram media urls

        :param username: Instagram username
        :param max_count: posts max count
        :param media_type: expected media type

        :returns: list of media urls
        """
        medias = []
        if max_count > 0:
            await self.get_profile(username=username)
            latest_post = await self.driver.find_element(by=By.CSS_SELECTOR,
                                                         value="a[href*='/p/']")
            if latest_post:
                latest_post.click()
                last_post = False
                while len(medias) < max_count and not last_post:
                    post_type = await self.get_post_type()
                    if post_type == media_type:
                        medias.append((await self.driver.find_element(
                            by=By.XPATH, value=media_type.value)).get_attribute("src"))
                    if post_type == InstagramMediaTypesSelectors.CAROUSEL:
                        carousel_media = await self.get_carousel_media(media_type=media_type,
                                                                       max_count=1)
                        if carousel_media.urls:
                            medias.append(carousel_media.urls[0])
                    last_post = await self.next_element(button_selector=InstagramNextButtonSelectors.POST)

        return InstagramLinksSchema(urls=medias)
