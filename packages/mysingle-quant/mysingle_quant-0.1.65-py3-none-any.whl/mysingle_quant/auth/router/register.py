from fastapi import APIRouter, Request, status

from ..schemas import UserCreate, UserResponse
from ..user_manager import UserManager

user_manager = UserManager()


def get_register_router() -> APIRouter:
    """Generate a router with the register route."""
    router = APIRouter()

    @router.post(
        "/register",
        response_model=UserResponse,
        status_code=status.HTTP_201_CREATED,
    )
    async def register(
        request: Request,
        obj_in: UserCreate,
    ) -> UserResponse:
        # UserManager.create에서 이미 적절한 예외를 발생시키므로
        # 직접 전파하도록 수정
        created_user = await user_manager.create(obj_in, request=request)
        return UserResponse.model_validate(created_user, from_attributes=True)

    return router
