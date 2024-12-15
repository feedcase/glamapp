from enum import Enum


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


class InstagramLoginSelectors(Enum):
    USERNAME = "input[name='username']"
    PASSWORD = "input[name='password']"
    SUBMIT_BUTTON = "button[type='submit']"
    NOT_NOW_BUTTON = "//button[contains(text(), 'Not Now')]"
    POST_TAB = "//span[contains(text(), 'Posts')]"
