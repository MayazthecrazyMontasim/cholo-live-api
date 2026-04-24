from sqlalchemy import Column, ForeignKey, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from .database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    trips = relationship("Trip", back_populates="user")
    expenses = relationship("Expense", back_populates="user")

class Destination(Base):
    __tablename__ = "destinations"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, index=True)
    division = Column(String)
    tagline = Column(String)
    emoji = Column(String)
    lat = Column(Float)
    lng = Column(Float)
    description = Column(String)

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
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    num_people = Column(Integer)
    num_days = Column(Integer)
    trip_type = Column(String) # budget, mid, luxury
    start_city = Column(String)
    destination_id = Column(String, ForeignKey("destinations.id"))
    selected_service_ids = Column(String) # Comma separated list of Place IDs
    total_budget = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="trips")
    destination = relationship("Destination", back_populates="trips")
    expenses = relationship("Expense", back_populates="trip")

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(String, primary_key=True, default=generate_uuid)
    trip_id = Column(String, ForeignKey("trips.id"))
    user_id = Column(String, ForeignKey("users.id"), nullable=True) 
    paid_by_name = Column(String) 
    amount = Column(Float)
    category = Column(String) # accommodation, food, transport, activities, misc
    note = Column(String)
    
    trip = relationship("Trip", back_populates="expenses")
    user = relationship("User", back_populates="expenses")
