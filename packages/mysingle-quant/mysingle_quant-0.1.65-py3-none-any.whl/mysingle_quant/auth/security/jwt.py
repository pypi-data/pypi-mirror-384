from typing import Any, Union

import jwt
from pydantic import SecretStr

from ...core.config import settings


def generate_jwt(
    payload: dict,
    key: Union[str, SecretStr] | None = settings.SECRET_KEY,
) -> str:
    payload = payload.copy()

    return jwt.encode(
        payload,
        key=key.get_secret_value() if isinstance(key, SecretStr) else key,
        algorithm=settings.ALGORITHM,
    )


def decode_jwt(
    token: str,
    key: Union[str, SecretStr] | None = settings.SECRET_KEY,
    audience: str | list[str] = settings.DEFAULT_AUDIENCE,
) -> dict[str, Any]:
    return jwt.decode(
        token,
        key=key.get_secret_value() if isinstance(key, SecretStr) else key,
        audience=audience,
        algorithms=[settings.ALGORITHM],
    )
