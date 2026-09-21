from pydantic import BaseModel
from fastapi import APIRouter, Depends, status
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


class TokenVerifyResponse(BaseModel):
    status: str
    user: UserResponse


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Retrieve currently authenticated user profile derived from the verified Firebase token.
    """
    return current_user


@router.post("/verify", response_model=TokenVerifyResponse, status_code=status.HTTP_200_OK)
def verify_token(current_user: User = Depends(get_current_user)):
    """
    Verify bearer token validity and return authenticated user session (Phase 9).
    """
    return TokenVerifyResponse(
        status="valid",
        user=UserResponse.model_validate(current_user)
    )
