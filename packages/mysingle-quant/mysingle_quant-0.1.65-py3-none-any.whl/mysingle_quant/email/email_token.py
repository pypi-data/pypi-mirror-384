# path: app/utils/utiles.py

import logging
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
from jwt.exceptions import InvalidTokenError

from ..core.config import settings

logger = logging.getLogger()


def generate_email_token(email: str) -> str:
    delta = timedelta(hours=settings.EMAIL_TOKEN_EXPIRE_HOURS)
    now = datetime.now(UTC)
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = pyjwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def verify_email_token(token: str) -> str | None:
    try:
        decoded_token = pyjwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return str(decoded_token["sub"])
    except InvalidTokenError:
        return None
