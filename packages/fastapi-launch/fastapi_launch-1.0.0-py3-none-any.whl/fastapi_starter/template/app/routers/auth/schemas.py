from pydantic import BaseModel, EmailStr


class RegistrationForm(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str


class LoginForm(BaseModel):
    email: EmailStr
    password: str


class RefreshToken(BaseModel):
    refresh_token: str


class ChangePassword(BaseModel):
    existing_password: str
    new_password: str
