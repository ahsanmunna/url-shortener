from pydantic import BaseModel, AnyHttpUrl, field_validator
from typing import Optional
from datetime import datetime

class ShortenRequest(BaseModel):
    original_url: AnyHttpUrl
    is_ghost: Optional[bool] = False
    password: Optional[str] = None
    click_limit: Optional[int] = None
    expiry_date: Optional[datetime] = None

    @field_validator("click_limit")
    @classmethod
    def validate_click_limit(cls, v):
        if v is not None and v <= 0:
            raise ValueError("click_limit must be greater than 0")
        return v

    @field_validator("expiry_date")
    @classmethod
    def validate_expiry_date(cls, v):
        if v is not None and v <= datetime.now():
            raise ValueError("expiry_date must be in the future")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("password must not be whitespace only")
        return v

class VerifyRequest(BaseModel):
    password: str