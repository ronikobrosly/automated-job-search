#!/usr/bin/env python3
"""
Database initialization script for the automated job search system.
This script sets up the SQLite database and runs initial migrations.
"""

import os
import subprocess
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database import JobOperations, db_manager


def run_alembic_upgrade() -> bool:
    """Run alembic upgrade to create database schema.

    Returns:
        bool: True if migration succeeded, False otherwise.
    """
    print("Running database migrations...")

    # Change to data directory where alembic.ini is located
    data_dir = project_root / "data"
    original_cwd = os.getcwd()

    try:
        os.chdir(data_dir)
        # Run alembic upgrade using uv
        result = subprocess.run(
            ["uv", "run", "alembic", "upgrade", "head"], capture_output=True, text=True
        )

        if result.returncode == 0:
            print("✓ Database migrations completed successfully")
            print(result.stdout)
        else:
            print("✗ Database migration failed:")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"✗ Error running migrations: {e}")
        return False
    finally:
        os.chdir(original_cwd)

    return True


def verify_database() -> bool:
    """Verify that the database was created correctly.

    Returns:
        bool: True if verification succeeded, False otherwise.
    """
    print("Verifying database setup...")

    # Test database connection and basic operations
    with db_manager.get_session() as session:
        stats = JobOperations.get_job_stats(session)
        print(f"✓ Database connection successful")
        print(f"  - Total jobs: {stats['total_jobs']}")
        print(f"  - Database path: {db_manager.engine.url}")

    return True

    # AIDEV-NOTE: Commented out alternative verification approach
    # try:
    #     # Test database connection and basic operations
    #     with next(db_manager.get_session()) as session:
    #         stats = JobOperations.get_job_stats(session)
    #         print(f"✓ Database connection successful")
    #         print(f"  - Total jobs: {stats['total_jobs']}")
    #         print(f"  - Database path: {db_manager.engine.url}")

    #     return True

    # except Exception as e:
    #     print(f"✗ Database verification failed: {e}")
    #     return False


def main() -> None:
    """Main initialization function."""
    print("Initializing automated job search database...")
    print("=" * 50)

    # Step 1: Run migrations
    if not run_alembic_upgrade():
        print("\n❌ Database initialization failed during migration step")
        sys.exit(1)

    # Step 2: Verify database
    if not verify_database():
        print("\n❌ Database initialization failed during verification step")
        sys.exit(1)

    print("\n✅ Database initialization completed successfully!")
    print("\nNext steps:")
    print("- Configure job scraping sites in config/sites/")
    print("- Set up email configuration in config/email/")
    print("- Run the main job scraping pipeline with: python main.py")


if __name__ == "__main__":
    main()
