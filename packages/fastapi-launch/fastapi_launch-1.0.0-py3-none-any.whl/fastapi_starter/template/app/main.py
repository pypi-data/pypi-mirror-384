from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.db.session import close_db
from app.lib.config import settings
from app.routers.auth.router import router as auth_router
from app.routers.user.router import router as user_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    yield
    await close_db()


app = FastAPI(lifespan=lifespan)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:  # noqa: ARG001  # pyright: ignore[reportUnusedParameter]
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests, please try again in a minute"},
        headers={"X-RateLimit-Limit": exc.detail},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(user_router, prefix="/user", tags=["User"])
