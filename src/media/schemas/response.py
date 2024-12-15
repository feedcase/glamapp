from typing import List, Optional

from pydantic import AnyUrl

from src.common.schemas import BaseResponseSchema


class InstagramLinksSchema(BaseResponseSchema):
    """Instagram links model"""
    urls: List[Optional[AnyUrl]] = []


class UrlsCreateResponseSchema(BaseResponseSchema):
    ids: Optional[List[int]] = []
