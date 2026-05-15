import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import database, models, schemas, security

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trips", tags=["Trips"])


def _get_trip_or_404(id: str, db: Session, user: models.User) -> models.Trip:
    trip = db.query(models.Trip).filter(
        models.Trip.id == id,
        models.Trip.user_id == user.id,
    ).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.post("/", response_model=schemas.TripResponse, status_code=status.HTTP_201_CREATED)
def create_trip(
    trip: schemas.TripCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    new_trip = models.Trip(
        **trip.dict(),
        user_id=current_user.id,
        organization_id=current_user.current_organization_id,
        workspace_id=current_user.current_workspace_id,
    )
    db.add(new_trip)
    db.commit()
    db.refresh(new_trip)
    logger.info("Trip %s created by user %s", new_trip.id, current_user.username)
    return new_trip


@router.get("/", response_model=List[schemas.TripResponse])
def list_trips(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    return db.query(models.Trip).filter(models.Trip.user_id == current_user.id).all()


@router.get("/{id}", response_model=schemas.TripResponse)
def get_trip(
    id: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    return _get_trip_or_404(id, db, current_user)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip(
    id: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    trip = _get_trip_or_404(id, db, current_user)
    db.delete(trip)
    db.commit()


@router.post("/{id}/expenses", response_model=schemas.ExpenseResponse, status_code=status.HTTP_201_CREATED)
def add_expense(
    id: str,
    expense: schemas.ExpenseCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    trip = _get_trip_or_404(id, db, current_user)
    new_expense = models.Expense(
        **expense.dict(),
        trip_id=id,
        user_id=current_user.id,
        organization_id=trip.organization_id,
        workspace_id=trip.workspace_id,
    )
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return new_expense


@router.get("/{id}/settlements", response_model=schemas.SettlementResponse)
def get_trip_settlements(
    id: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    trip = _get_trip_or_404(id, db, current_user)
    expenses = db.query(models.Expense).filter(models.Expense.trip_id == id).all()

    total_spent = sum(e.amount for e in expenses)
    per_person = total_spent / trip.num_people if trip.num_people > 0 else 0

    spent_by_person: dict[str, float] = {}
    for e in expenses:
        spent_by_person[e.paid_by_name] = spent_by_person.get(e.paid_by_name, 0) + e.amount

    balances = {name: amount - per_person for name, amount in spent_by_person.items()}

    debtors = [{"name": n, "amount": -b} for n, b in balances.items() if b < 0]
    creditors = [{"name": n, "amount": b} for n, b in balances.items() if b > 0]
    debtors.sort(key=lambda x: x["amount"], reverse=True)
    creditors.sort(key=lambda x: x["amount"], reverse=True)

    actions: list[schemas.SettlementAction] = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        amount = min(debtors[i]["amount"], creditors[j]["amount"])
        actions.append(schemas.SettlementAction(
            from_user=debtors[i]["name"],
            to_user=creditors[j]["name"],
            amount=round(amount, 2),
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
        actions=actions,
    )
