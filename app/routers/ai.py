import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.ai import run_support_agent
from app.ai.rate_limit import consume_request
from app.deps import get_current_user
from app.models import User
from app.schemas import ChatRequest, ChatResponse


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["ai"])
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, current_user: CurrentUser) -> ChatResponse:
    message = payload.message.strip()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty",
        )

    retry_after = consume_request(str(current_user.id))
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many support requests. Please try again shortly.",
            headers={"Retry-After": str(retry_after)},
        )

    try:
        response = run_support_agent(message, str(current_user.id))
    except Exception:
        logger.exception("AI support request failed for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI support is temporarily unavailable",
        ) from None
    return ChatResponse(response=response)


# This limiter is intentionally process-local. Multi-instance deployments should
# replace it with a shared Redis-backed limiter at the gateway or application layer.
