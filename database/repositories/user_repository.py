"""
User repository - User database operations
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional
import uuid

from database.models import User, UserRole
from api.core.security import get_password_hash, verify_password


class UserRepository:
    """Repository for user operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        role: UserRole = UserRole.READONLY
    ) -> User:
        """Create a new user"""
        user = User(
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            full_name=full_name,
            role=role,
            is_active=True
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        user = self.get_user_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
    
    def list_users(self, skip: int = 0, limit: int = 20) -> list:
        """List users with pagination"""
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def update_user(self, user_id: uuid.UUID, **kwargs) -> Optional[User]:
        """Update user"""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def delete_user(self, user_id: uuid.UUID) -> bool:
        """Delete user"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        self.db.delete(user)
        self.db.commit()
        return True
