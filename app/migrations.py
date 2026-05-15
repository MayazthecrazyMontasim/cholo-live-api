"""
Database migration script for multi-tenancy schema.

This script adds the necessary tables for multi-tenant support:
- organizations
- workspaces
- user_organizations

It also adds tenant columns to existing tables:
- users: current_organization_id, current_workspace_id, full_name
- trips: organization_id, workspace_id
- expenses: organization_id, workspace_id
- destinations: organization_id

Usage:
  python -m app.migrations.create_tenant_schema
"""

from sqlalchemy import create_engine, text, inspect
from app.database import engine, Base
from app.models import (
    Organization, Workspace, UserOrganization, User,
    Trip, Expense, Destination
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_to_multi_tenant():
    """
    Create multi-tenant schema.
    This is idempotent - it checks if tables exist before creating.
    """
    
    with engine.begin() as connection:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        logger.info(f"Existing tables: {existing_tables}")
        
        # Create new tenant tables
        logger.info("Creating multi-tenant tables...")
        Base.metadata.create_all(engine)
        logger.info("✓ Multi-tenant tables created successfully")
        
        # Add columns to existing User table if they don't exist
        logger.info("Checking User table columns...")
        user_columns = [col['name'] for col in inspector.get_columns('users')]
        
        if 'current_organization_id' not in user_columns:
            logger.info("  Adding current_organization_id to users...")
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN current_organization_id VARCHAR"
            ))
            connection.commit()
            logger.info("  ✓ Added current_organization_id")
        
        if 'current_workspace_id' not in user_columns:
            logger.info("  Adding current_workspace_id to users...")
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN current_workspace_id VARCHAR"
            ))
            connection.commit()
            logger.info("  ✓ Added current_workspace_id")
        
        if 'full_name' not in user_columns:
            logger.info("  Adding full_name to users...")
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN full_name VARCHAR"
            ))
            connection.commit()
            logger.info("  ✓ Added full_name")
        
        if 'updated_at' not in user_columns:
            logger.info("  Adding updated_at to users...")
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"
            ))
            connection.commit()
            logger.info("  ✓ Added updated_at")
        
        # Add columns to Trip table if they don't exist
        logger.info("Checking Trip table columns...")
        trip_columns = [col['name'] for col in inspector.get_columns('trips')]
        
        if 'organization_id' not in trip_columns:
            logger.info("  Adding organization_id to trips...")
            connection.execute(text(
                "ALTER TABLE trips ADD COLUMN organization_id VARCHAR"
            ))
            connection.commit()
            logger.info("  ✓ Added organization_id")
        
        if 'workspace_id' not in trip_columns:
            logger.info("  Adding workspace_id to trips...")
            connection.execute(text(
                "ALTER TABLE trips ADD COLUMN workspace_id VARCHAR"
            ))
            connection.commit()
            logger.info("  ✓ Added workspace_id")
        
        if 'updated_at' not in trip_columns:
            logger.info("  Adding updated_at to trips...")
            connection.execute(text(
                "ALTER TABLE trips ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"
            ))
            connection.commit()
            logger.info("  ✓ Added updated_at")
        
        # Add columns to Expense table if they don't exist
        logger.info("Checking Expense table columns...")
        expense_columns = [col['name'] for col in inspector.get_columns('expenses')]
        
        if 'organization_id' not in expense_columns:
            logger.info("  Adding organization_id to expenses...")
            connection.execute(text(
                "ALTER TABLE expenses ADD COLUMN organization_id VARCHAR"
            ))
            connection.commit()
            logger.info("  ✓ Added organization_id")
        
        if 'workspace_id' not in expense_columns:
            logger.info("  Adding workspace_id to expenses...")
            connection.execute(text(
                "ALTER TABLE expenses ADD COLUMN workspace_id VARCHAR"
            ))
            connection.commit()
            logger.info("  ✓ Added workspace_id")
        
        if 'updated_at' not in expense_columns:
            logger.info("  Adding updated_at to expenses...")
            connection.execute(text(
                "ALTER TABLE expenses ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"
            ))
            connection.commit()
            logger.info("  ✓ Added updated_at")
        
        # Add columns to Destination table if they don't exist
        logger.info("Checking Destination table columns...")
        dest_columns = [col['name'] for col in inspector.get_columns('destinations')]
        
        if 'organization_id' not in dest_columns:
            logger.info("  Adding organization_id to destinations...")
            connection.execute(text(
                "ALTER TABLE destinations ADD COLUMN organization_id VARCHAR"
            ))
            connection.commit()
            logger.info("  ✓ Added organization_id")
        
        if 'created_at' not in dest_columns:
            logger.info("  Adding created_at to destinations...")
            connection.execute(text(
                "ALTER TABLE destinations ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"
            ))
            connection.commit()
            logger.info("  ✓ Added created_at")
    
    logger.info("\n✓ Migration completed successfully!")

if __name__ == "__main__":
    migrate_to_multi_tenant()
