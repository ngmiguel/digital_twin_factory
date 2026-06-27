"""Password hashing and verification."""

import bcrypt

from src.domain.shared.exceptions import ValidationError

_BCRYPT_ROUNDS = 12


class PasswordService:
    """Hash and verify passwords using bcrypt."""

    @staticmethod
    def validate_strength(password: str) -> None:
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters", field="password")
        if not any(c.isupper() for c in password):
            raise ValidationError("Password must contain an uppercase letter", field="password")
        if not any(c.islower() for c in password):
            raise ValidationError("Password must contain a lowercase letter", field="password")
        if not any(c.isdigit() for c in password):
            raise ValidationError("Password must contain a digit", field="password")

    @staticmethod
    def hash(password: str) -> str:
        PasswordService.validate_strength(password)
        salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
        return bcrypt.hashpw(password.encode(), salt).decode()

    @staticmethod
    def verify(password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
