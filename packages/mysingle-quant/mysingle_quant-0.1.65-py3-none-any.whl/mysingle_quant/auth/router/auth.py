"""Health check utilities and endpoints."""

from typing import Annotated

from beanie import PydanticObjectId
from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    Header,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm

from ...core.config import settings
from ...core.logging_config import get_logger
from ..authenticate import authenticator
from ..deps import get_current_active_verified_user
from ..exceptions import AuthenticationFailed
from ..models import User
from ..schemas.auth import LoginResponse
from ..schemas.user import UserResponse
from ..user_manager import UserManager

logger = get_logger(__name__)
access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
user_manager = UserManager()
authenticator = authenticator


def create_auth_router() -> APIRouter:
    router = APIRouter()

    @router.post(
        "/login",
        response_model=LoginResponse,
        status_code=status.HTTP_200_OK,  # 202 -> 200 변경
    )
    async def login(
        request: Request,
        response: Response,  # Response 객체를 직접 받도록 수정
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    ) -> LoginResponse:
        user = await user_manager.authenticate(
            username=form_data.username, password=form_data.password
        )

        if not user:
            raise AuthenticationFailed("Invalid credentials")

        # authenticator.login을 호출하여 토큰 생성
        token_data = authenticator.login(user=user, response=response)

        # LoginResponse 생성 시 토큰 전송 방식에 따라 분기
        user_response = UserResponse.model_validate(user)

        if settings.TOKEN_TRANSPORT_TYPE in ["bearer", "hybrid"]:
            # Bearer 또는 Hybrid 방식: 응답에 토큰 포함
            return LoginResponse(
                access_token=token_data["access_token"] if token_data else "",
                refresh_token=token_data["refresh_token"] if token_data else "",
                token_type="bearer",
                user_info=user_response,
            )
        else:
            # Cookie 방식: 토큰은 쿠키에만 설정, 응답에는 사용자 정보만
            return LoginResponse(
                user_info=user_response,
            )

    @router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
    async def logout(
        request: Request,
        response: Response,
        current_user: User = Depends(get_current_active_verified_user),
    ) -> None:
        """
        로그아웃 엔드포인트.

        쿠키에서 토큰을 삭제하고 로그아웃 처리를 합니다.
        """
        # authenticator를 사용하여 쿠키 삭제
        authenticator.logout(response)

        # 로그아웃 후 처리 로직 실행
        await user_manager.on_after_logout(current_user, request)
        # HTTP 204는 응답 본문이 없어야 하므로 None 반환
        return None

    @router.post("/refresh", response_model=LoginResponse)
    async def refresh_token(
        request: Request,
        response: Response,  # Response 객체 추가
        refresh_token_header: str | None = Header(None, alias="X-Refresh-Token"),
        refresh_token_cookie: str | None = Cookie(None, alias="refresh_token"),
    ) -> LoginResponse:
        """JWT 토큰 갱신 엔드포인트"""

        # 토큰 전송 방식에 따라 refresh token 소스 결정
        if settings.TOKEN_TRANSPORT_TYPE == "bearer":
            refresh_token = refresh_token_header
        elif settings.TOKEN_TRANSPORT_TYPE == "cookie":
            refresh_token = refresh_token_cookie
        else:  # hybrid
            refresh_token = refresh_token_header or refresh_token_cookie

        if not refresh_token:
            raise AuthenticationFailed("Refresh token not provided")

        try:
            # 토큰 전송 방식에 맞게 새 토큰 생성
            transport_type = (
                "header"
                if settings.TOKEN_TRANSPORT_TYPE in ["bearer", "hybrid"]
                else "cookie"
            )
            token_data = authenticator.refresh_token(
                refresh_token=refresh_token,
                response=response,
                transport_type=transport_type,
            )
        except HTTPException:
            raise AuthenticationFailed("Invalid refresh token")

        # 사용자 정보 조회
        try:
            payload = authenticator.validate_token(refresh_token)
            user_id = payload.get("sub")
            user = await user_manager.get(PydanticObjectId(user_id))
            if not user:
                raise AuthenticationFailed("User not found")
        except Exception:
            raise AuthenticationFailed("Failed to retrieve user information")

        user_response = UserResponse.model_validate(user)

        # 토큰 전송 방식에 따른 응답 생성
        if settings.TOKEN_TRANSPORT_TYPE in ["bearer", "hybrid"] and token_data:
            return LoginResponse(
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                token_type=token_data["token_type"],
                user_info=user_response,
            )
        else:
            # Cookie 방식
            return LoginResponse(
                user_info=user_response,
            )

    @router.get("/token/verify")
    async def verify_token(
        current_user: User = Depends(get_current_active_verified_user),
    ) -> dict:
        """토큰 검증 및 사용자 정보 반환 (디버깅용)"""
        return {
            "valid": True,
            "user_id": str(current_user.id),
            "email": current_user.email,
            "is_active": current_user.is_active,
            "is_verified": current_user.is_verified,
            "is_superuser": current_user.is_superuser,
        }

    return router
