"""Database connection and session management for the job search pipeline."""

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .models import Base

class DatabaseManager:
    """Manages database connections and session creation."""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Default to data/jobs/jobs.db relative to project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            db_path = os.path.join(project_root, 'data', 'jobs', 'jobs.db')
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Create SQLite engine with connection pooling for concurrent access
        self.engine = create_engine(
            f'sqlite:///{db_path}',
            poolclass=StaticPool,
            connect_args={
                'check_same_thread': False,
                'timeout': 20
            },
            echo=False  # Set to True for SQL debugging
        )
        
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self) -> None:
        """Create all tables defined in models."""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a new database session.
        
        Returns:
            Session: A new SQLAlchemy session instance.
        """
        return self.SessionLocal()
    
    def get_engine(self):
        """Get the database engine.
        
        Returns:
            Engine: The SQLAlchemy database engine.
        """
        return self.engine

# Global database manager instance
db_manager = DatabaseManager()

def get_db_session() -> Generator[Session, None, None]:
    """Dependency to get database session.
    
    Yields:
        Session: A database session that will be automatically closed.
    """
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()

def get_engine():
    """Get database engine.
    
    Returns:
        Engine: The SQLAlchemy database engine.
    """
    return db_manager.get_engine()