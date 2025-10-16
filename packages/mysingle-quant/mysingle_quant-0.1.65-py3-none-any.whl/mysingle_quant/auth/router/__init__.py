from fastapi import APIRouter

from .auth import create_auth_router
from .oauth2 import get_oauth2_router
from .oauth_management import get_oauth_management_router
from .register import get_register_router
from .reset import get_reset_password_router
from .users import get_users_router
from .verify import get_verify_router

auth_router = APIRouter()
oauth2_router = APIRouter()
user_router = APIRouter()

auth_router.include_router(create_auth_router())
auth_router.include_router(get_register_router())
auth_router.include_router(get_reset_password_router())
auth_router.include_router(get_verify_router())

oauth2_router.include_router(get_oauth2_router(), prefix="/oauth2", tags=["OAuth2"])
oauth2_router.include_router(
    get_oauth_management_router(), prefix="/users", tags=["User"]
)

user_router.include_router(get_users_router())

__all__ = ["auth_router", "user_router", "oauth2_router"]
