from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import database, models, schemas, security

router = APIRouter(
    prefix="/trips",
    tags=["Trips"]
)

@router.post("/", response_model=schemas.TripResponse, status_code=status.HTTP_201_CREATED)
def create_trip(
    trip: schemas.TripCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    new_trip = models.Trip(
        **trip.dict(),
        user_id=current_user.id
    )
    db.add(new_trip)
    db.commit()
    db.refresh(new_trip)
    return new_trip

@router.get("/{id}", response_model=schemas.TripResponse)
def get_trip(id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    trip = db.query(models.Trip).filter(models.Trip.id == id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    # allow any authenticated user to view the trip for bill splitting context, 
    # or optionally strict it to trip.user_id == current_user.id
    return trip

@router.post("/{id}/expenses", response_model=schemas.ExpenseResponse, status_code=status.HTTP_201_CREATED)
def add_expense(
    id: str, 
    expense: schemas.ExpenseCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    trip = db.query(models.Trip).filter(models.Trip.id == id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    new_expense = models.Expense(
        **expense.dict(),
        trip_id=id,
        user_id=current_user.id
    )
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return new_expense

@router.get("/{id}/settlements", response_model=schemas.SettlementResponse)
def get_trip_settlements(id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    trip = db.query(models.Trip).filter(models.Trip.id == id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    expenses = db.query(models.Expense).filter(models.Expense.trip_id == id).all()
    
    total_spent = sum(e.amount for e in expenses)
    per_person = total_spent / trip.num_people if trip.num_people > 0 else 0
    
    # Calculate how much each 'paid_by_name' has spent
    spent_by_person = {}
    for e in expenses:
        name = e.paid_by_name
        spent_by_person[name] = spent_by_person.get(name, 0) + e.amount
        
    balances = {name: amount - per_person for name, amount in spent_by_person.items()}
    
    # Simplified splitting logic
    debtors = []
    creditors = []
    for name, balance in balances.items():
        if balance < 0:
            debtors.append({"name": name, "amount": -balance})
        elif balance > 0:
            creditors.append({"name": name, "amount": balance})
            
    debtors.sort(key=lambda x: x["amount"], reverse=True)
    creditors.sort(key=lambda x: x["amount"], reverse=True)
    
    actions = []
    i, j = 0, 0
    while i < len(debtors) and j < len(creditors):
        debtor = debtors[i]
        creditor = creditors[j]
        
        amount = min(debtor["amount"], creditor["amount"])
        
        actions.append(schemas.SettlementAction(
            from_user=debtor["name"],
            to_user=creditor["name"],
            amount=round(amount, 2)
        ))
        
        debtors[i]["amount"] -= amount
        creditors[j]["amount"] -= amount
        
        if debtors[i]["amount"] < 0.01:
            i += 1
        if creditors[j]["amount"] < 0.01:
            j += 1
            
    return schemas.SettlementResponse(
        total_spent=round(total_spent, 2),
        per_person=round(per_person, 2),
        actions=actions
    )
