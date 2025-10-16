from httpx_oauth.clients.google import GoogleOAuth2
from httpx_oauth.clients.kakao import KakaoOAuth2
from httpx_oauth.clients.naver import NaverOAuth2
from httpx_oauth.integrations.fastapi import OAuth2AuthorizeCallback
from httpx_oauth.oauth2 import BaseOAuth2

from ...core.config import settings


def get_oauth2_client(provider_name: str) -> BaseOAuth2:
    """주어진 공급자 이름에 해당하는 OAuth2 클라이언트를 반환합니다."""

    if provider_name == "google":
        return GoogleOAuth2(
            settings.GOOGLE_CLIENT_ID,
            settings.GOOGLE_CLIENT_SECRET,
            scopes=settings.GOOGLE_OAUTH_SCOPES,
        )
    elif provider_name == "kakao":
        return KakaoOAuth2(
            client_id=settings.KAKAO_CLIENT_ID,
            client_secret=settings.KAKAO_CLIENT_SECRET,
            scopes=settings.KAKAO_OAUTH_SCOPES,
        )
    elif provider_name == "naver":
        return NaverOAuth2(
            client_id=settings.NAVER_CLIENT_ID,
            client_secret=settings.NAVER_CLIENT_SECRET,
            scopes=settings.NAVER_OAUTH_SCOPES,
        )
    else:
        raise ValueError(f"Unsupported OAuth2 provider: {provider_name}")


def get_oauth2_authorize_callback(
    provider_name: str, redirect_url: str | None = None
) -> OAuth2AuthorizeCallback:
    """주어진 공급자 이름에 해당하는 OAuth2AuthorizeCallback을 반환합니다."""
    oauth_client = get_oauth2_client(provider_name=provider_name)
    return OAuth2AuthorizeCallback(oauth_client, redirect_url=redirect_url)
