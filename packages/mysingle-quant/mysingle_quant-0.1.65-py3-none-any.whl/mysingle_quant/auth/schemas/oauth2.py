# path: app/schemas/oauth2.py

from pydantic import BaseModel


# -------------------
# 공통 토큰 스키마 (필요한 필드만 선언)
# -------------------
class BaseOAuthToken(BaseModel):
    access_token: str
    token_type: str | None = None
    refresh_token: str | None = None
    expires_in: int | None = None
    expires_at: int | None = None
    scope: str | None = None
    id_token: str | None = None
    refresh_token_expires_in: int | None = None


# -------------------
# 구글
# -------------------
class GoogleToken(BaseOAuthToken):
    # 기존에 없는 필드 id_token 등 이미 BaseOAuthToken에 들어있으면 중복 필요 X
    pass


class GoogleProfile(BaseModel):
    id: str
    email: str
    verified_email: bool
    name: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    picture: str | None = None
    hd: str | None = None


# -------------------
# 카카오
# -------------------
class KakaoToken(BaseOAuthToken):
    # e.g. Kakao 전용 필드가 있으면 여기에
    pass


class KakaoProfile(BaseModel):
    id: int
    connected_at: str

    # 실제로는 kakao_account 구조
    # 여기서는 간단히 예시
    class KakaoAccount(BaseModel):
        email: str

        class Profile(BaseModel):
            nickname: str
            profile_image_url: str | None

        profile: Profile

    kakao_account: KakaoAccount


# -------------------
# 네이버
# -------------------
class NaverToken(BaseOAuthToken):
    pass


class NaverProfile(BaseModel):
    id: str
    nickname: str
    profile_image: str
    email: str
    name: str
