from fastapi import APIRouter, Body, Request, status
from pydantic import EmailStr

from ..exceptions import (
    UserAlreadyVerified,
    UserInactive,
    UserNotExists,
)
from ..schemas import UserResponse
from ..user_manager import UserManager

user_manager = UserManager()


def get_verify_router() -> APIRouter:
    router = APIRouter()

    @router.post(
        "/request-verify-token",
        status_code=status.HTTP_202_ACCEPTED,
    )
    async def request_verify_token(
        request: Request,
        email: EmailStr = Body(..., embed=True),
    ) -> None:
        try:
            user = await user_manager.get_by_email(email)
            await user_manager.request_verify(user, request)
        except (
            UserNotExists,
            UserInactive,
            UserAlreadyVerified,
        ):
            pass

        return None

    @router.post(
        "/verify",
        response_model=UserResponse,
    )
    async def verify(
        request: Request,
        token: str = Body(..., embed=True),
    ) -> UserResponse:
        # UserManager.verify에서 이미 적절한 예외를 발생시키므로
        # 직접 전파하도록 수정
        user = await user_manager.verify(token, request)
        return UserResponse.model_validate(user, from_attributes=True)

    return router
