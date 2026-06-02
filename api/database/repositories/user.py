"""
User Repository - Specialized data access for users
"""

from typing import Optional
from sqlalchemy.orm import Session
from api.database.models import User
from api.database.repositories.base import BaseRepository
from api.core.security import get_password_hash, verify_password


class UserRepository(BaseRepository[User]):
    """Repository for user data access"""
    
    def __init__(self, session: Session):
        super().__init__(session, User)
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.session.query(User).filter(User.id == user_id).first()
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.session.query(User).filter(User.username == username).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.session.query(User).filter(User.email == email).first()
    
    def get_active_users(self, skip: int = 0, limit: int = 100):
        """Get all active users"""
        return self.session.query(User).filter(
            User.is_active == True
        ).offset(skip).limit(limit).all()
    
    def create_user(self, user_data: dict) -> User:
        """Create new user with hashed password"""
        user_data_copy = user_data.copy()
        
        # Hash password
        if "password" in user_data_copy:
            plain_password = user_data_copy.pop("password")
            user_data_copy["hashed_password"] = get_password_hash(plain_password)
        
        return self.create(user_data_copy)
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        user = self.get_by_username(username)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    def update_password(self, user_id: str, new_password: str) -> Optional[User]:
        """Update user password"""
        hashed_password = get_password_hash(new_password)
        return self.update(user_id, {"hashed_password": hashed_password})
    
    def deactivate_user(self, user_id: str) -> Optional[User]:
        """Deactivate a user"""
        return self.update(user_id, {"is_active": False})
    
    def activate_user(self, user_id: str) -> Optional[User]:
        """Activate a user"""
        return self.update(user_id, {"is_active": True})
    
    def update_last_login(self, user_id: str) -> Optional[User]:
        """Update user's last login timestamp"""
        from datetime import datetime
        return self.update(user_id, {"last_login": datetime.utcnow()})
