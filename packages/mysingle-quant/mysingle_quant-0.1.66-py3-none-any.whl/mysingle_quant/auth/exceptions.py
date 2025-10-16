"""Auth 관련 사용자 정의 예외 클래스들"""

from typing import Any


class AuthException(Exception):
    """Auth 시스템의 기본 예외 클래스"""

    def __init__(
        self,
        message: str = "Authentication error occurred",
        details: Any | None = None,
    ):
        self.message = message
        self.details = details
        super().__init__(self.message)


class InvalidID(AuthException):
    """유효하지 않은 ID 예외"""

    def __init__(self, id_value: Any | None = None):
        message = f"Invalid ID format: {id_value}" if id_value else "Invalid ID format"
        super().__init__(message, {"id": id_value})


class UserAlreadyExists(AuthException):
    """사용자가 이미 존재하는 예외"""

    def __init__(self, email: str | None = None):
        message = (
            f"User with email '{email}' already exists"
            if email
            else "User already exists"
        )
        super().__init__(message, {"email": email})


class UserNotExists(AuthException):
    """사용자가 존재하지 않는 예외"""

    def __init__(self, identifier: str | None = None, identifier_type: str = "user"):
        message = (
            f"{identifier_type.title()} '{identifier}' not found"
            if identifier
            else f"{identifier_type.title()} not found"
        )
        super().__init__(message, {"identifier": identifier, "type": identifier_type})


class UserInactive(AuthException):
    """비활성 사용자 예외"""

    def __init__(self, user_id: Any | None = None):
        message = f"User '{user_id}' is inactive" if user_id else "User is inactive"
        super().__init__(message, {"user_id": user_id})


class UserAlreadyVerified(AuthException):
    """이미 인증된 사용자 예외"""

    def __init__(self, user_id: Any | None = None):
        message = (
            f"User '{user_id}' is already verified"
            if user_id
            else "User is already verified"
        )
        super().__init__(message, {"user_id": user_id})


class InvalidVerifyToken(AuthException):
    """유효하지 않은 인증 토큰 예외"""

    def __init__(self, reason: str | None = None):
        message = (
            f"Invalid verification token: {reason}"
            if reason
            else "Invalid verification token"
        )
        super().__init__(message, {"reason": reason})


class InvalidResetPasswordToken(AuthException):
    """유효하지 않은 비밀번호 재설정 토큰 예외"""

    def __init__(self, reason: str | None = None):
        message = (
            f"Invalid reset password token: {reason}"
            if reason
            else "Invalid reset password token"
        )
        super().__init__(message, {"reason": reason})


class InvalidPasswordException(AuthException):
    """유효하지 않은 비밀번호 예외"""

    def __init__(self, reason: Any | None = None):
        self.reason = reason
        message = f"Invalid password: {reason}" if reason else "Invalid password"
        super().__init__(message, {"reason": reason})


class AuthenticationFailed(AuthException):
    """인증 실패 예외"""

    def __init__(self, reason: str = "Invalid credentials"):
        super().__init__(f"Authentication failed: {reason}", {"reason": reason})


class AuthorizationFailed(AuthException):
    """인가 실패 예외"""

    def __init__(
        self, required_permission: str | None = None, user_id: Any | None = None
    ):
        message = (
            f"Authorization failed. Required: {required_permission}"
            if required_permission
            else "Authorization failed"
        )
        super().__init__(
            message, {"required_permission": required_permission, "user_id": user_id}
        )


class TokenExpired(AuthException):
    """토큰 만료 예외"""

    def __init__(self, token_type: str = "token"):
        message = f"{token_type.title()} has expired"
        super().__init__(message, {"token_type": token_type})


class InvalidToken(AuthException):
    """유효하지 않은 토큰 예외"""

    def __init__(self, token_type: str = "token", reason: str | None = None):
        message = (
            f"Invalid {token_type}: {reason}" if reason else f"Invalid {token_type}"
        )
        super().__init__(message, {"token_type": token_type, "reason": reason})


class JWTStrategyDestroyNotSupportedError(AuthException):
    """JWT 전략에서 토큰 파기가 지원되지 않는 예외"""

    def __init__(self):
        super().__init__("JWT tokens cannot be destroyed")


class OAuth2Error(AuthException):
    """OAuth2 관련 예외"""

    def __init__(
        self, message: str = "OAuth2 error occurred", details: Any | None = None
    ):
        super().__init__(message, details)
