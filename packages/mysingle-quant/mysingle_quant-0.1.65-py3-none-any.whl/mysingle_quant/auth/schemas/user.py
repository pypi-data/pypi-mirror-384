from beanie import PydanticObjectId
from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    """Base User model."""

    _id: PydanticObjectId
    email: EmailStr
    full_name: str | None = None
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    avatar_url: str | None = None
    oauth_accounts: list["OAuthAccount"] = Field(default_factory=list)

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "_id": "string",
                "email": "user@example.com",
                "full_name": "string",
                "is_active": True,
                "is_superuser": False,
                "is_verified": False,
                "avatar_url": "string",
                "oauth_accounts": [
                    {
                        "_id": "string",
                        "oauth_name": "string",
                        "access_token": "string",
                        "expires_at": 1234567890,
                        "refresh_token": "string",
                        "account_id": "string",
                        "account_email": "user@example.com",
                    }
                ],
            }
        }


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str | None = None
    password: str
    is_active: bool | None = True
    is_superuser: bool | None = False
    is_verified: bool | None = False
    avatar_url: str | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "full_name": "string",
                "password": "string",
                "is_active": True,
                "is_superuser": False,
                "is_verified": False,
                "avatar_url": "string",
            }
        }


class UserUpdate(BaseModel):
    password: str | None = None
    email: EmailStr | None = None
    full_name: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    is_verified: bool | None = None
    avatar_url: str | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "full_name": "string",
                "password": "string",
                "is_active": True,
                "is_superuser": False,
                "is_verified": False,
                "avatar_url": "string",
            }
        }


class OAuthAccount(BaseModel):
    """Base OAuth account model."""

    _id: PydanticObjectId
    oauth_name: str
    access_token: str
    expires_at: int | None = None
    refresh_token: str | None = None
    account_id: str
    account_email: str

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "_id": "string",
                "oauth_name": "string",
                "access_token": "string",
                "expires_at": 1234567890,
                "refresh_token": "string",
                "account_id": "string",
                "account_email": "user@example.com",
            }
        }
