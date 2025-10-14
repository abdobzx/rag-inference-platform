#!/usr/bin/env python3
"""
Database setup script for SothemaAI auth service.
Creates tables and runs initial migration.
"""

import os
import sys
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """Create database tables"""
    try:
        from src.database import Base, engine
        from src.models.user import User
        from src.models.api_key import APIKey

        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created successfully!")

        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Created tables: {tables}")

        for table in tables:
            if table not in ['alembic_version']:
                columns = inspector.get_columns(table)
                logger.info(f"Table {table} columns: {[col['name'] for col in columns]}")

    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        return False
    return True

def run_migration():
    """Run alembic migration"""
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, '-m', 'alembic', 'revision', '--autogenerate', '-m', 'Create users and api_keys tables'
        ], cwd=os.path.dirname(__file__), capture_output=True, text=True)

        if result.returncode == 0:
            logger.info("Migration created successfully")
            logger.info(result.stdout)
        else:
            logger.error(f"Migration failed: {result.stderr}")
            return False

        # Run the migration
        result = subprocess.run([
            sys.executable, '-m', 'alembic', 'upgrade', 'head'
        ], cwd=os.path.dirname(__file__), capture_output=True, text=True)

        if result.returncode == 0:
            logger.info("Migration applied successfully")
            logger.info(result.stdout)
        else:
            logger.error(f"Migration application failed: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Error running migration: {e}")
        return False
    return True

if __name__ == "__main__":
    logger.info("Setting up SothemaAI auth service database...")

    if create_tables():
        logger.info("Database setup completed successfully!")
    else:
        logger.error("Database setup failed!")
        sys.exit(1)