from fastapi import Depends, FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from redis import asyncio as aioredis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from dependencies import get_config, UserNotFound
from routers import instagram


app = FastAPI()

app.include_router(instagram.router)

@app.exception_handler(UserNotFound)
def inst_user_not_found_handler(request: Request, exc: UserNotFound):
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                        content=jsonable_encoder({"detail": exc.message}))

@app.on_event("startup")
async def startup_event():
    config = get_config()
    ENVIRONMENT = config("ENVIRONMENT", default="local")
    DEBUG = config("DEBUG", cast=bool, default=False)
    SHOW_DOCS_ENVIRONMENT = ("local", "staging")
    REDIS_URL = config("REDIS_URL", cast=str, default="redis://localhost")
    if ENVIRONMENT not in SHOW_DOCS_ENVIRONMENT:
        app.openapi_url = None
    app.title = "GlamAI Test Task"
    app.debug = DEBUG
    redis = aioredis.from_url(url=REDIS_URL, encoding="utf8", decode_responses=True)
    FastAPICache.init(backend=RedisBackend(redis=redis), prefix="fastapi-cache")
    Depends
