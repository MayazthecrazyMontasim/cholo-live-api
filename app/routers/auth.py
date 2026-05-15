import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Optional
from pydantic import BaseModel
from .. import database, models, schemas, security
from ..services import OrganizationService
from ..schemas import OrganizationCreate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None


@router.post("/register", response_model=schemas.UserResponseWithTenant, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(
        or_(models.User.email == user.email, models.User.username == user.username)
    ).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email or username already registered")

    hashed_password = security.get_password_hash(user.password)
    new_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
    )
    db.add(new_user)
    db.flush()

    # Auto-create a personal organization for every new user
    try:
        import re
        slug_base = re.sub(r"[^a-z0-9]", "-", user.username.lower())[:30]
        slug = slug_base
        # Ensure slug uniqueness
        counter = 1
        while db.query(models.Organization).filter(models.Organization.slug == slug).first():
            slug = f"{slug_base}-{counter}"
            counter += 1

        org = models.Organization(
            name=f"{user.username}'s Workspace",
            slug=slug,
            owner_id=new_user.id,
            branding_config={},
        )
        db.add(org)
        db.flush()

        workspace = models.Workspace(
            organization_id=org.id,
            name="Personal",
            is_default=True,
        )
        db.add(workspace)
        db.flush()

        user_org = models.UserOrganization(
            user_id=new_user.id,
            organization_id=org.id,
            role="admin",
            default_workspace_id=workspace.id,
        )
        db.add(user_org)

        new_user.current_organization_id = org.id
        new_user.current_workspace_id = workspace.id

        db.commit()
        db.refresh(new_user)
        logger.info("Registered user '%s' with personal org '%s'", user.username, org.slug)
    except Exception as exc:
        db.rollback()
        logger.error("Registration failed for '%s': %s", user.username, exc)
        raise HTTPException(status_code=500, detail="Registration failed. Please try again.")

    return new_user


@router.post("/token", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(database.get_db),
):
    user = db.query(models.User).filter(
        or_(models.User.username == form_data.username, models.User.email == form_data.username)
    ).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    logger.info("User '%s' logged in", user.username)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserResponseWithTenant)
def read_users_me(current_user: models.User = Depends(security.get_current_user)):
    return current_user


@router.patch("/me", response_model=schemas.UserResponseWithTenant)
def update_profile(
    updates: UserUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    if updates.full_name is not None:
        current_user.full_name = updates.full_name
    if updates.email is not None:
        existing = db.query(models.User).filter(
            models.User.email == updates.email,
            models.User.id != current_user.id,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = updates.email
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/logout")
def logout(current_user: models.User = Depends(security.get_current_user)):
    # JWT is stateless; client discards token. This endpoint confirms logout.
    logger.info("User '%s' logged out", current_user.username)
    return {"message": "Logged out successfully"}


@router.post("/change-password")
def change_password(
    current_password: str,
    new_password: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    if not security.verify_password(current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    current_user.hashed_password = security.get_password_hash(new_password)
    db.commit()
    return {"message": "Password updated successfully"}
