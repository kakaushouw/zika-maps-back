from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

# Profile Schemas
class ProfileBase(BaseModel):
    display_name: Optional[str] = None
    phone: Optional[str] = None

    class Config:
        from_attributes = True

class ProfileCreate(ProfileBase):
    pass

class ProfileResponse(ProfileBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# User Schemas
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    role: str = "citizen" # 'citizen' ou 'agent'

class UserResponse(UserBase):
    id: str
    created_at: datetime
    roles: List[str] = []
    profile: Optional[ProfileBase] = None

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    user: UserResponse

class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    roles: List[str] = []

# Report Schemas
class ReportBase(BaseModel):
    description: str
    address: Optional[str] = None
    lat: float
    lng: float
    image_url: Optional[str] = None

class ReportCreate(ReportBase):
    pass

class ReportUpdateStatus(BaseModel):
    status: str # 'pending', 'confirmed', 'resolved', 'discarded'

class ReportResponse(BaseModel):
    id: str
    user_id: str
    description: str
    address: Optional[str] = None
    status: str
    date: date
    lat: float
    lng: float
    image_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ResetPasswordRequest(BaseModel):
    email: EmailStr

class UpdatePasswordRequest(BaseModel):
    password: str

