from http import HTTPStatus

from fastapi import status
from pydantic import BaseModel


class BaseResponseSchema(BaseModel):
    msg: str = HTTPStatus.OK.phrase
    status: int = status.HTTP_200_OK
