from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.deps import get_current_user
from app.models import User, UserRole
from app.schemas import GoogleAuthRequest, TokenResponse, UserRead


router = APIRouter(prefix="/auth", tags=["auth"])
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("/google", response_model=TokenResponse)
def google_login(payload: GoogleAuthRequest, db: DbSession) -> TokenResponse:
    try:
        claims: dict[str, Any] = id_token.verify_oauth2_token(
            payload.credential,
            google_requests.Request(),
            settings.google_client_id,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google ID token",
        ) from None

    google_sub = claims.get("sub")
    email = claims.get("email")
    name = claims.get("name")
    if not isinstance(google_sub, str) or not isinstance(email, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google ID token is missing required claims",
        )

    user = db.scalar(select(User).where(User.google_sub == google_sub))
    if user is None:
        # A verified Google email can safely attach to a pre-existing local account.
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(
                email=email,
                name=name if isinstance(name, str) and name else email.split("@", 1)[0],
                google_sub=google_sub,
                role=UserRole.CUSTOMER,
            )
            db.add(user)
        else:
            user.google_sub = google_sub
        db.commit()
        db.refresh(user)

    access_token = create_access_token(user.id, user.role)
    return TokenResponse(access_token=access_token, user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead)
def get_me(current_user: CurrentUser) -> User:
    return current_user


@router.post("/logout")
def logout(_: CurrentUser) -> dict[str, str]:
    return {"detail": "Logged out; discard the access token on the client"}
