from sqlalchemy import Column, ForeignKey, Integer, String, Float, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from .database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, index=True, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    domain = Column(String, unique=True, nullable=True)  # Custom domain for tenant
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    branding_config = Column(JSON, default={})  # Logo, colors, app name, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", foreign_keys=[owner_id], backref="owned_organizations")
    workspaces = relationship("Workspace", back_populates="organization", cascade="all, delete-orphan")
    users = relationship("UserOrganization", back_populates="organization", cascade="all, delete-orphan")
    trips = relationship("Trip", back_populates="organization")
    destinations = relationship("Destination", back_populates="organization")

class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization", back_populates="workspaces")
    trips = relationship("Trip", back_populates="workspace")

class UserOrganization(Base):
    """Join table for users and organizations with roles"""
    __tablename__ = "user_organizations"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    role = Column(String, default="member")  # admin, editor, viewer, guide
    default_workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="organization_memberships")
    organization = relationship("Organization", back_populates="users")

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    # Tenant context (will be set by middleware)
    current_organization_id = Column(String, ForeignKey("organizations.id"), nullable=True)
    current_workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    trips = relationship("Trip", back_populates="user", foreign_keys="Trip.user_id")
    expenses = relationship("Expense", back_populates="user")
    current_organization = relationship("Organization", foreign_keys=[current_organization_id])
    current_workspace = relationship("Workspace", foreign_keys=[current_workspace_id])

class Destination(Base):
    __tablename__ = "destinations"

    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=True)  # NULL = global destinations
    name = Column(String, index=True)
    division = Column(String)
    tagline = Column(String)
    emoji = Column(String)
    lat = Column(Float)
    lng = Column(Float)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="destinations")
    places = relationship("Place", back_populates="destination")
    trips = relationship("Trip", back_populates="destination")

class Place(Base):
    __tablename__ = "places"

    id = Column(String, primary_key=True, default=generate_uuid)
    destination_id = Column(String, ForeignKey("destinations.id"))
    type = Column(String) # hotel, bike_rental, bus_counter, restaurant
    name = Column(String)
    detail_text = Column(String)
    address = Column(String)
    price = Column(Float)
    badge = Column(String) # Popular, Budget, Luxury, Eco

    destination = relationship("Destination", back_populates="places")

class Trip(Base):
    __tablename__ = "trips"

    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=True)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    num_people = Column(Integer)
    num_days = Column(Integer)
    trip_type = Column(String) # budget, mid, luxury
    start_city = Column(String)
    destination_id = Column(String, ForeignKey("destinations.id"))
    selected_service_ids = Column(String) # Comma separated list of Place IDs
    total_budget = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization", back_populates="trips")
    workspace = relationship("Workspace", back_populates="trips")
    user = relationship("User", back_populates="trips", foreign_keys=[user_id])
    destination = relationship("Destination", back_populates="trips")
    expenses = relationship("Expense", back_populates="trip")

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=True)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=True)
    trip_id = Column(String, ForeignKey("trips.id"))
    user_id = Column(String, ForeignKey("users.id"), nullable=True) 
    paid_by_name = Column(String) 
    amount = Column(Float)
    category = Column(String) # accommodation, food, transport, activities, misc
    note = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    organization = relationship("Organization", foreign_keys=[organization_id])
    workspace = relationship("Workspace", foreign_keys=[workspace_id])
    trip = relationship("Trip", back_populates="expenses")
    user = relationship("User", back_populates="expenses")
