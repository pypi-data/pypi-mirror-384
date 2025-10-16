"""Auth 시스템의 예외 핸들러"""

from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse

from .exceptions import (
    AuthenticationFailed,
    AuthException,
    AuthorizationFailed,
    InvalidID,
    InvalidPasswordException,
    InvalidResetPasswordToken,
    InvalidVerifyToken,
    JWTStrategyDestroyNotSupportedError,
    TokenExpired,
    UserAlreadyExists,
    UserAlreadyVerified,
    UserInactive,
    UserNotExists,
)


def create_error_response(
    status_code: int, error_code: str, message: str, details: Any = None
) -> JSONResponse:
    """표준화된 에러 응답 생성"""
    content = {
        "error": {
            "code": error_code,
            "message": message,
        }
    }

    if details:
        content["error"]["details"] = details

    return JSONResponse(status_code=status_code, content=content)


async def auth_exception_handler(request: Request, exc: AuthException) -> JSONResponse:
    """Auth 기본 예외 핸들러"""
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="AUTH_ERROR",
        message=exc.message,
        details=exc.details,
    )


async def invalid_id_handler(request: Request, exc: InvalidID) -> JSONResponse:
    """잘못된 ID 예외 핸들러"""
    return create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_code="INVALID_ID",
        message=exc.message,
        details=exc.details,
    )


async def user_already_exists_handler(
    request: Request, exc: UserAlreadyExists
) -> JSONResponse:
    """사용자 이미 존재 예외 핸들러"""
    return create_error_response(
        status_code=status.HTTP_409_CONFLICT,
        error_code="USER_ALREADY_EXISTS",
        message=exc.message,
        details=exc.details,
    )


async def user_not_exists_handler(request: Request, exc: UserNotExists) -> JSONResponse:
    """사용자 존재하지 않음 예외 핸들러"""
    return create_error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="USER_NOT_FOUND",
        message=exc.message,
        details=exc.details,
    )


async def user_inactive_handler(request: Request, exc: UserInactive) -> JSONResponse:
    """비활성 사용자 예외 핸들러"""
    return create_error_response(
        status_code=status.HTTP_403_FORBIDDEN,
        error_code="USER_INACTIVE",
        message=exc.message,
        details=exc.details,
    )


async def user_already_verified_handler(
    request: Request, exc: UserAlreadyVerified
) -> JSONResponse:
    """이미 인증된 사용자 예외 핸들러"""
    return create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_code="USER_ALREADY_VERIFIED",
        message=exc.message,
        details=exc.details,
    )


async def invalid_verify_token_handler(
    request: Request, exc: InvalidVerifyToken
) -> JSONResponse:
    """잘못된 인증 토큰 예외 핸들러"""
    return create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_code="INVALID_VERIFY_TOKEN",
        message=exc.message,
        details=exc.details,
    )


async def invalid_reset_password_token_handler(
    request: Request, exc: InvalidResetPasswordToken
) -> JSONResponse:
    """잘못된 비밀번호 재설정 토큰 예외 핸들러"""
    return create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_code="INVALID_RESET_TOKEN",
        message=exc.message,
        details=exc.details,
    )


async def invalid_password_handler(
    request: Request, exc: InvalidPasswordException
) -> JSONResponse:
    """잘못된 비밀번호 예외 핸들러"""
    return create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_code="INVALID_PASSWORD",
        message=exc.message,
        details=exc.details,
    )


async def authentication_failed_handler(
    request: Request, exc: AuthenticationFailed
) -> JSONResponse:
    """인증 실패 예외 핸들러"""
    return create_error_response(
        status_code=status.HTTP_401_UNAUTHORIZED,
        error_code="AUTHENTICATION_FAILED",
        message=exc.message,
        details=exc.details,
    )


async def authorization_failed_handler(
    request: Request, exc: AuthorizationFailed
) -> JSONResponse:
    """인가 실패 예외 핸들러"""
    return create_error_response(
        status_code=status.HTTP_403_FORBIDDEN,
        error_code="AUTHORIZATION_FAILED",
        message=exc.message,
        details=exc.details,
    )


async def token_expired_handler(request: Request, exc: TokenExpired) -> JSONResponse:
    """토큰 만료 예외 핸들러"""
    return create_error_response(
        status_code=status.HTTP_401_UNAUTHORIZED,
        error_code="TOKEN_EXPIRED",
        message=exc.message,
        details=exc.details,
    )


async def jwt_destroy_not_supported_handler(
    request: Request, exc: JWTStrategyDestroyNotSupportedError
) -> JSONResponse:
    """JWT 토큰 파기 미지원 예외 핸들러"""
    return create_error_response(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        error_code="JWT_DESTROY_NOT_SUPPORTED",
        message=exc.message,
        details=exc.details,
    )


# 예외 핸들러 매핑
EXCEPTION_HANDLERS: dict[type, Any] = {
    InvalidID: invalid_id_handler,
    UserAlreadyExists: user_already_exists_handler,
    UserNotExists: user_not_exists_handler,
    UserInactive: user_inactive_handler,
    UserAlreadyVerified: user_already_verified_handler,
    InvalidVerifyToken: invalid_verify_token_handler,
    InvalidResetPasswordToken: invalid_reset_password_token_handler,
    InvalidPasswordException: invalid_password_handler,
    AuthenticationFailed: authentication_failed_handler,
    AuthorizationFailed: authorization_failed_handler,
    TokenExpired: token_expired_handler,
    JWTStrategyDestroyNotSupportedError: jwt_destroy_not_supported_handler,
    AuthException: auth_exception_handler,  # 기본 핸들러는 마지막에
}


def register_auth_exception_handlers(app: Any) -> None:
    """FastAPI 앱에 Auth 예외 핸들러들을 등록"""
    for exception_type, handler in EXCEPTION_HANDLERS.items():
        app.add_exception_handler(exception_type, handler)
