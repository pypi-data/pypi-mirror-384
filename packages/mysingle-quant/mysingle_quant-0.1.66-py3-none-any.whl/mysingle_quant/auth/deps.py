# path: app/api/deps.py

import logging

from beanie import PydanticObjectId
from fastapi import Cookie, Depends
from fastapi.security import OAuth2PasswordBearer

from ..core.config import settings
from .exceptions import (
    AuthorizationFailed,
    InvalidToken,
    UserInactive,
    UserNotExists,
)
from .models import User
from .security.jwt import decode_jwt
from .user_manager import UserManager

logger = logging.getLogger(__name__)

# --------------------------------------------------------
# 패스워드 기반 인증을 위한 OAuth2 설정
# --------------------------------------------------------
VERSION = settings.AUTH_API_VERSION

user_manager = UserManager()
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"/api/{VERSION}/auth/login", auto_error=False
)


def get_token_from_cookie_or_header(
    token_from_cookie: str | None = Cookie(None, alias="access_token"),
    token_from_header: str | None = Depends(reusable_oauth2),
) -> str:
    """
    1) 쿠키에 토큰이 있으면 그걸 사용
    2) 없으면 헤더에서 토큰 추출 (Bearer)
    3) 둘 다 없으면 403 에러
    """
    if token_from_cookie:
        return token_from_cookie
    if token_from_header:
        return token_from_header
    raise UserNotExists(identifier="token", identifier_type="authentication token")


async def get_current_user(
    token: str = Depends(get_token_from_cookie_or_header),
) -> User:
    """
    토큰(쿠키 또는 헤더)을 디코딩하여 현재 사용자를 반환합니다.
    """
    if not token:
        raise UserNotExists(identifier="token", identifier_type="authentication token")

    try:
        decoded_token = decode_jwt(token)
        user_id = decoded_token["sub"]
        if not user_id:
            raise UserNotExists(identifier="user", identifier_type="authenticated user")
        user = await user_manager.get(PydanticObjectId(user_id))
        if not user:
            raise UserNotExists(identifier="user", identifier_type="authenticated user")
        return user
    except InvalidToken:
        # 이미 InvalidToken 예외인 경우 그대로 재발생
        raise
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        # 토큰 만료의 경우 구체적인 메시지 제공
        if "expired" in str(e).lower():
            raise InvalidToken(
                token_type="Access Token",
                reason="Token has expired. Please login again.",
            )
        else:
            raise InvalidToken(
                token_type="Access Token", reason="Token validation error"
            )


# --------------------------------------------------------
# 활성 사용자 확인
# --------------------------------------------------------


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    현재 사용자가 활성 사용자인지 확인
    """
    if not current_user.is_active:
        raise UserInactive(user_id=str(current_user.id))
    return current_user


# --------------------------------------------------------
# 이메일 검증된 활성 사용자 확인
# --------------------------------------------------------
def get_current_active_verified_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    현재 사용자가 활성 사용자이고 이메일이 확인된 사용자인지 확인
    """
    if not current_user.is_verified:
        raise AuthorizationFailed(
            "Email verification required", user_id=str(current_user.id)
        )
    return current_user


# --------------------------------------------------------
# 슈퍼유저 권한 검증
# --------------------------------------------------------
def get_current_active_superuser(
    current_user: User = Depends(get_current_active_verified_user),
) -> User:
    """
    현재 사용자가 슈퍼유저인지 검증
    """
    if not current_user.is_superuser:
        raise AuthorizationFailed(
            "Superuser privileges required", user_id=str(current_user.id)
        )
    return current_user
