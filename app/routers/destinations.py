from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import database, models, schemas

router = APIRouter(
    prefix="/destinations",
    tags=["Destinations"]
)

@router.get("/", response_model=List[schemas.DestinationResponse])
def get_destinations(db: Session = Depends(database.get_db), limit: int = 64):
    destinations = db.query(models.Destination).limit(limit).all()
    return destinations

@router.get("/{id}", response_model=schemas.DestinationResponse)
def get_destination(id: str, db: Session = Depends(database.get_db)):
    destination = db.query(models.Destination).filter(models.Destination.id == id).first()
    if not destination:
        raise HTTPException(status_code=404, detail="Destination not found")
    return destination

@router.get("/{id}/places", response_model=List[schemas.PlaceResponse])
def get_destination_places(id: str, db: Session = Depends(database.get_db), type: Optional[str] = None):
    query = db.query(models.Place).filter(models.Place.destination_id == id)
    if type:
        query = query.filter(models.Place.type == type)
    places = query.all()
    return places
