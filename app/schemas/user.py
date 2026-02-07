from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models.user import UserRole


class UserBase(BaseModel):
    username: str
    email: EmailStr
    is_active: Optional[bool] = True
    role: Optional[UserRole] = UserRole.WORKER


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None


class UserInDBBase(UserBase):
    id: int

    class Config:
        from_attributes = True


class UserResponse(UserInDBBase):
    pass
