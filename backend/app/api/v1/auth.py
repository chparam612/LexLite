from pydantic import BaseModel
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.user import (
    UserResponse,
    UserRegisterRequest,
    UserLoginRequest,
    AuthTokenResponse
)
from app.services.auth_service import AuthService
from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


class TokenVerifyResponse(BaseModel):
    status: str
    user: UserResponse


@router.post("/register", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
def register_account(req: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new tenant user account with email, password, and optional display name.
    Returns a signed JWT bearer token and user profile.
    """
    user = AuthService.register_user(db, req)
    token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "name": user.display_name
    })
    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=AuthTokenResponse, status_code=status.HTTP_200_OK)
def login_account(req: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate tenant user with email and salted password.
    Returns a signed JWT bearer token and user profile.
    """
    user = AuthService.authenticate_user(db, req.email, req.password)
    token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "name": user.display_name
    })
    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/demo-login", response_model=AuthTokenResponse, status_code=status.HTTP_200_OK)
def demo_attorney_login(db: Session = Depends(get_db)):
    """
    1-click instant login as Demo Attorney (Sarah Jenkins, Esq.) for judging and evaluation.
    """
    user = AuthService.get_or_create_demo_attorney(db)
    token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "name": user.display_name
    })
    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Retrieve currently authenticated user profile.
    """
    return current_user


@router.post("/verify", response_model=TokenVerifyResponse, status_code=status.HTTP_200_OK)
def verify_token(current_user: User = Depends(get_current_user)):
    """
    Verify bearer token validity and return authenticated user session.
    """
    return TokenVerifyResponse(
        status="valid",
        user=UserResponse.model_validate(current_user)
    )
