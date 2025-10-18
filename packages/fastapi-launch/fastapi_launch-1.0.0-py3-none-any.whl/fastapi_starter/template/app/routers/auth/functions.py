# pyright: reportUnknownMemberType=false
from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal, TypedDict

import jwt
from argon2 import PasswordHasher
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models
from app.lib.config import settings

ALGORITHM = "HS256"
REFRESH_TOKEN_EXPIRES_MINUTES = 60 * 24 * 7
ACCESS_TOKEN_EXPIRES_MINUTES = 10


ph = PasswordHasher()
security = HTTPBearer(auto_error=False)

TokenType = Literal["access", "refresh"]
TokenRole = Literal["admin", "user"]


class BaseTokenPayload(TypedDict):
    sub: str
    exp: int
    iat: int
    token_type: TokenType
    role: TokenRole


class AccessTokenPayload(BaseTokenPayload):
    pass


class RefreshTokenPayload(BaseTokenPayload):
    jti: str


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(hash: str, password: str) -> bool:
    try:
        ph.verify(hash, password)
    except Exception:
        return False
    else:
        return True


async def authenticate_credentials(unauthenticated_user: models.Users, password: str) -> models.Users | None:
    if unauthenticated_user and verify_password(unauthenticated_user.hashed_password, password):
        return unauthenticated_user
    return None


def create_access_token(user: models.Users) -> str:
    current_time = datetime.now(UTC)
    expire = current_time + timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES)
    to_encode: AccessTokenPayload = {
        "sub": str(user.id),
        "exp": int(expire.timestamp()),
        "iat": int(current_time.timestamp()),
        "token_type": "access",
        "role": user.role.value,
    }
    return jwt.encode(dict(to_encode), settings.JWT_SECRET_KEY, algorithm=ALGORITHM)


async def create_refresh_token(user: models.Users, db: AsyncSession) -> str:
    current_time = datetime.now(UTC)
    expire = current_time + timedelta(minutes=REFRESH_TOKEN_EXPIRES_MINUTES)
    result = await db.execute(
        insert(models.Sessions).values(
            user_id=user.id,
            expires_at=expire,
        )
    )
    await db.commit()
    session_id = result.inserted_primary_key[0] if result.inserted_primary_key else None

    to_encode: RefreshTokenPayload = {
        "sub": str(user.id),
        "exp": int(expire.timestamp()),
        "iat": int(current_time.timestamp()),
        "token_type": "refresh",
        "jti": str(session_id),
        "role": user.role.value,
    }
    return jwt.encode(dict(to_encode), settings.JWT_SECRET_KEY, algorithm=ALGORITHM)


def return_auth_tokens(access_token: str | None = None, refresh_token: str | None = None) -> dict[str, str | datetime]:
    response: dict[str, str | datetime] = {}
    current_time = datetime.now(UTC)
    if access_token:
        response["access_token"] = access_token
        response["access_token_expires_at"] = current_time + timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES)
    if refresh_token:
        response["refresh_token"] = refresh_token
        response["refresh_token_expires_at"] = current_time + timedelta(minutes=REFRESH_TOKEN_EXPIRES_MINUTES)
    return response


def authenticate_user(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]) -> int:
    access_token = credentials.credentials

    try:
        payload: AccessTokenPayload = jwt.decode(access_token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("token_type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        try:
            user_id = int(payload.get("sub", ""))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    except jwt.exceptions.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.exceptions.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is invalid")
    else:
        return user_id


def authenticate_admin(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]) -> int:
    user_id = authenticate_user(credentials)
    payload: AccessTokenPayload = jwt.decode(credentials.credentials, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not an admin")
    return user_id
