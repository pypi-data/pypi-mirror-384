from fastapi import Response

from ...core.config import settings


def set_cookie(
    response: Response,
    key: str,
    value: str,
    max_age: int,
) -> None:
    response.set_cookie(
        key=key,
        value=value,
        max_age=max_age,
        httponly=settings.ENVIRONMENT == "production",
        samesite="lax" if settings.ENVIRONMENT == "production" else None,
        secure=settings.ENVIRONMENT == "production",
    )


def delete_cookie(response: Response, key: str) -> None:
    response.delete_cookie(key)


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
) -> None:
    set_cookie(
        response,
        key="access_token",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    set_cookie(
        response,
        key="refresh_token",
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )
