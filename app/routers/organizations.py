import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import database, models, schemas, security
from ..services import OrganizationService, WorkspaceService, UserOrganizationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/organizations", tags=["Organizations"])


def _require_org_admin(org_id: str, user: models.User, db: Session):
    user_org = db.query(models.UserOrganization).filter(
        models.UserOrganization.organization_id == org_id,
        models.UserOrganization.user_id == user.id,
        models.UserOrganization.role == "admin",
    ).first()
    if not user_org:
        raise HTTPException(status_code=403, detail="Admin access required")


# ── Organizations ──────────────────────────────────────────────────────

@router.post("/", response_model=schemas.OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_organization(
    org: schemas.OrganizationCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    try:
        return OrganizationService.create_organization(db, org, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[schemas.OrganizationResponse])
def list_my_organizations(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    return OrganizationService.list_user_organizations(db, current_user.id)


@router.get("/{org_id}", response_model=schemas.OrganizationResponse)
def get_organization(
    org_id: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    membership = db.query(models.UserOrganization).filter(
        models.UserOrganization.organization_id == org_id,
        models.UserOrganization.user_id == current_user.id,
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    try:
        return OrganizationService.get_organization(db, org_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{org_id}", response_model=schemas.OrganizationResponse)
def update_organization(
    org_id: str,
    updates: schemas.OrganizationUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    _require_org_admin(org_id, current_user, db)
    try:
        org = OrganizationService.get_organization(db, org_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    if updates.name is not None:
        org.name = updates.name
    if updates.domain is not None:
        org.domain = updates.domain
    if updates.branding_config is not None:
        org.branding_config = updates.branding_config
    db.commit()
    db.refresh(org)
    return org


# ── Workspaces ─────────────────────────────────────────────────────────

@router.post("/{org_id}/workspaces", response_model=schemas.WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(
    org_id: str,
    workspace: schemas.WorkspaceCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    _require_org_admin(org_id, current_user, db)
    try:
        return WorkspaceService.create_workspace(db, org_id, workspace)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{org_id}/workspaces", response_model=List[schemas.WorkspaceResponse])
def list_workspaces(
    org_id: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    membership = db.query(models.UserOrganization).filter(
        models.UserOrganization.organization_id == org_id,
        models.UserOrganization.user_id == current_user.id,
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    return WorkspaceService.list_organization_workspaces(db, org_id)


# ── Members ────────────────────────────────────────────────────────────

@router.post("/{org_id}/members", response_model=schemas.UserOrganizationResponse, status_code=status.HTTP_201_CREATED)
def invite_member(
    org_id: str,
    invite: schemas.UserOrganizationCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    _require_org_admin(org_id, current_user, db)
    try:
        return UserOrganizationService.invite_user(db, org_id, invite)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{org_id}/members/{user_id}", response_model=schemas.UserOrganizationResponse)
def update_member_role(
    org_id: str,
    user_id: str,
    update: schemas.UserOrganizationUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    _require_org_admin(org_id, current_user, db)
    try:
        return UserOrganizationService.set_user_role(db, org_id, user_id, update.role)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    org_id: str,
    user_id: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    _require_org_admin(org_id, current_user, db)
    try:
        UserOrganizationService.remove_user(db, org_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Switch active org/workspace ────────────────────────────────────────

@router.post("/{org_id}/switch", response_model=schemas.UserResponseWithTenant)
def switch_organization(
    org_id: str,
    workspace_id: str = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    membership = db.query(models.UserOrganization).filter(
        models.UserOrganization.organization_id == org_id,
        models.UserOrganization.user_id == current_user.id,
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    current_user.current_organization_id = org_id
    if workspace_id:
        ws = db.query(models.Workspace).filter(
            models.Workspace.id == workspace_id,
            models.Workspace.organization_id == org_id,
        ).first()
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found in this organization")
        current_user.current_workspace_id = workspace_id
    else:
        default_ws = db.query(models.Workspace).filter(
            models.Workspace.organization_id == org_id,
            models.Workspace.is_default == True,
        ).first()
        current_user.current_workspace_id = default_ws.id if default_ws else None

    db.commit()
    db.refresh(current_user)
    return current_user
