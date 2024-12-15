from fastapi import (
    APIRouter,
    Depends,
    status, HTTPException
)
from selenium.common import NoSuchElementException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.dependencies import create_driver
from src.common.services.selenoid import SelenoidBrowser
from src.dao.session_maker import TransactionSessionDep
from src.media.dao import (
    MediaCategoryDAO,
    MediaUrlDAO
)
from src.media.enums import InstagramMediaTypesSelectors
from src.media.schemas import (
    BaseResponseSchema,
    InstagramLinksSchema,
    CreateMediaUrlsSchema, UrlsCreateResponseSchema
)
from src.media.services import InstagramDriver

router = APIRouter(tags=["media"])


@router.get(
    "/getPhotos",
    tags=["media"],
    response_model=InstagramLinksSchema,
    status_code=status.HTTP_200_OK,
    summary="Get user photos by username",
    responses={status.HTTP_400_BAD_REQUEST: {"description": "User not found"}}
    )
async def get_photos(username: str, max_count: int, driver: SelenoidBrowser = Depends(create_driver)):
    instagram_driver = InstagramDriver(driver)
    try:
        await instagram_driver.login_instagram()
    except NoSuchElementException:
        pass
    photos_urls = await instagram_driver.get_profile_media_urls(username=username,
                                                                media_type=InstagramMediaTypesSelectors.PHOTO,
                                                                max_count=max_count,
                                                                driver=driver)
    return photos_urls


@router.post(
    "/saveMediaUrls",
    tags=["media"],
    response_model=UrlsCreateResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Save post url for category",
    responses={status.HTTP_400_BAD_REQUEST: {"description": "User not found"}}
    )
async def save_media_urls(add_data: CreateMediaUrlsSchema,
                          session: AsyncSession = TransactionSessionDep):
    media_dict = add_data.model_dump()
    category_name = media_dict.pop("category_name", "")
    category_id = media_dict.pop("category_id", "")
    urls = media_dict.pop("urls", [])
    try:
        if not category_id:
            category_ids = await MediaCategoryDAO.add_media_categories(session=session,
                                                                       category_names=[category_name])
            category_id = category_ids[0]
        media_urls_ids = await MediaUrlDAO.add_media_urls(session=session,
                                                          urls=urls,
                                                          category_id=category_id)
        return UrlsCreateResponseSchema(ids=media_urls_ids)
    except IntegrityError as e:
        if "UNIQUE constraint failed" in str(e.orig):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Media Url for Category {category_name | category_id} already exists")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Exception on Media Url creation")
