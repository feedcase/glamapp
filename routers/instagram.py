from fastapi import APIRouter, status

from dependencies import InstagramPhotosLinksModel, get_instagram_user_photos

router = APIRouter()


@router.get(
    "/getPhotos",
    tags=["instagram"], 
    response_model=InstagramPhotosLinksModel, 
    status_code=status.HTTP_200_OK, 
    summary="Get user photos by username",
    responses={status.HTTP_400_BAD_REQUEST: "User not found"})
async def get_photos(username: str, max_count: int):
    response = await get_instagram_user_photos(username=username, max_count=max_count)
    return response
