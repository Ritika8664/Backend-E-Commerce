import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.config import settings
from app.models.enums import UserRole


ACCESS_TOKEN_TTL = timedelta(hours=24)


def create_access_token(user_id: uuid.UUID, role: UserRole) -> str:
    expires_at = datetime.now(timezone.utc) + ACCESS_TOKEN_TTL
    return jwt.encode(
        {
            "sub": str(user_id),
            "user_id": str(user_id),
            "role": role.value,
            "exp": expires_at,
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
