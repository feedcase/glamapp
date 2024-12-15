from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi_cloud_drives import GoogleDriveConfig
from redis import asyncio as aioredis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from starlette.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.media.exceptions import UserNotFound
from src.media.router import router as inst_router

google_conf = {
    "CLIENT_ID_JSON": "client_id.json",
    "SCOPES": [
        "https://www.googleapis.com/auth/drive"
        ]
}

config = GoogleDriveConfig(**google_conf)

settings = get_settings()

app = FastAPI()

app.include_router(inst_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGIN,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(UserNotFound)
def inst_user_not_found_handler(request: Request, exc: UserNotFound):
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                        content=jsonable_encoder({"detail": exc.message}))


@app.on_event("startup")
async def startup_event():
    environment = settings.ENVIRONMENT
    debug = settings.DEBUG == "True"
    show_docs_environments = ("local", "staging")
    if environment not in show_docs_environments:
        app.openapi_url = None
    app.title = "Vsevo Inst Scrapper"
    app.debug = debug
    redis = aioredis.from_url(url=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
                              encoding="utf8",
                              decode_responses=True)
    FastAPICache.init(backend=RedisBackend(redis=redis),
                      prefix="fastapi-cache")
