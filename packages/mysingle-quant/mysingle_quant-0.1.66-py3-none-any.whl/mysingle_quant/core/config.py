"""Common configuration settings for all microservices."""

from typing import Literal, Self

from pydantic import EmailStr, Field, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class CommonSettings(BaseSettings):
    """Common settings for all microservices."""

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Project Settings
    PROJECT_NAME: str = Field(default="Quant Platform", description="Project name")
    ENVIRONMENT: str = Field(
        default="development",
        description="Environment (development, staging, production)",
    )
    DEBUG: bool = Field(default=True, description="Debug mode")
    DEV_MODE: bool = Field(default=True, description="Development mode")
    MOCK_DATABASE: bool = Field(default=False, description="Use mock database")

    FRONTEND_URL: str = Field(
        default="http://localhost:3000", description="Frontend application URL"
    )  # TODO: Need to deprecated after refactoring
    BACKEND_URL: str = Field(
        default="http://localhost:8000", description="Backend application URL"
    )  # TODO: Need to deprecated after refactoring

    # Default Superuser Settings
    SUPERUSER_EMAIL: EmailStr = Field(
        default="your_email@example.com", description="Superuser email"
    )
    SUPERUSER_PASSWORD: str = Field(
        default="change-this-admin-password", description="Superuser password"
    )
    SUPERUSER_FULLNAME: str = Field(
        default="Admin User", description="Superuser full name"
    )

    # Application Settings
    AUTH_ENABLED: bool = Field(default=True, description="Enable authentication system")
    AUTH_API_VERSION: str = Field(default="v1", description="IAM API version")

    # Database Settings
    MONGODB_SERVER: str = Field(default="localhost:27019", description="MongoDB host")
    MONGODB_USERNAME: str = Field(default="root", description="MongoDB username")
    MONGODB_PASSWORD: str = Field(default="example", description="MongoDB password")

    # Token and Security Settings
    SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production", description="Secret key for JWT"
    )
    TOKEN_TRANSPORT_TYPE: Literal["bearer", "cookie", "hybrid"] = Field(
        default="hybrid", description="Token transport type (bearer, cookie, or hybrid)"
    )
    HTTPONLY_COOKIES: bool = Field(default=False, description="Use HTTPOnly cookies")
    SAMESITE_COOKIES: Literal["lax", "strict", "none"] = Field(
        default="lax", description="SameSite attribute for cookies (lax, strict, none)"
    )
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    DEFAULT_AUDIENCE: str = Field(
        default="your-audience", description="Default audience for JWT"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=480, description="Access token expiration in minutes (8 hours)"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7, description="Refresh token expiration in days"
    )
    RESET_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60, description="Reset password token expiration in minutes"
    )
    VERIFY_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60, description="Verify user token expiration in minutes"
    )
    EMAIL_TOKEN_EXPIRE_HOURS: int = Field(
        default=48, description="Token for Email Verification expiration in hours"
    )

    # API Settings
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="CORS origins",
    )

    # Performance Settings
    MAX_CONNECTIONS_COUNT: int = Field(
        default=10, description="Max database connections"
    )
    MIN_CONNECTIONS_COUNT: int = Field(
        default=1, description="Min database connections"
    )

    @property
    def all_cors_origins(self) -> list[str]:
        """Get all CORS origins including environment-specific ones."""
        origins = self.CORS_ORIGINS.copy()

        # Add localhost variants for development
        if self.ENVIRONMENT in ["development", "local"]:
            dev_origins = [
                "http://localhost:3000",
                "http://localhost:8000",
                "http://localhost:8080",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8000",
                "http://127.0.0.1:8080",
            ]
            for origin in dev_origins:
                if origin not in origins:
                    origins.append(origin)

        return origins

    # 메일링 설정 (Mailtrap)
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str = "your_smtp_host"
    SMTP_USER: str = "your_smtp_user"
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: str = "your_email@example.com"
    EMAILS_FROM_NAME: str = "Admin Name"

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    @computed_field
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST == "your_smtp_host")

    # External API Keys

    # OAuth2 Client IDs and Secrets
    GOOGLE_CLIENT_ID: str = Field(
        default="your-google-client-id", description="Google client ID"
    )
    GOOGLE_CLIENT_SECRET: str = Field(
        default="your-google-client-secret", description="Google client secret"
    )
    GOOGLE_OAUTH_SCOPES: list[str] = Field(
        default=["openid", "email", "profile"], description="Google OAuth scopes"
    )
    OKTA_CLIENT_ID: str = Field(
        default="your-okta-client-id", description="Okta client ID"
    )
    OKTA_CLIENT_SECRET: str = Field(
        default="your-okta-client-secret", description="Okta client secret"
    )
    OKTA_DOMAIN: str = Field(default="your-okta-domain", description="Okta domain")
    KAKAO_CLIENT_ID: str = Field(
        default="your-kakao-client-id", description="Kakao client ID"
    )
    KAKAO_CLIENT_SECRET: str = Field(
        default="your-kakao-client-secret", description="Kakao client secret"
    )
    KAKAO_OAUTH_SCOPES: list[str] = Field(
        default=["profile", "account_email"], description="Kakao OAuth scopes"
    )
    NAVER_CLIENT_ID: str = Field(
        default="your-naver-client-id", description="Naver client ID"
    )
    NAVER_CLIENT_SECRET: str = Field(
        default="your-naver-client-secret", description="Naver client secret"
    )
    NAVER_OAUTH_SCOPES: list[str] = Field(
        default=["profile", "email"], description="Naver OAuth scopes"
    )

    # Market Data API Keys
    ALPHA_VANTAGE_API_KEY: str = Field(
        default="demo", description="Alpha Vantage API Key"
    )


# Global settings instance
settings = CommonSettings()


def get_settings() -> CommonSettings:
    """Get the global settings instance."""
    return settings
