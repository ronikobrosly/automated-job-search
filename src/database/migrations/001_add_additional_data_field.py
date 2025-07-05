"""
Migration 001: Add additional_data JSON field to jobs table

This migration adds a JSON field to store site-specific job details
like benefits, work_type, detailed requirements, etc.
"""

import logging

from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

def upgrade(engine: Engine) -> None:
    """Add additional_data JSON field to jobs table.
    
    Args:
        engine: SQLAlchemy database engine.
    """
    try:
        with engine.connect() as conn:
            # Add the additional_data column as JSON
            conn.execute(text("""
                ALTER TABLE jobs 
                ADD COLUMN additional_data JSON
            """))
            conn.commit()
            logger.info("Successfully added additional_data JSON field to jobs table")
    except Exception as e:
        logger.error(f"Failed to add additional_data field: {e}")
        raise

def downgrade(engine: Engine) -> None:
    """Remove additional_data JSON field from jobs table.
    
    Args:
        engine: SQLAlchemy database engine.
    """
    try:
        with engine.connect() as conn:
            # Remove the additional_data column
            conn.execute(text("""
                ALTER TABLE jobs
                DROP COLUMN additional_data
            """))
            conn.commit()
            logger.info("Successfully removed additional_data field from jobs table")
    except Exception as e:
        logger.error(f"Failed to remove additional_data field: {e}")
        raise

# Migration metadata
MIGRATION_ID = "001_add_additional_data_field"
MIGRATION_DESCRIPTION = "Add additional_data JSON field to jobs table"
DEPENDS_ON = []  # No dependencies for first migration