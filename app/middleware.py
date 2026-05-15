"""
Multi-tenant middleware for extracting and validating tenant context
from request headers, JWT claims, or subdomains.
"""

from fastapi import Request, HTTPException, status
from typing import Optional
import jwt
import re
from .config import SECRET_KEY

class TenantContext:
    """Context object for tenant information"""
    def __init__(
        self,
        organization_id: str,
        workspace_id: str,
        user_id: str,
        user_role: str,
        user_email: str
    ):
        self.organization_id = organization_id
        self.workspace_id = workspace_id
        self.user_id = user_id
        self.user_role = user_role
        self.user_email = user_email

    def can_read(self) -> bool:
        """Check if user can read"""
        return self.user_role in ["admin", "editor", "viewer", "guide"]

    def can_write(self) -> bool:
        """Check if user can write"""
        return self.user_role in ["admin", "editor", "guide"]

    def can_delete(self) -> bool:
        """Check if user can delete"""
        return self.user_role == "admin"

    def can_invite(self) -> bool:
        """Check if user can invite others"""
        return self.user_role == "admin"

    def can_manage_settings(self) -> bool:
        """Check if user can manage org settings"""
        return self.user_role == "admin"


async def extract_tenant_context(request: Request) -> Optional[TenantContext]:
    """
    Extract tenant context from:
    1. JWT token in Authorization header
    2. X-Organization-ID and X-Workspace-ID headers
    3. Subdomain ({org}.cholo.app)
    
    Returns TenantContext or None if not found
    """
    
    # Try to extract from Authorization header (JWT)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            tenant_context = TenantContext(
                organization_id=payload.get("org_id"),
                workspace_id=payload.get("workspace_id"),
                user_id=payload.get("sub"),
                user_role=payload.get("role", "viewer"),
                user_email=payload.get("email")
            )
            if tenant_context.organization_id and tenant_context.workspace_id:
                return tenant_context
        except jwt.InvalidTokenError:
            pass
    
    # Try to extract from custom headers
    org_id = request.headers.get("X-Organization-ID")
    workspace_id = request.headers.get("X-Workspace-ID")
    user_id = request.headers.get("X-User-ID")
    user_role = request.headers.get("X-User-Role", "viewer")
    user_email = request.headers.get("X-User-Email", "")
    
    if org_id and workspace_id and user_id:
        return TenantContext(
            organization_id=org_id,
            workspace_id=workspace_id,
            user_id=user_id,
            user_role=user_role,
            user_email=user_email
        )
    
    # Try to extract from subdomain ({org}.cholo.app)
    host = request.headers.get("host", "")
    subdomain_match = re.match(r"^([a-z0-9-]+)\.cholo\.app$", host)
    if subdomain_match:
        org_slug = subdomain_match.group(1)
        # In production, you'd look up org by slug and get IDs from DB
        # For now, return None - this requires DB query
        pass
    
    return None


async def validate_tenant_access(request: Request, required_role: str = "viewer"):
    """
    Validate that user has required role for tenant access.
    
    Usage in endpoints:
    @router.get("/trips")
    async def get_trips(request: Request):
        tenant = await validate_tenant_access(request, required_role="viewer")
        # tenant.organization_id and tenant.workspace_id are available
    """
    
    tenant = await extract_tenant_context(request)
    
    if not tenant or not tenant.organization_id or not tenant.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid tenant context. Include X-Organization-ID, X-Workspace-ID headers or valid JWT."
        )
    
    # Role-based access control
    role_hierarchy = {
        "viewer": 1,
        "guide": 2,
        "editor": 3,
        "admin": 4
    }
    
    user_role_level = role_hierarchy.get(tenant.user_role, 0)
    required_role_level = role_hierarchy.get(required_role, 1)
    
    if user_role_level < required_role_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required role: {required_role}, your role: {tenant.user_role}"
        )
    
    return tenant
