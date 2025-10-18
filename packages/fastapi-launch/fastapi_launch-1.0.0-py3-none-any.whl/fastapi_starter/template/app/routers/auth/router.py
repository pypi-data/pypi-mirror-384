# pyright: reportUnknownMemberType=false
from datetime import UTC, datetime
from typing import Annotated

import jwt
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import models
from app.db.session import get_db
from app.lib.config import settings
from app.lib.limiter import limiter
from app.routers.auth.functions import (
    ALGORITHM,
    RefreshTokenPayload,
    authenticate_credentials,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    hash_password,
    return_auth_tokens,
)
from app.routers.auth.schemas import ChangePassword, LoginForm, RefreshToken, RegistrationForm

router = APIRouter()


@router.post("/register")
async def register(registration_form: RegistrationForm, db: Annotated[AsyncSession, Depends(get_db)]) -> dict[str, str]:
    existing_user = await db.execute(select(models.Users).where(models.Users.email == registration_form.email).limit(1))
    existing_user = existing_user.scalar()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    new_user = models.Users(
        email=registration_form.email,
        hashed_password=hash_password(registration_form.password),
        first_name=registration_form.first_name,
        last_name=registration_form.last_name,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {"message": "User registered successfully"}


@router.post("/token")
@limiter.limit("5/minute")  # pyright: ignore[reportUntypedFunctionDecorator]
async def login(login_form: LoginForm, db: Annotated[AsyncSession, Depends(get_db)], request: Request) -> dict[str, str | datetime]:  # noqa: ARG001  # pyright: ignore[reportUnusedParameter]
    email = login_form.email
    password = login_form.password

    unauthenticated_user = await db.execute(select(models.Users).where(models.Users.email == email).limit(1))
    unauthenticated_user = unauthenticated_user.scalar()

    if not unauthenticated_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not registered")

    user = await authenticate_credentials(unauthenticated_user, password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is not active")

    access_token = create_access_token(user)
    refresh_token = await create_refresh_token(user, db=db)

    return return_auth_tokens(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh")
async def refresh(credentials: RefreshToken, db: Annotated[AsyncSession, Depends(get_db)]) -> dict[str, str | datetime]:
    try:
        payload: RefreshTokenPayload = jwt.decode(credentials.refresh_token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if payload.get("token_type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    db_session = await db.execute(
        select(models.Sessions)
        .where(
            models.Sessions.id == int(payload["jti"]),
            models.Sessions.revoked.is_(False),
            models.Sessions.expires_at > datetime.now(UTC),
            models.Sessions.user_id == int(payload["sub"]),
        )
        .options(selectinload(models.Sessions.user))
        .limit(1)
    )
    result = db_session.scalar()

    if not result or not result.user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if not result.user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is not active")

    await db.commit()

    access_token = create_access_token(result.user)
    return return_auth_tokens(access_token=access_token)


@router.post("/logout")
async def logout(credentials: RefreshToken, db: Annotated[AsyncSession, Depends(get_db)]) -> dict[str, str]:
    try:
        payload: RefreshTokenPayload = jwt.decode(credentials.refresh_token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if payload.get("token_type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    await db.execute(update(models.Sessions).where(models.Sessions.id == int(payload.get("jti"))).values(revoked=True))
    await db.commit()

    return {"message": "success"}


@router.post("/change-password")
async def change_password(
    user_id: Annotated[int, Depends(authenticate_user)], db: Annotated[AsyncSession, Depends(get_db)], change_password: ChangePassword
) -> dict[str, str]:
    unauthenticated_user = await db.execute(select(models.Users).where(models.Users.id == user_id).limit(1))
    unauthenticated_user = unauthenticated_user.scalar_one()

    user = await authenticate_credentials(unauthenticated_user, change_password.existing_password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")

    user.hashed_password = hash_password(change_password.new_password)
    await db.commit()
    return {"message": "success"}
