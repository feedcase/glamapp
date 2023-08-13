from functools import lru_cache
from typing import List, Optional

from fastapi_cache.decorator import cache
from instagrapi import Client
from instagrapi.types import Media
from pydantic import AnyUrl, BaseModel
from starlette.config import Config


class InstagramPhotosLinksModel(BaseModel):
    urls: List[Optional[AnyUrl]] = []


@lru_cache
def get_config() -> Config:
    config = Config(".env")
    return config

@cache(expire=1800)
async def get_instagram_client() -> Client:
    config = get_config()
    inst_client = Client()
    if not (username := config("INST_USERNAME")):
        raise Exception("Instagram credentials are not provided")
    inst_client.login(username=username, password=config("INST_PASSWORD"))
    return inst_client

@cache()
async def get_instagram_user_id(username: str):
    client: Client = await get_instagram_client()
    user_id = client.user_info_by_username(username=username).pk
    return user_id

@cache(expire=15)
async def get_instagram_posts(user_id: str, max_count: int = 0):
    posts = []
    client: Client = await get_instagram_client()
    if max_count:
        posts: List[Media] = client.user_medias(user_id=user_id, amount=max_count)
    return posts

async def get_instagram_user_photos(username: str, max_count: int):
    posts_urls = []
    if max_count:
        user_id: str = await get_instagram_user_id(username=username)
        posts = await get_instagram_posts(user_id=user_id, max_count=max_count)
        posts_urls = [post.thumbnail_url or post.resources[0].thumbnail_url for post in posts]
    return InstagramPhotosLinksModel(urls=posts_urls)
