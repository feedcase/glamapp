from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from redis import asyncio as aioredis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from starlette.middleware.cors import CORSMiddleware
from webdriver_manager.chrome import ChromeDriverManager

from dependencies import get_config, UserNotFound, waiter_wrapper
from routers import instagram

config = get_config()

app = FastAPI()

app.include_router(instagram.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGIN,
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
    environment = config.ENVIRONMENT
    debug = config.DEBUG
    show_docs_environments = ("local", "staging")
    redis_host = config.REDIS_HOST
    redis_port = config.REDIS_PORT
    if environment not in show_docs_environments:
        app.openapi_url = None
    app.title = "GlamAI Test Task"
    app.debug = debug
    redis = aioredis.from_url(url=f"redis://{redis_host}:{redis_port}", encoding="utf8", decode_responses=True)
    FastAPICache.init(backend=RedisBackend(redis=redis), prefix="fastapi-cache")
