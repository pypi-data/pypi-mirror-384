import secrets
import string

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher


class PasswordHelper:
    def __init__(self, password_hash: PasswordHash | None = None) -> None:
        if password_hash is None:
            self.password_hash = PasswordHash(
                (
                    Argon2Hasher(),
                    BcryptHasher(),
                )
            )
        else:
            self.password_hash = password_hash  # pragma: no cover

    def verify_and_update(
        self, plain_password: str, hashed_password: str
    ) -> tuple[bool, str | None]:
        return self.password_hash.verify_and_update(plain_password, hashed_password)

    def hash(self, password: str) -> str:
        return self.password_hash.hash(password)

    def generate(self) -> str:
        return secrets.token_urlsafe()

    def generate_secure_password(self, length: int = 12) -> str:
        characters = string.ascii_letters + string.digits + string.punctuation
        password = "".join(secrets.choice(characters) for _ in range(length))
        return password


password_helper = PasswordHelper()
