from pydantic import BaseModel, EmailStr
from typing import List, Optional
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
    class Config:
        orm_mode = True

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
    class Config:
        orm_mode = True

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
    class Config:
        orm_mode = True

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
    class Config:
        orm_mode = True

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
    class Config:
        orm_mode = True

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
