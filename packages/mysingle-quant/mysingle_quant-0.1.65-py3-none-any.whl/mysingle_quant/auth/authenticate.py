from typing import Any, Literal, Union

from fastapi import HTTPException
from fastapi.responses import Response
from pydantic import SecretStr

from ..core.config import settings
from ..core.logging_config import get_logger
from .models import User
from .schemas.auth import AccessTokenData, RefreshTokenData
from .security.cookie import delete_cookie, set_auth_cookies
from .security.jwt import decode_jwt, generate_jwt
from .user_manager import UserManager

logger = get_logger(__name__)
SecretType = Union[str, SecretStr]
user_manager = UserManager()


class Authentication:
    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.secret_key: SecretType = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.audience = settings.DEFAULT_AUDIENCE
        self.transport_type = settings.TOKEN_TRANSPORT_TYPE

    def login(
        self,
        user: User,
        response: Response,
    ) -> dict[str, Any] | None:
        if user is None:
            raise HTTPException(status_code=400, detail="Invalid user")
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        if not user.is_verified:
            raise HTTPException(status_code=400, detail="Unverified user")

        access_token_data = AccessTokenData(sub=str(user.id), email=user.email)
        refresh_token_data = RefreshTokenData(sub=str(user.id))
        access_token = generate_jwt(payload=access_token_data.model_dump())
        refresh_token = generate_jwt(payload=refresh_token_data.model_dump())

        # 토큰 전송 방식에 따른 처리
        token_response = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
        if self.transport_type in ["cookie", "hybrid"]:
            # 쿠키에 토큰 설정
            set_auth_cookies(
                response,
                access_token=access_token,
                refresh_token=refresh_token,
            )

        if self.transport_type in ["bearer", "hybrid"]:
            # Bearer 방식에서는 토큰 정보 반환
            return token_response

        # Cookie 전용 방식에서는 None 반환 (토큰은 쿠키에만 설정)
        return None

    def refresh_token(
        self,
        refresh_token: str,
        response: Response,
        transport_type: Literal["cookie", "header"] = "cookie",
    ) -> dict[str, Any] | None:
        """Refresh token을 사용하여 새로운 access token과 refresh token을 생성합니다."""
        try:
            payload = decode_jwt(refresh_token)
        except Exception as e:
            self.logger.error(f"Failed to decode refresh token: {e}")
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        # 새로운 토큰 데이터 생성
        access_token_data = AccessTokenData(sub=user_id, email=payload.get("email", ""))
        refresh_token_data = RefreshTokenData(sub=user_id)

        access_token = generate_jwt(payload=access_token_data.model_dump())
        new_refresh_token = generate_jwt(payload=refresh_token_data.model_dump())

        if transport_type == "cookie":
            set_auth_cookies(
                response,
                access_token=access_token,
                refresh_token=new_refresh_token,
            )

        if transport_type == "header":
            return {
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
            }

        return None

    def validate_token(self, token: str) -> dict[str, Any]:
        """토큰을 검증하고 payload를 반환합니다."""
        try:
            return decode_jwt(token)
        except Exception as e:
            self.logger.error(f"Failed to validate token: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")

    def logout(self, response: Response) -> None:
        """로그아웃 처리 (쿠키 삭제)."""
        delete_cookie(response, key="access_token")
        delete_cookie(response, key="refresh_token")


authenticator = Authentication()
