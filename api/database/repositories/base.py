"""
Base Repository - Abstract data access pattern
All repositories inherit from this base class
"""

from typing import TypeVar, Generic, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations"""
    
    def __init__(self, session: Session, model_class: type):
        self.session = session
        self.model_class = model_class
    
    def create(self, obj_in: dict) -> T:
        """Create a new record"""
        db_obj = self.model_class(**obj_in)
        self.session.add(db_obj)
        self.session.commit()
        self.session.refresh(db_obj)
        return db_obj
    
    def get_by_id(self, obj_id: Any) -> Optional[T]:
        """Get record by ID"""
        return self.session.query(self.model_class).filter(
            self.model_class.id == obj_id
        ).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all records with pagination"""
        return self.session.query(self.model_class).offset(skip).limit(limit).all()
    
    def update(self, obj_id: Any, obj_in: dict) -> Optional[T]:
        """Update a record"""
        db_obj = self.get_by_id(obj_id)
        if db_obj:
            for key, value in obj_in.items():
                if hasattr(db_obj, key):
                    setattr(db_obj, key, value)
            self.session.commit()
            self.session.refresh(db_obj)
        return db_obj
    
    def delete(self, obj_id: Any) -> bool:
        """Delete a record"""
        db_obj = self.get_by_id(obj_id)
        if db_obj:
            self.session.delete(db_obj)
            self.session.commit()
            return True
        return False
    
    def count(self) -> int:
        """Count total records"""
        return self.session.query(self.model_class).count()
