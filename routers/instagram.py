from fastapi import APIRouter, Depends, status
from selenium import webdriver

from dependencies import InstagramLinksModel, InstagramMediaTypesSelectors, get_profile_media_urls, create_driver

router = APIRouter(tags=["instagram"])


@router.get(
    "/getPhotos",
    tags=["instagram"], 
    response_model=InstagramLinksModel, 
    status_code=status.HTTP_200_OK, 
    summary="Get user photos by username",
    responses={status.HTTP_400_BAD_REQUEST: {"description": "User not found"}}
    )
async def get_photos(username: str, max_count: int, driver: webdriver.Chrome = Depends(create_driver)):
    photos_urls = await get_profile_media_urls(username=username, media_type=InstagramMediaTypesSelectors.PHOTO, 
                                               max_count=max_count, driver=driver)
    return photos_urls
