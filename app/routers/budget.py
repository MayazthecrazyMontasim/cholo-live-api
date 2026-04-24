from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import database, models, schemas

router = APIRouter(
    prefix="/budget",
    tags=["Budget"]
)

@router.post("/estimate", response_model=schemas.BudgetEstimateResponse)
def estimate_budget(request: schemas.BudgetEstimateRequest, db: Session = Depends(database.get_db)):
    # Standard baseline factors based on trip type
    base_per_day = {
        "budget": 1500,
        "mid": 4000,
        "luxury": 15000
    }
    
    trip_type = request.trip_type.lower()
    if trip_type not in base_per_day:
        trip_type = "mid"
        
    daily_cost_pp = base_per_day[trip_type]
    
    # Calculate costs based on services selected
    services_cost = 0.0
    if request.selected_service_ids:
        places = db.query(models.Place).filter(models.Place.id.in_(request.selected_service_ids)).all()
        for p in places:
            # Simple assumption: a place cost is per person
            services_cost += p.price
            
    # Base calculation
    base_cost_pp = (daily_cost_pp * request.num_days) + services_cost
    total_cost = base_cost_pp * request.num_people
    
    # Breakdown approximation
    breakdown = {
        "accommodation": total_cost * 0.40,
        "food": total_cost * 0.30,
        "transport": total_cost * 0.20,
        "activities": total_cost * 0.05,
        "misc": total_cost * 0.05
    }
    
    smart_tip = f"For a {trip_type} trip to this destination, plan to book accommodations well in advance for better rates!"
    
    return schemas.BudgetEstimateResponse(
        total_cost=total_cost,
        per_person=base_cost_pp,
        breakdown=breakdown,
        smart_tip=smart_tip
    )
