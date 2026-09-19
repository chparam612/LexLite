import uuid
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import TokenData
from app.core.logging import logger


class AuthService:
    @staticmethod
    def get_or_create_user(db: Session, token_data: TokenData) -> User:
        """
        Derive or persist the tenant user record from verified token claims.
        Ensures existing users are reused without duplication.
        """
        user = db.query(User).filter_by(firebase_uid=token_data.uid).first()
        if user:
            # Update display name or email if changed
            if token_data.display_name and user.display_name != token_data.display_name:
                user.display_name = token_data.display_name
                db.commit()
                db.refresh(user)
            return user

        # Check by email as fallback
        user = db.query(User).filter_by(email=token_data.email).first()
        if user:
            user.firebase_uid = token_data.uid
            if token_data.display_name:
                user.display_name = token_data.display_name
            db.commit()
            db.refresh(user)
            return user

        # Create new user
        new_user = User(
            id=str(uuid.uuid4()),
            firebase_uid=token_data.uid,
            email=token_data.email,
            display_name=token_data.display_name or token_data.email.split("@")[0]
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"Created new user record: {new_user.id} ({new_user.email})")
        return new_user
