#!/usr/bin/env python
"""
Setup script for Cholo multi-tenant database.

This script:
1. Creates all database tables
2. Runs migrations for multi-tenancy
3. Seeds initial data if needed

Usage:
  python setup_db.py [--seed]
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import engine, Base, init_db
from app.models import Organization, Workspace, User, UserOrganization
from app.migrations import migrate_to_multi_tenant
from app.security import get_password_hash
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_database():
    """Initialize database schema"""
    logger.info("=" * 60)
    logger.info("CHOLO MULTI-TENANT DATABASE SETUP")
    logger.info("=" * 60)
    
    # Create all tables
    logger.info("\n1. Creating database tables...")
    try:
        Base.metadata.create_all(engine)
        logger.info("✓ Database tables created")
    except Exception as e:
        logger.error(f"✗ Failed to create tables: {e}")
        return False
    
    # Run migrations
    logger.info("\n2. Running multi-tenant migrations...")
    try:
        migrate_to_multi_tenant()
        logger.info("✓ Migrations completed")
    except Exception as e:
        logger.error(f"✗ Migration failed: {e}")
        return False
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ DATABASE SETUP COMPLETED SUCCESSFULLY")
    logger.info("=" * 60)
    
    return True

def seed_sample_data():
    """Seed sample organizations and workspaces (optional)"""
    from sqlalchemy.orm import sessionmaker
    
    logger.info("\n3. Seeding sample data...")
    
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Check if sample data already exists
        sample_user = db.query(User).filter(
            User.email == "admin@cholo.local"
        ).first()
        
        if sample_user:
            logger.info("✓ Sample data already exists, skipping seed")
            return
        
        # Create sample user
        logger.info("  Creating sample user (admin@cholo.local)...")
        admin_user = User(
            username="admin",
            email="admin@cholo.local",
            full_name="Admin User",
            hashed_password=get_password_hash("admin123"),  # Change in production!
            is_admin=True
        )
        db.add(admin_user)
        db.flush()
        
        # Create sample organization
        logger.info("  Creating sample organization...")
        org = Organization(
            name="Cholo Demo Agency",
            slug="cholo-demo",
            domain="demo.cholo.app",
            owner_id=admin_user.id,
            branding_config={
                "app_name": "Cholo Demo",
                "primary_color": "#10b981",
                "logo_url": "https://cholo.app/logo.png"
            }
        )
        db.add(org)
        db.flush()
        
        # Create default workspace
        logger.info("  Creating default workspace...")
        workspace = Workspace(
            organization_id=org.id,
            name="Bangladesh Tours",
            description="Default workspace for Bangladesh travel packages",
            is_default=True
        )
        db.add(workspace)
        db.flush()
        
        # Create user-organization relationship
        logger.info("  Assigning user to organization...")
        user_org = UserOrganization(
            user_id=admin_user.id,
            organization_id=org.id,
            role="admin",
            default_workspace_id=workspace.id
        )
        db.add(user_org)
        
        db.commit()
        logger.info("✓ Sample data created successfully")
        logger.info("\n  Sample credentials:")
        logger.info("  Email: admin@cholo.local")
        logger.info("  Password: admin123")
        logger.info("  Organization: Cholo Demo Agency")
        logger.info("  ⚠️  CHANGE THESE IN PRODUCTION!")
        
    except Exception as e:
        logger.error(f"✗ Failed to seed data: {e}")
        db.rollback()
        return False
    finally:
        db.close()
    
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup Cholo database")
    parser.add_argument("--seed", action="store_true", help="Seed sample data")
    args = parser.parse_args()
    
    success = setup_database()
    
    if success and args.seed:
        success = seed_sample_data()
    
    sys.exit(0 if success else 1)
