from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from nys_schemas.auth_schema import RoleEnum

class UserSchema(BaseModel):
    idx: int
    username: str
    email: EmailStr
    role: RoleEnum
    password_expires_at: Optional[datetime] = None
    otp: Optional[str] = None
    otp_expires_at: Optional[datetime] = None

    class Config:
        orm_mode = True
