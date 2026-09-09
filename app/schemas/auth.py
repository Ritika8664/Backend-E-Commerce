from pydantic import BaseModel, Field

from app.schemas.user import UserRead


class GoogleAuthRequest(BaseModel):
    credential: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
