"""
Service layer for multi-tenant operations.
Handles organization, workspace, and user management.
"""

from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import (
    Organization, Workspace, User, UserOrganization
)
from app.schemas import (
    OrganizationCreate, WorkspaceCreate, UserOrganizationCreate
)
from app.security import get_password_hash, verify_password
import logging

logger = logging.getLogger(__name__)

class OrganizationService:
    """Service for organization management"""
    
    @staticmethod
    def create_organization(
        db: Session,
        org_data: OrganizationCreate,
        owner_id: str
    ) -> Organization:
        """Create a new organization"""
        
        # Check if slug already exists
        existing = db.query(Organization).filter(
            Organization.slug == org_data.slug
        ).first()
        
        if existing:
            raise ValueError(f"Organization slug '{org_data.slug}' already exists")
        
        org = Organization(
            name=org_data.name,
            slug=org_data.slug,
            domain=org_data.domain,
            owner_id=owner_id,
            branding_config=org_data.branding_config or {}
        )
        
        db.add(org)
        db.flush()
        
        # Create default workspace
        default_workspace = Workspace(
            organization_id=org.id,
            name="Default",
            is_default=True
        )
        db.add(default_workspace)
        
        # Assign owner as admin
        user_org = UserOrganization(
            user_id=owner_id,
            organization_id=org.id,
            role="admin",
            default_workspace_id=default_workspace.id
        )
        db.add(user_org)
        db.commit()
        
        logger.info(f"Created organization '{org.name}' (id: {org.id})")
        return org
    
    @staticmethod
    def get_organization(db: Session, org_id: str) -> Organization:
        """Get organization by ID"""
        org = db.query(Organization).filter(
            Organization.id == org_id
        ).first()
        
        if not org:
            raise ValueError(f"Organization '{org_id}' not found")
        
        return org
    
    @staticmethod
    def get_organization_by_slug(db: Session, slug: str) -> Organization:
        """Get organization by slug"""
        org = db.query(Organization).filter(
            Organization.slug == slug
        ).first()
        
        if not org:
            raise ValueError(f"Organization with slug '{slug}' not found")
        
        return org
    
    @staticmethod
    def list_user_organizations(db: Session, user_id: str) -> list[Organization]:
        """List all organizations a user belongs to"""
        user_orgs = db.query(UserOrganization).filter(
            UserOrganization.user_id == user_id
        ).all()
        
        org_ids = [uo.organization_id for uo in user_orgs]
        orgs = db.query(Organization).filter(
            Organization.id.in_(org_ids)
        ).all()
        
        return orgs


class WorkspaceService:
    """Service for workspace management"""
    
    @staticmethod
    def create_workspace(
        db: Session,
        org_id: str,
        workspace_data: WorkspaceCreate
    ) -> Workspace:
        """Create a new workspace in organization"""
        
        # Verify organization exists
        org = db.query(Organization).filter(
            Organization.id == org_id
        ).first()
        
        if not org:
            raise ValueError(f"Organization '{org_id}' not found")
        
        # If this is the first workspace, make it default
        existing_count = db.query(Workspace).filter(
            Workspace.organization_id == org_id
        ).count()
        
        workspace = Workspace(
            organization_id=org_id,
            name=workspace_data.name,
            description=workspace_data.description,
            is_default=workspace_data.is_default or (existing_count == 0)
        )
        
        db.add(workspace)
        db.commit()
        
        logger.info(f"Created workspace '{workspace.name}' in org '{org_id}'")
        return workspace
    
    @staticmethod
    def get_workspace(db: Session, workspace_id: str) -> Workspace:
        """Get workspace by ID"""
        workspace = db.query(Workspace).filter(
            Workspace.id == workspace_id
        ).first()
        
        if not workspace:
            raise ValueError(f"Workspace '{workspace_id}' not found")
        
        return workspace
    
    @staticmethod
    def list_organization_workspaces(
        db: Session,
        org_id: str
    ) -> list[Workspace]:
        """List all workspaces in organization"""
        return db.query(Workspace).filter(
            Workspace.organization_id == org_id
        ).all()


class UserOrganizationService:
    """Service for user-organization relationships"""
    
    @staticmethod
    def invite_user(
        db: Session,
        org_id: str,
        invite_data: UserOrganizationCreate
    ) -> UserOrganization:
        """Invite user to organization"""
        
        # Find user by email
        user = db.query(User).filter(
            User.email == invite_data.email
        ).first()
        
        if not user:
            raise ValueError(f"User with email '{invite_data.email}' not found")
        
        # Check if already a member
        existing = db.query(UserOrganization).filter(
            UserOrganization.user_id == user.id,
            UserOrganization.organization_id == org_id
        ).first()
        
        if existing:
            raise ValueError(f"User '{invite_data.email}' is already in this organization")
        
        # Get default workspace
        workspace = db.query(Workspace).filter(
            Workspace.organization_id == org_id,
            Workspace.is_default == True
        ).first()
        
        user_org = UserOrganization(
            user_id=user.id,
            organization_id=org_id,
            role=invite_data.role,
            default_workspace_id=workspace.id if workspace else None
        )
        
        db.add(user_org)
        db.commit()
        
        logger.info(f"Invited user '{invite_data.email}' to organization '{org_id}' with role '{invite_data.role}'")
        return user_org
    
    @staticmethod
    def set_user_role(
        db: Session,
        org_id: str,
        user_id: str,
        new_role: str
    ) -> UserOrganization:
        """Update user role in organization"""
        
        user_org = db.query(UserOrganization).filter(
            UserOrganization.user_id == user_id,
            UserOrganization.organization_id == org_id
        ).first()
        
        if not user_org:
            raise ValueError(f"User '{user_id}' not found in organization '{org_id}'")
        
        user_org.role = new_role
        db.commit()
        
        logger.info(f"Updated user '{user_id}' role to '{new_role}' in org '{org_id}'")
        return user_org
    
    @staticmethod
    def remove_user(
        db: Session,
        org_id: str,
        user_id: str
    ):
        """Remove user from organization"""
        
        user_org = db.query(UserOrganization).filter(
            UserOrganization.user_id == user_id,
            UserOrganization.organization_id == org_id
        ).first()
        
        if not user_org:
            raise ValueError(f"User '{user_id}' not found in organization '{org_id}'")
        
        db.delete(user_org)
        db.commit()
        
        logger.info(f"Removed user '{user_id}' from organization '{org_id}'")
    
    @staticmethod
    def get_user_role(
        db: Session,
        org_id: str,
        user_id: str
    ) -> str:
        """Get user role in organization"""
        
        user_org = db.query(UserOrganization).filter(
            UserOrganization.user_id == user_id,
            UserOrganization.organization_id == org_id
        ).first()
        
        if not user_org:
            return None
        
        return user_org.role
