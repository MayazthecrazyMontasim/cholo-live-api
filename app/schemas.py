from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    is_admin: bool
    created_at: datetime
    model_config = {"from_attributes": True}

class DestinationBase(BaseModel):
    name: str
    division: str
    tagline: str
    emoji: str
    lat: float
    lng: float
    description: str

class DestinationCreate(DestinationBase):
    pass

class DestinationResponse(DestinationBase):
    id: str
    model_config = {"from_attributes": True}

class PlaceBase(BaseModel):
    type: str # hotel, bike_rental, bus_counter, restaurant
    name: str
    detail_text: str
    address: str
    price: float
    badge: str

class PlaceCreate(PlaceBase):
    pass

class PlaceResponse(PlaceBase):
    id: str
    destination_id: str
    model_config = {"from_attributes": True}

class TripBase(BaseModel):
    num_people: int
    num_days: int
    trip_type: str
    start_city: str
    destination_id: str
    selected_service_ids: str # Comma separated Place IDs for simplicity, could be validated
    total_budget: float

class TripCreate(TripBase):
    pass

class TripResponse(TripBase):
    id: str
    user_id: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}

class ExpenseBase(BaseModel):
    paid_by_name: str
    amount: float
    category: str
    note: str

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseResponse(ExpenseBase):
    id: str
    trip_id: str
    user_id: Optional[str] = None
    model_config = {"from_attributes": True}

class SettlementAction(BaseModel):
    from_user: str
    to_user: str
    amount: float

class SettlementResponse(BaseModel):
    total_spent: float
    per_person: float
    actions: List[SettlementAction]

class BudgetEstimateRequest(BaseModel):
    num_people: int
    num_days: int
    trip_type: str
    destination_id: str
    selected_service_ids: Optional[List[str]] = []
    
class BudgetEstimateResponse(BaseModel):
    total_cost: float
    per_person: float
    breakdown: dict
    smart_tip: str


# ===== Multi-Tenant Schemas =====

class OrganizationCreate(BaseModel):
    name: str
    slug: str
    domain: Optional[str] = None
    branding_config: Optional[Dict[str, Any]] = None

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    branding_config: Optional[Dict[str, Any]] = None

class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    domain: Optional[str]
    owner_id: str
    branding_config: Dict[str, Any]
    created_at: datetime
    
    model_config = {"from_attributes": True}

class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_default: bool = False

class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None

class WorkspaceResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    description: Optional[str]
    is_default: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}

class UserOrganizationCreate(BaseModel):
    email: str
    role: str = "viewer"  # admin, editor, viewer, guide

class UserOrganizationUpdate(BaseModel):
    role: str

class UserOrganizationResponse(BaseModel):
    id: str
    user_id: str
    organization_id: str
    role: str
    created_at: datetime
    
    model_config = {"from_attributes": True}

class UserCreateWithOrg(BaseModel):
    """User creation with automatic organization setup"""
    username: str
    email: EmailStr
    password: str
    full_name: str
    organization_name: str

class UserResponseWithTenant(UserResponse):
    """Extended user response with tenant context"""
    current_organization_id: Optional[str] = None
    current_workspace_id: Optional[str] = None
    full_name: Optional[str] = None
    updated_at: datetime
    
    model_config = {"from_attributes": True}

class TenantContextSchema(BaseModel):
    """Response for tenant context validation"""
    organization_id: str
    workspace_id: str
    user_id: str
    user_role: str
    user_email: str
    can_read: bool
    can_write: bool
    can_delete: bool
    can_invite: bool
    can_manage_settings: bool

