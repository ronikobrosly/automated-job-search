"""
Database migrations package

This package contains database migration scripts to manage schema changes
over time while preserving existing data.
"""

import importlib
import logging
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy.engine import Engine
from sqlalchemy import text

logger = logging.getLogger(__name__)

class MigrationManager:
    """Manages database migrations"""
    
    def __init__(self, engine: Engine):
        self.engine = engine
        self.migrations_dir = Path(__file__).parent
        self._ensure_migration_table()
    
    def _ensure_migration_table(self):
        """Create migrations tracking table if it doesn't exist"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        migration_id VARCHAR(255) PRIMARY KEY,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        description TEXT
                    )
                """))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to create schema_migrations table: {e}")
            raise
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of already applied migrations"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT migration_id FROM schema_migrations 
                    ORDER BY applied_at
                """))
                return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Failed to get applied migrations: {e}")
            return []
    
    def get_available_migrations(self) -> List[Dict[str, Any]]:
        """Get list of available migration files"""
        migrations = []
        for migration_file in sorted(self.migrations_dir.glob("???.py")):
            if migration_file.name.startswith("__"):
                continue
            
            try:
                module_name = f"src.database.migrations.{migration_file.stem}"
                module = importlib.import_module(module_name)
                
                migrations.append({
                    'id': getattr(module, 'MIGRATION_ID', migration_file.stem),
                    'description': getattr(module, 'MIGRATION_DESCRIPTION', ''),
                    'depends_on': getattr(module, 'DEPENDS_ON', []),
                    'module': module,
                    'filename': migration_file.name
                })
            except Exception as e:
                logger.warning(f"Failed to load migration {migration_file}: {e}")
        
        return migrations
    
    def get_pending_migrations(self) -> List[Dict[str, Any]]:
        """Get migrations that haven't been applied yet"""
        applied = set(self.get_applied_migrations())
        available = self.get_available_migrations()
        return [m for m in available if m['id'] not in applied]
    
    def apply_migration(self, migration: Dict[str, Any]):
        """Apply a single migration"""
        try:
            logger.info(f"Applying migration: {migration['id']} - {migration['description']}")
            
            # Execute the upgrade function
            migration['module'].upgrade(self.engine)
            
            # Record the migration as applied
            with self.engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO schema_migrations (migration_id, description)
                    VALUES (:migration_id, :description)
                """), {
                    'migration_id': migration['id'],
                    'description': migration['description']
                })
                conn.commit()
            
            logger.info(f"Successfully applied migration: {migration['id']}")
            
        except Exception as e:
            logger.error(f"Failed to apply migration {migration['id']}: {e}")
            raise
    
    def rollback_migration(self, migration_id: str):
        """Rollback a specific migration"""
        try:
            available = {m['id']: m for m in self.get_available_migrations()}
            if migration_id not in available:
                raise ValueError(f"Migration {migration_id} not found")
            
            migration = available[migration_id]
            logger.info(f"Rolling back migration: {migration_id}")
            
            # Execute the downgrade function
            migration['module'].downgrade(self.engine)
            
            # Remove from applied migrations
            with self.engine.connect() as conn:
                conn.execute(text("""
                    DELETE FROM schema_migrations 
                    WHERE migration_id = :migration_id
                """), {'migration_id': migration_id})
                conn.commit()
            
            logger.info(f"Successfully rolled back migration: {migration_id}")
            
        except Exception as e:
            logger.error(f"Failed to rollback migration {migration_id}: {e}")
            raise
    
    def migrate(self):
        """Apply all pending migrations"""
        pending = self.get_pending_migrations()
        
        if not pending:
            logger.info("No pending migrations to apply")
            return
        
        logger.info(f"Found {len(pending)} pending migrations")
        
        for migration in pending:
            self.apply_migration(migration)
        
        logger.info("All migrations applied successfully")
    
    def status(self):
        """Print migration status"""
        applied = self.get_applied_migrations()
        available = {m['id']: m for m in self.get_available_migrations()}
        
        print("Migration Status:")
        print("================")
        
        for migration_id in sorted(available.keys()):
            migration = available[migration_id]
            status = "Applied" if migration_id in applied else "Pending"
            print(f"{migration_id:30} {status:10} {migration['description']}")
        
        if not available:
            print("No migrations found")