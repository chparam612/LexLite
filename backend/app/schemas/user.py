from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime


class TokenData(BaseModel):
    uid: str
    email: str
    display_name: Optional[str] = None


class UserBase(BaseModel):
    email: EmailStr
    display_name: Optional[str] = None


class UserCreate(UserBase):
    firebase_uid: str


class UserResponse(UserBase):
    id: str
    firebase_uid: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: Optional[str] = None


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
