from pydantic import BaseModel, EmailStr, root_validator
from enum import Enum
from typing import Optional, List
from datetime import datetime

class LocaleEnum(str, Enum):
    en = "en"
    de = "de"

class RoleEnum(str, Enum):
    SUPER_ADMIN = "Super Admin"
    ADMIN = "Admin"
    USER = "User"

class SignupRequest(BaseModel):
    username: str
    email: EmailStr
    locale: Optional[LocaleEnum] = LocaleEnum.en  # Default is 'en', but can be 'de'
    role: RoleEnum = RoleEnum.USER

class SignUpResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    locale: Optional[LocaleEnum] = LocaleEnum.en

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str

class PasswordResetRequest(BaseModel):
    email: EmailStr
    old_password: str
    new_password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    locale: Optional[LocaleEnum] = LocaleEnum.en  # Default is 'en', but can be 'de'

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str
    otp: Optional[str] = None
    old_password: Optional[str] = None
    locale: Optional[str] = LocaleEnum.en
    
    @root_validator
    def check_reset_method(cls, values):
        """Ensure that either OTP or old_password is provided, but not both."""
        otp = values.get('otp')
        old_password = values.get('old_password')
        
        if bool(otp) == bool(old_password):  # Both are provided or both are missing
            raise ValueError("Exactly one of 'otp' or 'old_password' must be provided")
            
        return values

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class ApiKeyCreateInput(BaseModel):
    name: str

class ApiKeyCreateResponse(BaseModel):
    api_key: str

class ApiKeyInfo(BaseModel):
    id: int
    name: str
    api_key: str
    role: RoleEnum
    expires_at: datetime
    last_used: Optional[datetime]

class ApiKeysGetResponse(BaseModel):
    api_keys: List[ApiKeyInfo]

class ApiKeyDeleteResponse(BaseModel):
    message: str
    deleted_key: str
    deleted_key_id: int
    deleted_key_name: str
class UserUpdateRequest(BaseModel):
    email: EmailStr | None = None
    user_id: int | None = None
    username: str | None = None
    role: RoleEnum | None = None

class UserUpdateResponse(BaseModel):
    idx: int
    username: str
    email: EmailStr
    role: RoleEnum