from datetime import datetime

from pydantic import BaseModel, computed_field

from app.lib.enums import UserRole


class User(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    created_at: datetime
    updated_at: datetime
    role: UserRole
    is_active: bool

    @computed_field
    @property
    def name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @computed_field
    @property
    def initials(self) -> str:
        first = self.first_name[0].upper() if self.first_name else ""
        last = self.last_name[0].upper() if self.last_name else ""
        return f"{first}{last}"


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
