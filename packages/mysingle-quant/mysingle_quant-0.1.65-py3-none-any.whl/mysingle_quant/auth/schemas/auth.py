from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, Field

from ...core.config import settings
from .user import UserResponse


class LoginResponse(BaseModel):
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str | None = None
    user_info: UserResponse

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "string",
                "refresh_token": "string",
                "token_type": "bearer",
                "user_info": {
                    "id": "string",
                    "email": "user@example.com",
                    "full_name": "string",
                    "is_active": True,
                    "is_superuser": False,
                    "is_verified": False,
                },
            }
        }


class OAuth2AuthorizeResponse(BaseModel):
    authorization_url: str

    class Config:
        json_schema_extra = {
            "example": {
                "authorization_url": "https://example.com/oauth/authorize?response_type=code&client_id=your_client_id&redirect_uri=your_redirect_uri&scope=your_scope"
            }
        }


now = datetime.now(UTC)
access_exp = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
refresh_exp = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
default_audience = [settings.DEFAULT_AUDIENCE]


class AccessTokenData(BaseModel):
    sub: str
    email: str | None = None
    exp: int = Field(default_factory=lambda: int(access_exp.timestamp()))
    iat: int = Field(default_factory=lambda: int(now.timestamp()))
    aud: list[str] = Field(default_factory=lambda: default_audience)
    type: str = "access"


class RefreshTokenData(BaseModel):
    sub: str
    exp: int = Field(default_factory=lambda: int(refresh_exp.timestamp()))
    iat: int = Field(default_factory=lambda: int(now.timestamp()))
    aud: list[str] = Field(default_factory=lambda: default_audience)
    type: str = "refresh"
