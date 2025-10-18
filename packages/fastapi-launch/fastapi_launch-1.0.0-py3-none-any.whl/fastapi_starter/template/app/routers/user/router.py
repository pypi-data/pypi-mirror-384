from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models
from app.db.session import get_db
from app.routers.auth.functions import authenticate_user
from app.routers.user.schemas import User, UserUpdate

router = APIRouter()


@router.get("")
async def read_user(
    user_id: Annotated[int, Depends(authenticate_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    user = await db.execute(select(models.Users).where(models.Users.id == user_id).limit(1))
    return User(**user.scalar_one().__dict__)


@router.put("")
async def update_user(user: UserUpdate, user_id: Annotated[int, Depends(authenticate_user)], db: Annotated[AsyncSession, Depends(get_db)]) -> dict[str, str]:
    db_user = await db.execute(select(models.Users).where(models.Users.id == user_id).limit(1))
    db_user = db_user.scalar_one()

    for key, value in user.model_dump(exclude_unset=True).items():
        setattr(db_user, key, value)

    await db.commit()

    return {"message": "success"}
