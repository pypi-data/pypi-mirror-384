from fastapi import APIRouter, Body, Request, status
from pydantic import EmailStr

from ..exceptions import (
    UserInactive,
    UserNotExists,
)
from ..user_manager import UserManager

user_manager = UserManager()


def get_reset_password_router() -> APIRouter:
    """Generate a router with the reset password routes."""
    router = APIRouter()

    @router.post(
        "/forgot-password",
        status_code=status.HTTP_202_ACCEPTED,
    )
    async def forgot_password(
        request: Request,
        email: EmailStr = Body(..., embed=True),
    ) -> None:
        try:
            user = await user_manager.get_by_email(email)
        except UserNotExists:
            return None

        try:
            await user_manager.forgot_password(user, request)
        except UserInactive:
            pass

        return None

    @router.post(
        "/reset-password",
    )
    async def reset_password(
        request: Request,
        token: str = Body(...),
        password: str = Body(...),
    ) -> None:
        # UserManager.reset_password에서 이미 적절한 예외를 발생시키므로
        # 직접 전파하도록 수정
        await user_manager.reset_password(token, password, request)

    return router
