import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import TokenData, UserRegisterRequest
from app.core.security import hash_password, verify_password
from app.core.logging import logger


class AuthService:
    @staticmethod
    def register_user(db: Session, req: UserRegisterRequest) -> User:
        """Register a new tenant user with salted password hash."""
        clean_email = req.email.strip().lower()

        if len(req.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long."
            )

        existing = db.query(User).filter(User.email.ilike(clean_email)).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email address already exists."
            )

        new_user = User(
            id=str(uuid.uuid4()),
            firebase_uid=f"native_{uuid.uuid4().hex[:12]}",
            email=clean_email,
            display_name=req.display_name.strip() if req.display_name else clean_email.split("@")[0],
            hashed_password=hash_password(req.password)
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"Registered new native user: {new_user.id} ({new_user.email})")
        return new_user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User:
        """Authenticate user by verifying email and salted password."""
        clean_email = email.strip().lower()
        user = db.query(User).filter(User.email.ilike(clean_email)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password."
            )

        if not user.hashed_password or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password."
            )

        return user

    @staticmethod
    def get_or_create_demo_attorney(db: Session) -> User:
        """Retrieve or create the standard Demo Attorney profile for 1-click evaluation access."""
        demo_email = "attorney@legalai.example.com"
        user = db.query(User).filter_by(email=demo_email).first()
        if user:
            return user

        user = User(
            id="demo_attorney_01",
            firebase_uid="demo_attorney_uid",
            email=demo_email,
            display_name="Sarah Jenkins, Esq.",
            hashed_password=hash_password("password123")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_or_create_user(db: Session, token_data: TokenData) -> User:
        """
        Derive or persist the tenant user record from verified token claims.
        Ensures existing users are reused without duplication.
        """
        # 1. Look up by user id directly (sub in JWT)
        if token_data.uid:
            user = db.query(User).filter_by(id=token_data.uid).first()
            if user:
                return user

            # Look up by firebase_uid
            user = db.query(User).filter_by(firebase_uid=token_data.uid).first()
            if user:
                return user

        # 2. Check by email as fallback
        user = db.query(User).filter_by(email=token_data.email).first()
        if user:
            if not user.firebase_uid:
                user.firebase_uid = token_data.uid
            if token_data.display_name and not user.display_name:
                user.display_name = token_data.display_name
            db.commit()
            db.refresh(user)
            return user

        # 3. Create new user
        new_user = User(
            id=token_data.uid or str(uuid.uuid4()),
            firebase_uid=token_data.uid,
            email=token_data.email,
            display_name=token_data.display_name or token_data.email.split("@")[0]
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"Created new user record: {new_user.id} ({new_user.email})")
        return new_user
